"""Download, validazione e normalizzazione dei dati di mercato da Yahoo Finance."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf


class MarketDataError(RuntimeError):
    """Errore applicativo relativo al download o alla qualità dei dati di mercato."""

@st.cache_data(show_spinner=False, ttl=60 * 60)
def download_adjusted_close(
    tickers: tuple[str, ...],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Scarica gli Adjusted Close da Yahoo Finance tramite yfinance.

    Gli Adjusted Close incorporano split e dividendi, rendendo i prezzi più adatti
    alle simulazioni di performance storica total-return.

    La funzione conserva anche, dentro prices.attrs["first_valid_dates"], la prima
    data disponibile per ogni ticker prima dell'allineamento alla prima data comune.
    Questo permette all'app di avvisare correttamente quali ticker stanno accorciando
    il periodo simulabile.

    Args:
        tickers: tuple di ticker Yahoo Finance.
        start_date: data iniziale ISO YYYY-MM-DD.
        end_date: data finale ISO YYYY-MM-DD.

    Returns:
        DataFrame indicizzato per data di negoziazione, con una colonna per ticker.

    Raises:
        MarketDataError: se il download fallisce, non produce dati o contiene ticker
        interamente non valorizzati.
    """
    if not tickers:
        raise MarketDataError("Nessun ticker specificato.")

    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()

    if start >= end:
        raise MarketDataError("La data di inizio deve essere precedente alla data di fine.")

    # yfinance usa end esclusivo; aggiungiamo un giorno per includere la data finale scelta.
    yf_end = (end + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        raw = yf.download(
            list(tickers),
            start=start.strftime("%Y-%m-%d"),
            end=yf_end,
            auto_adjust=False,
            actions=False,
            progress=False,
            group_by="column",
            threads=True,
        )
    except Exception as exc:  # pragma: no cover - dipende dalla rete
        raise MarketDataError(f"Errore durante il download da Yahoo Finance: {exc}") from exc

    if raw is None or raw.empty:
        raise MarketDataError(
            "Yahoo Finance non ha restituito dati per il periodo e i ticker selezionati."
        )

    prices = _extract_adjusted_close(raw, list(tickers))
    prices = prices.sort_index()
    prices.index = pd.DatetimeIndex(prices.index).tz_localize(None).normalize()
    prices = prices.loc[(prices.index >= start) & (prices.index <= end)]
    prices = prices.dropna(how="all")

    if prices.empty:
        raise MarketDataError("Nessuna seduta di mercato disponibile nel periodo selezionato.")

    invalid = [
        ticker
        for ticker in tickers
        if ticker not in prices.columns or prices[ticker].dropna().empty
    ]

    if invalid:
        raise MarketDataError(
            "Ticker non validi o senza dati nel periodo selezionato: "
            + ", ".join(invalid)
        )

    # Salviamo le prime date disponibili PRIMA dell'allineamento.
    # Dopo ffill().dropna(how="any") tutte le colonne partiranno dalla stessa data comune,
    # quindi perderemmo l'informazione su quale ticker ha storico più corto.
    first_valid_dates = {
        ticker: prices[ticker].first_valid_index()
        for ticker in tickers
        if ticker in prices.columns
    }

    aligned_prices = prices[list(tickers)].ffill().dropna(how="any")

    if aligned_prices.empty:
        raise MarketDataError(
            "I ticker selezionati non hanno date comuni sufficienti. "
            "Prova un periodo diverso o rimuovi asset illiquidi."
        )

    aligned_prices = aligned_prices.astype(float)

    # Metadata usato dall'app per mostrare warning più precisi.
    aligned_prices.attrs["first_valid_dates"] = first_valid_dates
    aligned_prices.attrs["requested_start_date"] = start
    aligned_prices.attrs["actual_start_date"] = aligned_prices.index.min()

    return aligned_prices


def _extract_adjusted_close(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Estrae la matrice Adjusted Close da output yfinance single o multi ticker."""
    if isinstance(raw.columns, pd.MultiIndex):
        if "Adj Close" in raw.columns.get_level_values(0):
            adj = raw["Adj Close"].copy()
        elif "Close" in raw.columns.get_level_values(0):
            # Fallback per strumenti senza Adj Close: meglio segnalare visivamente in app,
            # ma mantenere funzionale il simulatore per asset particolari.
            adj = raw["Close"].copy()
        else:
            raise MarketDataError("Il dataset non contiene colonne Adj Close o Close.")
        if isinstance(adj, pd.Series):
            adj = adj.to_frame(name=tickers[0])
        return adj.rename(columns={c: str(c).upper() for c in adj.columns})

    if "Adj Close" in raw.columns:
        series = raw["Adj Close"].copy()
    elif "Close" in raw.columns:
        series = raw["Close"].copy()
    else:
        raise MarketDataError("Il dataset non contiene Adj Close.")
    name = tickers[0] if len(tickers) == 1 else "ASSET"
    return series.to_frame(name=name.upper())


def normalize_weights(weights: dict[str, float], prices: pd.DataFrame) -> dict[str, float]:
    """Allinea i pesi ai ticker presenti nei prezzi e li normalizza."""
    missing = [ticker for ticker in weights if ticker not in prices.columns]
    if missing:
        raise MarketDataError("Mancano prezzi per: " + ", ".join(missing))
    total = sum(max(float(weights[ticker]), 0.0) for ticker in prices.columns)
    if total <= 0:
        raise MarketDataError("La somma dei pesi deve essere positiva.")
    return {ticker: max(float(weights[ticker]), 0.0) / total for ticker in prices.columns}


def weighted_portfolio_index(prices: pd.DataFrame, weights: dict[str, float], base: float = 100.0) -> pd.Series:
    """Costruisce un indice sintetico di portafoglio normalizzato a base 100.

    L'indice usa rendimenti giornalieri ponderati e serve per rappresentazioni e
    confronti di mercato indipendenti dai flussi di capitale.
    """
    weights_series = pd.Series(weights).reindex(prices.columns).fillna(0.0)
    normalized = prices / prices.iloc[0]
    return (normalized.mul(weights_series, axis=1).sum(axis=1) * base).rename("Indice portafoglio")
