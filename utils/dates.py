"""Utility per date di versamento e date di mercato."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd


def ensure_timestamp(value: date | datetime | str | pd.Timestamp) -> pd.Timestamp:
    """Converte input data in pandas.Timestamp senza componente oraria."""
    return pd.Timestamp(value).normalize()


def generate_contribution_dates(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    frequency: str,
    day_of_month: int | None = None,
) -> list[pd.Timestamp]:
    """Genera le date teoriche dei versamenti PAC.

    Args:
        start_date: data di inizio simulazione.
        end_date: data di fine simulazione.
        frequency: "Mensile" o "Trimestrale".
        day_of_month: giorno del mese desiderato. Se None, usa il giorno di start_date.

    Returns:
        Lista di date teoriche, da convertire poi in prime date di mercato disponibili.
    """
    start_date = ensure_timestamp(start_date)
    end_date = ensure_timestamp(end_date)
    if start_date > end_date:
        raise ValueError("La data di inizio deve essere precedente alla data di fine.")

    freq = "MS" if frequency == "Mensile" else "QS"
    first_month_start = pd.Timestamp(year=start_date.year, month=start_date.month, day=1)
    month_starts = pd.date_range(first_month_start, end_date, freq=freq)
    requested_day = int(day_of_month or start_date.day)
    requested_day = min(max(requested_day, 1), 31)

    dates: list[pd.Timestamp] = []
    for month_start in month_starts:
        days_in_month = month_start.days_in_month
        selected_day = min(requested_day, days_in_month)
        candidate = pd.Timestamp(year=month_start.year, month=month_start.month, day=selected_day)
        if start_date <= candidate <= end_date:
            dates.append(candidate.normalize())

    if not dates and start_date <= end_date:
        dates.append(start_date)
    return dates


def first_available_market_date(
    requested_date: pd.Timestamp,
    market_dates: pd.DatetimeIndex,
    allow_next_available: bool = True,
) -> pd.Timestamp | None:
    """Restituisce la prima seduta disponibile uguale o successiva alla data richiesta.

    Se allow_next_available è False, la funzione restituisce None quando la data richiesta
    non è una seduta presente nel dataset.
    """
    requested_date = ensure_timestamp(requested_date)
    normalized_dates = pd.DatetimeIndex(market_dates).normalize()
    if requested_date in normalized_dates:
        return requested_date
    if not allow_next_available:
        return None
    pos = normalized_dates.searchsorted(requested_date, side="left")
    if pos >= len(normalized_dates):
        return None
    return pd.Timestamp(normalized_dates[pos]).normalize()


def years_between(start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    """Calcola la durata in anni civili medi."""
    start_date = ensure_timestamp(start_date)
    end_date = ensure_timestamp(end_date)
    return max((end_date - start_date).days / 365.25, 0.0)
