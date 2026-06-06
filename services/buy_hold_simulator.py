"""Motore di simulazione Buy and Hold multi-asset."""

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
from utils.dates import first_available_market_date
from utils.helpers import safe_divide


@dataclass(frozen=True)
class BuyHoldResult:
    """Risultato completo della simulazione Buy and Hold."""

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


def simulate_buy_and_hold(
    prices: pd.DataFrame,
    weights: dict[str, float],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    initial_capital: float,
    buy_next_market_day: bool,
    costs: CostConfig,
    tax_rate: float,
    risk_free_rate: float,
    cumulative_inflation: float,
) -> BuyHoldResult:
    """Simula un investimento unico Buy and Hold su un portafoglio multi-asset."""
    if initial_capital <= 0:
        raise ValueError("Il capitale iniziale del Buy and Hold deve essere positivo.")

    start_date = pd.Timestamp(start_date).normalize()
    end_date = pd.Timestamp(end_date).normalize()
    simulation_prices = prices.loc[(prices.index >= start_date) & (prices.index <= end_date)].copy()
    if simulation_prices.empty:
        raise ValueError("Nessun prezzo disponibile nel periodo selezionato.")

    trade_date = first_available_market_date(start_date, simulation_prices.index, allow_next_available=buy_next_market_day)
    if trade_date is None:
        raise ValueError("Nessuna seduta disponibile per l'acquisto Buy and Hold.")

    price_row = simulation_prices.loc[trade_date]
    explicit_cost = min(costs.explicit_cost_for(initial_capital), initial_capital)
    net_invested = max(initial_capital - explicit_cost, 0.0)
    shares = {
        ticker: (net_invested * weight) / float(price_row[ticker]) if float(price_row[ticker]) > 0 else 0.0
        for ticker, weight in weights.items()
    }

    value_without_ter = _build_buy_hold_value_series(simulation_prices, shares, trade_date, annual_ter=0.0)
    value_series = _build_buy_hold_value_series(simulation_prices, shares, trade_date, annual_ter=costs.annual_ter)
    value_series = value_series[value_series.index >= trade_date]
    value_without_ter = value_without_ter.reindex(value_series.index).fillna(0.0)

    cash_flow_series = pd.Series(0.0, index=value_series.index, name="Investimento Buy and Hold")
    cash_flow_series.loc[trade_date] = initial_capital

    final_gross_value = float(value_series.iloc[-1])
    final_without_ter = float(value_without_ter.iloc[-1])
    ter_costs = max(final_without_ter - final_gross_value, 0.0)
    total_costs = explicit_cost + ter_costs

    taxable_gain, taxes = capital_gain_tax(final_gross_value, tax_basis=net_invested, tax_rate=tax_rate)
    final_net_value = final_gross_value - taxes
    gross_profit = final_gross_value - initial_capital
    net_profit = final_net_value - initial_capital

    irr_value = periodic_irr([-initial_capital, final_net_value], periods_per_year=1)
    xirr_value = xirr([(trade_date, -initial_capital), (value_series.index[-1], final_net_value)])
    gross_ret = total_return(final_gross_value, initial_capital)
    net_ret = total_return(final_net_value, initial_capital)
    cagr_value = cagr(final_net_value, initial_capital, trade_date, value_series.index[-1])
    real_ret = real_return(net_ret, cumulative_inflation)

    risk = risk_metrics(value_series, risk_free_rate=risk_free_rate)
    annual_ret = annual_returns(value_series)
    drawdown = value_series / value_series.cummax() - 1.0
    efficiency = build_efficiency_metrics(net_profit, initial_capital, total_costs, taxes, gross_profit)
    performance = PerformanceMetrics(
        gross_total_return=gross_ret,
        net_total_return=net_ret,
        cagr=cagr_value,
        irr=irr_value,
        xirr=xirr_value,
        real_return=real_ret,
    )

    weighted_price = float(sum(weights[ticker] * float(price_row[ticker]) for ticker in weights))
    total_units = float(sum(shares.values()))
    history_row: dict[str, Any] = {
        "Data investimento": trade_date,
        "Prezzo acquisto ponderato": weighted_price,
        "Capitale iniziale": initial_capital,
        "Costi": explicit_cost,
        "Capitale investito netto": net_invested,
        "Quote acquistate totali": total_units,
        "Valore posizione iniziale": net_invested,
    }
    for ticker in simulation_prices.columns:
        history_row[f"Prezzo {ticker}"] = float(price_row[ticker])
        history_row[f"Quote {ticker}"] = shares.get(ticker, 0.0)

    value_series_net = value_series.copy().rename("Buy and Hold netto")
    value_series_net.iloc[-1] = final_net_value

    summary = {
        "Capitale investito": initial_capital,
        "Capitale netto investito": net_invested,
        "Costi espliciti": explicit_cost,
        "Costi TER stimati": ter_costs,
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
        "Numero totale quote acquistate": total_units,
        "Prezzo medio di carico aggregato": safe_divide(net_invested, total_units, 0.0),
    }

    return BuyHoldResult(
        summary=summary,
        history=pd.DataFrame([history_row]),
        value_series=value_series.rename("Buy & Hold"),
        value_series_net=value_series_net,
        cash_flow_series=cash_flow_series,
        drawdown_series=drawdown.rename("Drawdown Buy & Hold"),
        annual_returns=annual_ret.rename("Buy & Hold"),
        risk=risk,
        performance=performance,
        efficiency=efficiency,
        holdings={ticker: float(value) for ticker, value in shares.items()},
    )


def _build_buy_hold_value_series(
    prices: pd.DataFrame,
    shares: dict[str, float],
    trade_date: pd.Timestamp,
    annual_ter: float,
) -> pd.Series:
    """Costruisce la serie valore Buy and Hold con drag TER giornaliero."""
    annual_ter = min(max(float(annual_ter), 0.0), 0.9999)
    effective_prices = prices.loc[prices.index >= trade_date]
    shares_series = pd.Series(shares).reindex(prices.columns).fillna(0.0)
    raw_value = effective_prices.mul(shares_series, axis=1).sum(axis=1)
    if annual_ter > 0:
        days = (raw_value.index - trade_date).days.astype(float)
        ter_factor = np.power(1.0 - annual_ter, days / 365.25)
        raw_value = raw_value * ter_factor
    return raw_value.rename("Valore Buy and Hold")


def result_to_frames(result: BuyHoldResult) -> dict[str, pd.DataFrame]:
    """Converte il risultato Buy and Hold in DataFrame esportabili."""
    return {
        "summary": pd.DataFrame([result.summary]),
        "history": result.history.copy(),
        "risk": pd.DataFrame([asdict(result.risk)]),
        "performance": pd.DataFrame([asdict(result.performance)]),
        "efficiency": pd.DataFrame([asdict(result.efficiency)]),
    }
