"""Funzioni di supporto per validazione, formattazione e parsing input."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd


def parse_tickers(raw: str) -> list[str]:
    """Converte una stringa CSV di ticker in una lista normalizzata e senza duplicati."""
    if not raw or not raw.strip():
        raise ValueError("Inserisci almeno un ticker Yahoo Finance.")
    tickers: list[str] = []
    for item in raw.replace(";", ",").split(","):
        ticker = item.strip().upper()
        if ticker and ticker not in tickers:
            tickers.append(ticker)
    if not tickers:
        raise ValueError("Nessun ticker valido trovato.")
    return tickers


def parse_weights(raw: str, tickers: Iterable[str]) -> dict[str, float]:
    """Converte i pesi inseriti dall'utente in pesi normalizzati con somma pari a 1.

    Se l'utente non inserisce pesi, viene creato un portafoglio equiponderato.
    I pesi possono essere inseriti come percentuali (80,20) o come decimali (0.8,0.2).
    """
    tickers_list = list(tickers)
    if not tickers_list:
        raise ValueError("Lista ticker vuota.")

    if not raw or not raw.strip():
        equal_weight = 1.0 / len(tickers_list)
        return {ticker: equal_weight for ticker in tickers_list}

    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    if len(parts) != len(tickers_list):
        raise ValueError("Il numero dei pesi deve coincidere con il numero dei ticker.")

    values = [float(p.replace("%", "").replace(",", ".")) for p in parts]
    weights = np.array(values, dtype=float)
    if np.any(weights < 0):
        raise ValueError("I pesi non possono essere negativi.")
    if np.allclose(weights.sum(), 0.0):
        raise ValueError("La somma dei pesi deve essere maggiore di zero.")

    # Supporta sia input in percentuale sia input già decimale.
    if weights.sum() > 1.5:
        weights = weights / 100.0
    weights = weights / weights.sum()
    return {ticker: float(weight) for ticker, weight in zip(tickers_list, weights)}


def format_currency(value: float, currency_symbol: str = "€") -> str:
    """Formatta un numero come valuta in stile europeo."""
    if value is None or not np.isfinite(value):
        return "n.d."
    return f"{currency_symbol} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(value: float) -> str:
    """Formatta una percentuale espressa in forma decimale."""
    if value is None or not np.isfinite(value):
        return "n.d."
    return f"{value * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divisione robusta contro zero, NaN e infiniti."""
    if denominator is None or np.isclose(denominator, 0.0) or not np.isfinite(denominator):
        return default
    result = numerator / denominator
    return float(result) if np.isfinite(result) else default


def to_serializable_dict(obj: Any) -> dict[str, Any]:
    """Converte dataclass o mapping in dizionario serializzabile."""
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return dict(obj)
    raise TypeError(f"Oggetto non convertibile in dict: {type(obj)!r}")


def clean_numeric_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Restituisce una copia con infiniti convertiti in NaN per export e visualizzazione."""
    return df.replace([np.inf, -np.inf], np.nan)
