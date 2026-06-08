"""Motore di simulazione PAC multi-asset."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from config import CostConfig
from services.metrics import (
    EfficiencyMetrics,
    PerformanceMetrics,
    RiskMetrics,
    annual_returns,
    build_efficiency_metrics,
    cagr,
    periodic_irr,
    real_return,
    risk_metrics,
    total_return,
    xirr,
)
from services.taxes import capital_gain_tax
from utils.dates import first_available_market_date, generate_contribution_dates
from utils.helpers import safe_divide


@dataclass(frozen=True)
class PACResult:
    """Risultato completo della simulazione PAC."""

    summary: dict[str, float]
    history: pd.DataFrame
    value_series: pd.Series
    value_series_net: pd.Series
    cash_flow_series: pd.Series
    drawdown_series: pd.Series
    annual_returns: pd.Series
    risk: RiskMetrics
    performance: PerformanceMetrics
    efficiency: EfficiencyMetrics
    holdings: dict[str, float]


@dataclass(frozen=True)
class Lot:
    """Singolo lotto acquistato dal PAC."""

    trade_date: pd.Timestamp
    gross_amount: float
    explicit_cost: float
    net_invested: float
    shares: dict[str, float]


def simulate_pac(
    prices: pd.DataFrame,
    weights: dict[str, float],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    contribution_amount: float,
    frequency: str,
    day_of_month: int | None,
    buy_next_market_day: bool,
    costs: CostConfig,
    tax_rate: float,
    risk_free_rate: float,
    cumulative_inflation: float,
) -> PACResult:
    """Simula un Piano di Accumulo del Capitale su un portafoglio multi-asset.

    Per ogni versamento:
    1. viene individuata la prima seduta di mercato disponibile;
    2. vengono sottratti i costi espliciti;
    3. il capitale netto viene allocato sugli asset secondo i pesi;
    4. vengono acquistate quote frazionarie;
    5. l’eventuale costo annuo aggiuntivo viene applicato come drag giornaliero sul valore del lotto.
    """
    if contribution_amount <= 0:
        raise ValueError("L'importo periodico del PAC deve essere positivo.")
    if prices.empty:
        raise ValueError("Serie prezzi vuota.")

    start_date = pd.Timestamp(start_date).normalize()
    end_date = pd.Timestamp(end_date).normalize()
    simulation_prices = prices.loc[(prices.index >= start_date) & (prices.index <= end_date)].copy()
    if simulation_prices.empty:
        raise ValueError("Nessun prezzo disponibile nel periodo selezionato.")

    theoretical_dates = generate_contribution_dates(start_date, end_date, frequency, day_of_month)
    lots: list[Lot] = []
    rows: list[dict[str, Any]] = []
    cumulative_shares = {ticker: 0.0 for ticker in simulation_prices.columns}
    cash_flow_series = pd.Series(0.0, index=simulation_prices.index, name="Versamenti PAC")

    for requested_date in theoretical_dates:
        trade_date = first_available_market_date(
            requested_date,
            simulation_prices.index,
            allow_next_available=buy_next_market_day,
        )
        if trade_date is None or trade_date > end_date:
            continue

        price_row = simulation_prices.loc[trade_date]
        explicit_cost = min(costs.explicit_cost_for(contribution_amount), contribution_amount)
        net_invested = max(contribution_amount - explicit_cost, 0.0)
        purchased_shares: dict[str, float] = {}

        for ticker, weight in weights.items():
            allocated_capital = net_invested * weight
            price = float(price_row[ticker])
            shares = allocated_capital / price if price > 0 else 0.0
            purchased_shares[ticker] = shares
            cumulative_shares[ticker] += shares

        lots.append(
            Lot(
                trade_date=trade_date,
                gross_amount=contribution_amount,
                explicit_cost=explicit_cost,
                net_invested=net_invested,
                shares=purchased_shares,
            )
        )
        cash_flow_series.loc[trade_date] += contribution_amount

        weighted_price = float(sum(weights[ticker] * float(price_row[ticker]) for ticker in weights))
        current_position_value = float(
            sum(cumulative_shares[ticker] * float(price_row[ticker]) for ticker in cumulative_shares)
        )
        row: dict[str, Any] = {
            "Data richiesta": requested_date,
            "Data versamento": trade_date,
            "Prezzo acquisto ponderato": weighted_price,
            "Importo versato": contribution_amount,
            "Costi": explicit_cost,
            "Capitale investito netto": net_invested,
            "Quote acquistate totali": float(sum(purchased_shares.values())),
            "Quote cumulative totali": float(sum(cumulative_shares.values())),
            "Valore posizione": current_position_value,
        }
        for ticker in simulation_prices.columns:
            row[f"Prezzo {ticker}"] = float(price_row[ticker])
            row[f"Quote acquistate {ticker}"] = purchased_shares.get(ticker, 0.0)
            row[f"Quote cumulative {ticker}"] = cumulative_shares.get(ticker, 0.0)
        rows.append(row)

    if not lots:
        raise ValueError("Nessun versamento PAC eseguito. Controlla date, frequenza e dati di mercato.")

    history = pd.DataFrame(rows)
    value_without_ter = _build_value_series(simulation_prices, lots, annual_ter=0.0)
    value_series = _build_value_series(simulation_prices, lots, annual_ter=costs.annual_ter)
    value_series = value_series[value_series.index >= lots[0].trade_date]
    value_without_ter = value_without_ter.reindex(value_series.index).fillna(0.0)
    cash_flow_series = cash_flow_series.reindex(value_series.index).fillna(0.0)

    final_gross_value = float(value_series.iloc[-1])
    final_without_ter = float(value_without_ter.iloc[-1])
    total_contributed = float(sum(lot.gross_amount for lot in lots))
    explicit_costs = float(sum(lot.explicit_cost for lot in lots))
    net_invested = float(sum(lot.net_invested for lot in lots))
    ter_costs = max(final_without_ter - final_gross_value, 0.0)
    total_costs = explicit_costs + ter_costs

    taxable_gain, taxes = capital_gain_tax(final_gross_value, tax_basis=net_invested, tax_rate=tax_rate)
    final_net_value = final_gross_value - taxes
    gross_profit = final_gross_value - total_contributed
    net_profit = final_net_value - total_contributed

    periods_per_year = 12 if frequency == "Mensile" else 4
    irr_flows = [-lot.gross_amount for lot in lots] + [final_net_value]
    xirr_flows = [(lot.trade_date, -lot.gross_amount) for lot in lots] + [(value_series.index[-1], final_net_value)]
    irr_value = periodic_irr(irr_flows, periods_per_year=periods_per_year)
    xirr_value = xirr(xirr_flows)

    gross_ret = total_return(final_gross_value, total_contributed)
    net_ret = total_return(final_net_value, total_contributed)
    cagr_value = cagr(final_net_value, total_contributed, value_series.index[0], value_series.index[-1])
    real_ret = real_return(net_ret, cumulative_inflation)

    risk = risk_metrics(value_series, risk_free_rate=risk_free_rate, cash_flows=cash_flow_series)
    annual_ret = annual_returns(value_series, cash_flow_series)
    drawdown = value_series / value_series.cummax() - 1.0
    efficiency = build_efficiency_metrics(net_profit, total_contributed, total_costs, taxes, gross_profit)
    performance = PerformanceMetrics(
        gross_total_return=gross_ret,
        net_total_return=net_ret,
        cagr=cagr_value,
        irr=irr_value,
        xirr=xirr_value,
        real_return=real_ret,
    )

    value_series_net = value_series.copy().rename("PAC netto")
    value_series_net.iloc[-1] = final_net_value

    total_units = float(sum(cumulative_shares.values()))
    summary = {
        "Capitale investito": total_contributed,
        "Capitale netto investito": net_invested,
        "Costi espliciti": explicit_costs,
        "Costi annui aggiuntivi stimati": ter_costs,
        "Costi": total_costs,
        "Valore finale lordo": final_gross_value,
        "Plusvalenza tassabile": taxable_gain,
        "Tasse": taxes,
        "Valore finale netto": final_net_value,
        "Profitto lordo": gross_profit,
        "Profitto netto": net_profit,
        "Rendimento totale lordo": gross_ret,
        "Rendimento totale netto": net_ret,
        "CAGR": cagr_value,
        "IRR": irr_value if irr_value is not None else np.nan,
        "XIRR": xirr_value if xirr_value is not None else np.nan,
        "Rendimento reale": real_ret,
        "Volatilità annualizzata": risk.annualized_volatility,
        "Maximum Drawdown": risk.max_drawdown,
        "Drawdown corrente": risk.current_drawdown,
        "Sharpe Ratio": risk.sharpe_ratio,
        "Profitto netto per euro investito": efficiency.net_profit_per_euro_invested,
        "Rapporto costi/capitale investito": efficiency.costs_to_capital_ratio,
        "Rapporto tasse/profitto lordo": efficiency.taxes_to_gross_profit_ratio,
        "Numero versamenti": float(len(lots)),
        "Numero totale quote acquistate": total_units,
        "Prezzo medio di carico aggregato": safe_divide(net_invested, total_units, 0.0),
    }

    return PACResult(
        summary=summary,
        history=history,
        value_series=value_series.rename("PAC"),
        value_series_net=value_series_net,
        cash_flow_series=cash_flow_series,
        drawdown_series=drawdown.rename("Drawdown PAC"),
        annual_returns=annual_ret.rename("PAC"),
        risk=risk,
        performance=performance,
        efficiency=efficiency,
        holdings={ticker: float(value) for ticker, value in cumulative_shares.items()},
    )


def _build_value_series(prices: pd.DataFrame, lots: list[Lot], annual_ter: float) -> pd.Series:
    """Costruisce la serie storica del valore posizione.

    `annual_ter` è un nome interno legacy: nella UI rappresenta un
    costo annuo aggiuntivo opzionale.

    Se maggiore di 0, viene approssimato come riduzione composta giornaliera:

        valore_lotto_t = valore_lordo_lotto_t * (1 - costo_annuo_aggiuntivo)^(giorni_dal_acquisto / 365,25)

    Per ETF reali scaricati da Yahoo Finance il valore consigliato è normalmente 0%,
    perché i costi interni del fondo sono già riflessi nella performance/NAV storica.
    """
    annual_ter = min(max(float(annual_ter), 0.0), 0.9999)
    values = pd.Series(0.0, index=prices.index, dtype=float)
    for lot in lots:
        mask = prices.index >= lot.trade_date
        if not mask.any():
            continue
        lot_prices = prices.loc[mask]
        shares = pd.Series(lot.shares).reindex(prices.columns).fillna(0.0)
        raw_value = lot_prices.mul(shares, axis=1).sum(axis=1)
        if annual_ter > 0:
            days = (raw_value.index - lot.trade_date).days.astype(float)
            ter_factor = np.power(1.0 - annual_ter, days / 365.25)
            raw_value = raw_value * ter_factor
        values.loc[raw_value.index] += raw_value
    return values.rename("Valore PAC")


def result_to_frames(result: PACResult) -> dict[str, pd.DataFrame]:
    """Converte il risultato PAC in DataFrame esportabili."""
    return {
        "summary": pd.DataFrame([result.summary]),
        "history": result.history.copy(),
        "risk": pd.DataFrame([asdict(result.risk)]),
        "performance": pd.DataFrame([asdict(result.performance)]),
        "efficiency": pd.DataFrame([asdict(result.efficiency)]),
    }
