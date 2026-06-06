"""Simulazione del capitale non investito soggetto a inflazione."""

from __future__ import annotations

from dataclasses import dataclass
from typing import IO

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class InflationResult:
    """Risultato della simulazione inflazionistica."""

    summary: dict[str, float]
    series: pd.DataFrame
    cumulative_inflation: float


def simulate_manual_inflation(
    dates: pd.DatetimeIndex,
    nominal_capital: float,
    annual_inflation_rate: float,
) -> InflationResult:
    """Simula l'erosione del capitale usando un tasso medio annuo costante.

    Formula:
        Valore reale_t = Capitale nominale / (1 + inflazione_annua)^anni_trascorsi
    """
    if nominal_capital < 0:
        raise ValueError("Il capitale nominale non può essere negativo.")
    if len(dates) == 0:
        raise ValueError("Date vuote per la simulazione inflazione.")

    dates = pd.DatetimeIndex(dates).normalize()
    start = dates[0]
    years = np.array([(d - start).days / 365.25 for d in dates], dtype=float)
    factor = np.power(1.0 + annual_inflation_rate, years)
    factor = np.maximum(factor, 1e-12)
    real_capital = nominal_capital / factor
    series = pd.DataFrame(
        {
            "Capitale nominale": nominal_capital,
            "Fattore inflazione": factor,
            "Inflazione cumulata": factor - 1.0,
            "Capitale reale": real_capital,
            "Perdita potere acquisto": nominal_capital - real_capital,
        },
        index=dates,
    )
    return _build_result(series, nominal_capital)


def simulate_csv_inflation(
    dates: pd.DatetimeIndex,
    nominal_capital: float,
    csv_file: IO[bytes] | IO[str] | pd.DataFrame,
) -> InflationResult:
    """Simula l'inflazione usando un CSV storico fornito dall'utente.

    Il CSV deve contenere una colonna data e una colonna con il tasso di inflazione
    annualizzato. I nomi riconosciuti sono flessibili, ad esempio:
    Date, Data, inflation, inflation_rate, rate, inflazione.

    I tassi possono essere espressi come 3.2 oppure 0.032; valori con modulo > 1
    vengono interpretati come percentuali.
    """
    if isinstance(csv_file, pd.DataFrame):
        raw = csv_file.copy()
    else:
        raw = pd.read_csv(csv_file)
    if raw.empty:
        raise ValueError("Il file CSV inflazione è vuoto.")

    date_col = _find_column(raw, ["date", "data", "period", "periodo", "time"])
    rate_col = _find_column(
        raw,
        ["inflation", "inflation_rate", "inflazione", "tasso", "rate", "value", "valore"],
        exclude={date_col},
    )
    if date_col is None or rate_col is None:
        raise ValueError("Il CSV deve contenere una colonna data e una colonna tasso inflazione.")

    inflation = raw[[date_col, rate_col]].dropna().copy()
    inflation[date_col] = pd.to_datetime(inflation[date_col], errors="coerce")
    inflation[rate_col] = pd.to_numeric(inflation[rate_col], errors="coerce")
    inflation = inflation.dropna().sort_values(date_col)
    if inflation.empty:
        raise ValueError("Il CSV non contiene righe inflazione valide.")

    inflation = inflation.set_index(date_col)
    inflation.index = pd.DatetimeIndex(inflation.index).tz_localize(None).normalize()
    annual_rates = inflation[rate_col].astype(float)
    annual_rates = annual_rates / 100.0 if annual_rates.abs().median() > 1 else annual_rates

    dates = pd.DatetimeIndex(dates).normalize()
    daily_rates = annual_rates.reindex(dates, method="ffill")
    if daily_rates.isna().all():
        daily_rates = annual_rates.reindex(dates, method="bfill")
    daily_rates = daily_rates.ffill().bfill().fillna(0.0)

    # Trasforma tassi annui in tassi giornalieri composti e costruisce il fattore cumulato.
    daily_inflation = np.power(1.0 + daily_rates.clip(lower=-0.99), 1.0 / 365.25) - 1.0
    factor = (1.0 + daily_inflation).cumprod()
    # Il primo giorno rappresenta il punto iniziale della simulazione: fattore = 1.
    if len(factor) > 0:
        factor.iloc[0] = 1.0
        factor = factor / factor.iloc[0]

    real_capital = nominal_capital / factor.replace(0.0, np.nan)
    real_capital = real_capital.ffill().fillna(nominal_capital)
    series = pd.DataFrame(
        {
            "Capitale nominale": nominal_capital,
            "Fattore inflazione": factor,
            "Inflazione cumulata": factor - 1.0,
            "Capitale reale": real_capital,
            "Perdita potere acquisto": nominal_capital - real_capital,
            "Tasso inflazione annuo usato": daily_rates,
        },
        index=dates,
    )
    return _build_result(series, nominal_capital)


def _build_result(series: pd.DataFrame, nominal_capital: float) -> InflationResult:
    """Crea summary e risultato finale da una serie inflazione."""
    final_real = float(series["Capitale reale"].iloc[-1])
    loss = float(nominal_capital - final_real)
    erosion = loss / nominal_capital if nominal_capital > 0 else 0.0
    cumulative_inflation = float(series["Inflazione cumulata"].iloc[-1])
    summary = {
        "Capitale nominale": float(nominal_capital),
        "Capitale reale": final_real,
        "Perdita potere acquisto": loss,
        "Percentuale erosione": erosion,
        "Inflazione cumulata": cumulative_inflation,
        "Valore finale netto": final_real,
        "Profitto netto": final_real - nominal_capital,
        "CAGR": (final_real / nominal_capital) ** (1.0 / max((series.index[-1] - series.index[0]).days / 365.25, 1e-9)) - 1.0
        if nominal_capital > 0 and len(series) > 1
        else 0.0,
        "Rendimento reale": -erosion,
        "Costi": 0.0,
        "Valore finale lordo": final_real,
        "Tasse": 0.0,
        "Maximum Drawdown": 0.0,
        "Sharpe Ratio": 0.0,
    }
    return InflationResult(summary=summary, series=series, cumulative_inflation=cumulative_inflation)


def _find_column(df: pd.DataFrame, candidates: list[str], exclude: set[str | None] | None = None) -> str | None:
    """Trova una colonna con nome compatibile con i candidati forniti."""
    exclude = exclude or set()
    normalized = {str(col).strip().lower(): col for col in df.columns if col not in exclude}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    for normalized_name, original in normalized.items():
        if any(candidate in normalized_name for candidate in candidates):
            return original
    return None
