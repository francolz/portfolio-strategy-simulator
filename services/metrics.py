"""Metriche finanziarie, di rischio ed efficienza."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import numpy_financial as npf
import pandas as pd
from scipy.optimize import brentq

from config import DAYS_PER_YEAR, TRADING_DAYS_PER_YEAR
from utils.dates import years_between
from utils.helpers import safe_divide


@dataclass(frozen=True)
class RiskMetrics:
    """Metriche di rischio calcolate da una serie temporale di valore."""

    annualized_volatility: float
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float


@dataclass(frozen=True)
class PerformanceMetrics:
    """Metriche economiche e finanziarie aggregate di una strategia."""

    gross_total_return: float
    net_total_return: float
    cagr: float
    irr: float | None
    xirr: float | None
    real_return: float


@dataclass(frozen=True)
class EfficiencyMetrics:
    """Metriche di efficienza economica."""

    net_profit_per_euro_invested: float
    costs_to_capital_ratio: float
    taxes_to_gross_profit_ratio: float


def total_return(final_value: float, invested_capital: float) -> float:
    """Rendimento totale rispetto al capitale nominale versato."""
    return safe_divide(final_value - invested_capital, invested_capital, default=0.0)


def cagr(final_value: float, initial_or_total_capital: float, start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    """Calcola il CAGR economico sul periodo selezionato.

    Formula:
        CAGR = (Valore finale / Capitale di riferimento)^(1 / anni) - 1

    Per il PAC il capitale di riferimento è il totale versato. Questa scelta rende
    il confronto leggibile nella dashboard, ma non sostituisce l'XIRR, che è la
    misura più corretta quando i flussi sono distribuiti nel tempo.
    """
    years = years_between(start_date, end_date)
    if years <= 0 or initial_or_total_capital <= 0 or final_value <= 0:
        return 0.0
    return float((final_value / initial_or_total_capital) ** (1.0 / years) - 1.0)


def calculate_drawdown(value_series: pd.Series) -> pd.Series:
    """Calcola la serie dei drawdown rispetto ai massimi storici.

    Formula:
        drawdown_t = Valore_t / max(Valore_0...Valore_t) - 1
    """
    series = value_series.dropna().astype(float)
    if series.empty:
        return pd.Series(dtype=float)
    running_max = series.cummax()
    return series / running_max - 1.0


def cash_flow_adjusted_returns(value_series: pd.Series, cash_flows: pd.Series | None = None) -> pd.Series:
    """Calcola rendimenti giornalieri depurando i nuovi versamenti.

    Per una strategia con versamenti intermedi, un aumento del valore dovuto a un
    nuovo versamento non deve essere interpretato come performance di mercato.
    La formula usata è:

        r_t = (Valore_t - Flusso_t) / Valore_{t-1} - 1

    dove Flusso_t è positivo quando entra nuovo capitale nella strategia.
    """
    values = value_series.dropna().astype(float)
    if values.empty:
        return pd.Series(dtype=float)
    flows = pd.Series(0.0, index=values.index)
    if cash_flows is not None and not cash_flows.empty:
        aligned_flows = cash_flows.reindex(values.index).fillna(0.0).astype(float)
        flows = aligned_flows
    previous_values = values.shift(1)
    returns = (values - flows) / previous_values - 1.0
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
    return returns


def risk_metrics(
    value_series: pd.Series,
    risk_free_rate: float = 0.0,
    cash_flows: pd.Series | None = None,
) -> RiskMetrics:
    """Calcola volatilità annualizzata, drawdown e Sharpe Ratio.

    Volatilità annualizzata:
        std(rendimenti_giornalieri) * sqrt(252)

    Sharpe Ratio:
        (rendimento_medio_giornaliero - risk_free_giornaliero) /
        volatilità_giornaliera * sqrt(252)
    """
    values = value_series.dropna().astype(float)
    if len(values) < 2:
        return RiskMetrics(0.0, 0.0, 0.0, 0.0)

    returns = cash_flow_adjusted_returns(values, cash_flows)
    if returns.empty:
        volatility = 0.0
        sharpe = 0.0
    else:
        daily_volatility = float(returns.std(ddof=1))
        volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0
        if daily_volatility > 0:
            sharpe = float(((returns.mean() - daily_rf) / daily_volatility) * np.sqrt(TRADING_DAYS_PER_YEAR))
        else:
            sharpe = 0.0

    drawdown = calculate_drawdown(values)
    max_dd = float(drawdown.min()) if not drawdown.empty else 0.0
    current_dd = float(drawdown.iloc[-1]) if not drawdown.empty else 0.0
    return RiskMetrics(volatility, max_dd, current_dd, sharpe)


def periodic_irr(cash_flows: Iterable[float], periods_per_year: int) -> float | None:
    """Calcola l'IRR periodico annualizzato.

    npf.irr restituisce il rendimento per periodo. Per renderlo confrontabile su
    base annua viene applicata la formula:

        IRR_annuo = (1 + IRR_periodico)^periodi_per_anno - 1
    """
    flows = list(float(x) for x in cash_flows)
    if len(flows) < 2 or not any(x < 0 for x in flows) or not any(x > 0 for x in flows):
        return None
    try:
        period_rate = npf.irr(flows)
        if period_rate is None or not np.isfinite(period_rate):
            return None
        return float((1.0 + period_rate) ** periods_per_year - 1.0)
    except Exception:
        return None


def xirr(cash_flows: list[tuple[pd.Timestamp, float]]) -> float | None:
    """Calcola l'XIRR, cioè il tasso interno di rendimento con date reali.

    L'XIRR è il tasso r che azzera il valore attuale netto dei flussi:

        NPV = Σ CF_i / (1 + r)^((data_i - data_0) / 365,25) = 0

    È più adatto dell'IRR tradizionale quando i flussi non sono perfettamente
    equidistanti, come nei PAC con date spostate al primo giorno di mercato.
    """
    if len(cash_flows) < 2:
        return None
    ordered = sorted((pd.Timestamp(d).normalize(), float(v)) for d, v in cash_flows)
    values = [v for _, v in ordered]
    if not any(v < 0 for v in values) or not any(v > 0 for v in values):
        return None
    start = ordered[0][0]

    def npv(rate: float) -> float:
        total = 0.0
        for dt, amount in ordered:
            exponent = (dt - start).days / DAYS_PER_YEAR
            total += amount / ((1.0 + rate) ** exponent)
        return total

    # Cerca un intervallo con cambio di segno. Il limite inferiore evita rate <= -100%.
    intervals = [(-0.9999, 10.0), (-0.9999, 5.0), (-0.95, 3.0), (-0.8, 1.5), (-0.5, 0.8)]
    for low, high in intervals:
        try:
            if np.sign(npv(low)) != np.sign(npv(high)):
                return float(brentq(npv, low, high, maxiter=1000))
        except Exception:
            continue
    return None


def real_return(nominal_return: float, cumulative_inflation: float) -> float:
    """Calcola il rendimento reale al netto dell'inflazione.

    Formula di Fisher approssimata in forma esatta:
        rendimento_reale = (1 + rendimento_nominale) / (1 + inflazione) - 1
    """
    if cumulative_inflation <= -1:
        return nominal_return
    return (1.0 + nominal_return) / (1.0 + cumulative_inflation) - 1.0


def annual_returns(value_series: pd.Series, cash_flows: pd.Series | None = None) -> pd.Series:
    """Calcola i rendimenti per anno solare da una serie di valore."""
    returns = cash_flow_adjusted_returns(value_series, cash_flows)
    if returns.empty:
        return pd.Series(dtype=float)
    compounded = (1.0 + returns).resample("YE").prod() - 1.0
    compounded.index = compounded.index.year
    return compounded


def build_efficiency_metrics(
    net_profit: float,
    invested_capital: float,
    total_costs: float,
    taxes: float,
    gross_profit: float,
) -> EfficiencyMetrics:
    """Costruisce le metriche di efficienza economica."""
    return EfficiencyMetrics(
        net_profit_per_euro_invested=safe_divide(net_profit, invested_capital, 0.0),
        costs_to_capital_ratio=safe_divide(total_costs, invested_capital, 0.0),
        taxes_to_gross_profit_ratio=safe_divide(taxes, gross_profit, 0.0) if gross_profit > 0 else 0.0,
    )
