"""Applicazione Streamlit per confronto PAC, Buy and Hold e inflazione.

Esecuzione locale:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    APP_ICON,
    APP_TITLE,
    CostConfig,
    DEFAULT_RISK_FREE_RATE,
    DEFAULT_START,
    DEFAULT_TAX_RATE,
    DEFAULT_TICKERS,
    DEFAULT_WEIGHTS,
)
from services.buy_hold_simulator import BuyHoldResult, simulate_buy_and_hold
from services.glossary import full_manual_markdown
from services.inflation import InflationResult, simulate_csv_inflation, simulate_manual_inflation
from services.market_data import MarketDataError, download_adjusted_close, normalize_weights
from services.metrics import cash_flow_adjusted_returns
from services.pac_simulator import PACResult, simulate_pac
from utils.dates import generate_contribution_dates
from utils.export import create_excel_export, dataframe_to_csv_bytes
from utils.helpers import format_currency, format_percentage, parse_tickers, parse_weights

from datetime import date
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")


PERCENTAGE_ROWS = {
    "CAGR",
    "IRR",
    "XIRR",
    "Rendimento totale lordo",
    "Rendimento totale netto",
    "Rendimento reale",
    "Maximum Drawdown",
    "Drawdown corrente",
    "Volatilità annualizzata",
    "Rapporto costi/capitale investito",
    "Rapporto tasse/profitto lordo",
    "Percentuale erosione",
}
CURRENCY_ROWS = {
    "Capitale investito",
    "Costi",
    "Valore finale lordo",
    "Tasse",
    "Valore finale netto",
    "Profitto netto",
    "Capitale nominale",
    "Capitale reale",
    "Perdita potere acquisto",
}
LOWER_IS_BETTER = {"Costi", "Tasse", "Maximum Drawdown", "Volatilità annualizzata"}

def parse_portfolio_upload(uploaded_file) -> tuple[str, str, pd.DataFrame]:
    """Legge un portafoglio da file Excel/CSV.

    Il file deve contenere almeno due colonne:
    - ticker
    - peso

    Sono accettati anche nomi colonna alternativi:
    - ticker, symbol, simbolo, asset
    - peso, weight, allocazione, allocation, percentuale

    Returns:
        tuple con:
        - stringa ticker compatibile con parse_tickers()
        - stringa pesi compatibile con parse_weights()
        - DataFrame pulito per anteprima
    """
    if uploaded_file is None:
        raise ValueError("Nessun file caricato.")

    file_name = uploaded_file.name.lower()

    try:
        uploaded_file.seek(0)

        if file_name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        elif file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=None, engine="python")
        else:
            raise ValueError("Formato file non supportato. Usa .xlsx oppure .csv.")

    except Exception as exc:
        raise ValueError(f"Errore durante la lettura del file portafoglio: {exc}") from exc

    if df.empty:
        raise ValueError("Il file portafoglio è vuoto.")

    normalized_columns = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    ticker_aliases = ["ticker", "tickers", "symbol", "simbolo", "asset"]
    weight_aliases = ["peso", "pesi", "weight", "weights", "allocazione", "allocation", "percentuale"]

    ticker_column = next(
        (normalized_columns[col] for col in ticker_aliases if col in normalized_columns),
        None,
    )
    weight_column = next(
        (normalized_columns[col] for col in weight_aliases if col in normalized_columns),
        None,
    )

    if ticker_column is None or weight_column is None:
        raise ValueError(
            "Il file deve contenere una colonna ticker e una colonna peso. "
            "Esempio: ticker | peso"
        )

    portfolio_df = df[[ticker_column, weight_column]].copy()
    portfolio_df.columns = ["ticker", "peso"]

    portfolio_df["ticker"] = (
        portfolio_df["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    portfolio_df["peso"] = pd.to_numeric(
        portfolio_df["peso"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

    portfolio_df = portfolio_df.dropna(subset=["ticker", "peso"])
    portfolio_df = portfolio_df[portfolio_df["ticker"] != ""]
    portfolio_df = portfolio_df[portfolio_df["peso"] > 0]

    if portfolio_df.empty:
        raise ValueError("Il file non contiene righe valide con ticker e peso positivo.")

    # Se lo stesso ticker compare più volte, sommiamo i pesi.
    portfolio_df = (
        portfolio_df
        .groupby("ticker", as_index=False)["peso"]
        .sum()
    )

    tickers_raw = ", ".join(portfolio_df["ticker"].tolist())
    weights_raw = ", ".join(portfolio_df["peso"].map(lambda value: f"{value:g}").tolist())

    return tickers_raw, weights_raw, portfolio_df

def render_market_data_warning(
    requested_start_date: date,
    prices: pd.DataFrame,
    tickers: list[str],
) -> None:
    """Mostra un avviso se il portafoglio parte dopo la data richiesta.

    Usa prices.attrs["first_valid_dates"], salvato in download_adjusted_close(),
    per identificare solo i ticker che hanno realmente storico più corto.
    """
    if prices.empty:
        return

    requested_start = pd.Timestamp(requested_start_date).normalize()
    actual_start = pd.Timestamp(prices.index.min()).normalize()

    if actual_start <= requested_start:
        return

    raw_first_dates = prices.attrs.get("first_valid_dates", {})

    first_valid_dates = []

    for ticker in tickers:
        raw_date = raw_first_dates.get(ticker)

        if raw_date is None or pd.isna(raw_date):
            first_valid_dates.append(
                {
                    "Ticker": ticker,
                    "Prima data disponibile": "Non disponibile",
                    "Giorni di ritardo": None,
                }
            )
            continue

        first_date = pd.Timestamp(raw_date).normalize()
        delay_days = int((first_date - requested_start).days)

        first_valid_dates.append(
            {
                "Ticker": ticker,
                "Prima data disponibile": first_date.date(),
                "Giorni di ritardo": max(delay_days, 0),
            }
        )

    availability_df = pd.DataFrame(first_valid_dates)

    limiting_assets = availability_df[
        availability_df["Prima data disponibile"].astype(str)
        == str(actual_start.date())
    ]["Ticker"].tolist()

    st.warning(
        "La simulazione non parte dalla data iniziale richiesta. "
        f"Hai richiesto il {requested_start.date()}, ma il portafoglio può essere "
        f"simulato solo dal {actual_start.date()}, perché è la prima data comune "
        "in cui tutti gli asset hanno un prezzo disponibile."
    )

    if limiting_assets:
        st.info(
            "Ticker che stanno limitando l'inizio della simulazione: "
            + ", ".join(limiting_assets)
        )
    else:
        st.info(
            "La simulazione parte dopo la data richiesta, ma non è stato possibile "
            "identificare con certezza un singolo ticker responsabile."
        )

    st.caption(
        "Suggerimento: se vuoi simulare dal periodo selezionato, valuta di sostituire "
        "i ticker indicati con strumenti equivalenti che abbiano uno storico più lungo "
        "su Yahoo Finance."
    )

    with st.expander("Dettaglio disponibilità dati per ticker", expanded=False):
        st.dataframe(
            availability_df,
            use_container_width=True,
            hide_index=True,
        )
def portfolio_df_to_markdown(portfolio_df: pd.DataFrame) -> str:
    """Converte il DataFrame del portafoglio in una piccola tabella Markdown.

    Evita di usare DataFrame.to_markdown(), così non serve aggiungere
    la dipendenza tabulate al requirements.txt.
    """
    lines = [
        "| ticker | peso (%) |",
        "|---|---:|",
    ]

    for _, row in portfolio_df.iterrows():
        lines.append(f"| {row['ticker']} | {row['peso']:.2f} |")

    return "\n".join(lines)


def generate_chatgpt_configuration_prompt(
    broker_name: str,
    portfolio_df: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> str:
    """Genera un prompt da copiare in ChatGPT per configurare i parametri."""
    broker = broker_name.strip() if broker_name.strip() else "[INSERISCI NOME BROKER]"
    portfolio_markdown = portfolio_df_to_markdown(portfolio_df)

    return f"""
Sto usando questo simulatore Streamlit di strategie di investimento:

https://github.com/francolz/portfolio-strategy-simulator

Il mio broker/intermediario è: {broker}

Il periodo che voglio simulare è:

- Data inizio: {start_date}
- Data fine: {end_date}

Questa è la composizione del mio portafoglio:

{portfolio_markdown}

Voglio configurare il simulatore nel modo più realistico possibile.

Aiutami a stimare i parametri più sensati per questo broker e per questi strumenti finanziari.

Il simulatore confronta:

1. PAC
2. Buy and Hold
3. Capitale non investito eroso dall'inflazione

Indicami valori realistici per tutti questi parametri:

## Parametri PAC

- Importo versamento periodico consigliato
- Frequenza consigliata: mensile o trimestrale
- Giorno del versamento
- Commissione fissa PAC
- Commissione percentuale PAC
- Costi di cambio PAC
- Slippage PAC
- TER annuo ETF PAC

## Parametri Buy and Hold

- Capitale iniziale consigliato
- Se ha senso usare capitale manuale o uguale al totale versato dal PAC
- Commissione fissa Buy and Hold
- Commissione percentuale Buy and Hold
- Costi di cambio Buy and Hold
- Slippage Buy and Hold
- TER annuo ETF Buy and Hold

## Fiscalità

- Aliquota fiscale sulle plusvalenze
- Eventuali differenze tra ETF, azioni, obbligazioni o titoli di Stato
- Come impostare la fiscalità se il portafoglio contiene strumenti con tassazione diversa

## Inflazione

- Se usare inflazione manuale o CSV storico
- Tasso medio annuo realistico da usare in assenza di CSV

## Rischio

- Risk-free rate annuo realistico per il calcolo dello Sharpe Ratio

## Note operative

- Eventuali problemi di valuta
- Eventuali problemi di liquidità
- Eventuali limiti dei dati Yahoo Finance
- Eventuali ticker alternativi più adatti se quelli indicati hanno storico incompleto
- Eventuali accorgimenti per rendere la simulazione più realistica

Rispondimi con una tabella pratica pronta da usare nel simulatore.

Quando non hai dati certi sulle commissioni ufficiali del broker, usa stime prudenti e dichiara chiaramente le assunzioni.
""".strip()

def main() -> None:
    """Entry point dell'applicazione Streamlit.

    Streamlit riesegue l'intero script a ogni interazione dell'utente,
    inclusa la selezione dei radio button nelle tab. Per evitare che i
    risultati spariscano dopo una simulazione, salviamo l'ultimo output
    valido in st.session_state e lo riutilizziamo finché l'utente non
    preme nuovamente "Esegui simulazione".
    """
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption(
        "Simula un portafoglio multi-asset con dati Yahoo Finance Adjusted Close, costi, TER, fiscalità e inflazione."
    )

    sidebar_config = render_sidebar()

    if sidebar_config["run"]:
        try:
            st.session_state["simulation_results"] = run_simulation(sidebar_config)
        except (ValueError, MarketDataError) as exc:
            st.error(str(exc))
            return
        except Exception as exc:  # pragma: no cover - protezione UI
            st.exception(exc)
            return

    if "simulation_results" not in st.session_state:
        render_intro()
        return

    results = st.session_state["simulation_results"]
    render_results(
        prices=results["prices"],
        weights=results["weights"],
        pac=results["pac"],
        bh=results["bh"],
        inflation=results["inflation"],
    )

def generate_portfolio_xlsx_prompt(raw_portfolio_description: str) -> str:
    """Genera un prompt per trasformare nomi comuni di strumenti in portafoglio.xlsx.

    L'obiettivo è aiutare l'utente a ottenere un file Excel compatibile con
    il simulatore, partendo da nomi descrittivi come 'Enel', 'Ferrari',
    'MSCI World ETF', ecc.
    """
    description = raw_portfolio_description.strip()

    if not description:
        description = """
Enel 20
Ferrari 20
MSCI World ETF 60
""".strip()

    return f"""
Voglio creare un file Excel chiamato `portafoglio.xlsx` da usare come input in questo simulatore Streamlit:

https://github.com/francolz/portfolio-strategy-simulator

Il simulatore richiede un file Excel con due colonne:

| ticker | peso |
|---|---:|

Dove:

- `ticker` deve essere il ticker Yahoo Finance corretto;
- `peso` deve essere il peso percentuale dell'asset nel portafoglio;
- la somma dei pesi dovrebbe essere 100;
- i ticker devono essere compatibili con Yahoo Finance e, se possibile, avere uno storico dati sufficientemente lungo.

Questa è la lista degli strumenti che vorrei inserire nel portafoglio, con i pesi indicativi:

{description}

Aiutami a trasformare questa lista in un file `portafoglio.xlsx` compatibile con il simulatore.

Istruzioni:

1. Identifica per ogni strumento il ticker Yahoo Finance più appropriato.
2. Se esistono più quotazioni possibili, preferisci:
   - strumenti quotati su Borsa Italiana se disponibili;
   - strumenti quotati in EUR;
   - strumenti con storico dati più lungo;
   - strumenti liquidi e facilmente scaricabili da Yahoo Finance.
3. Se un nome è ambiguo, proponi la scelta più probabile e indicami eventuali alternative.
4. Verifica che la somma dei pesi sia 100. Se non lo è, normalizzala e spiegami la modifica.
5. Crea un file Excel `portafoglio.xlsx` con colonne esattamente:
   - `ticker`
   - `peso`
6. Oltre al file Excel, mostrami anche una tabella riepilogativa con:
   - nome originale inserito;
   - ticker Yahoo Finance scelto;
   - peso;
   - mercato;
   - valuta;
   - eventuali note o alternative.

Formato finale desiderato del file:

| ticker | peso |
|---|---:|
| ENEL.MI | 20 |
| RACE.MI | 20 |
| SWDA.MI | 60 |

Se non puoi creare direttamente il file Excel, forniscimi almeno il contenuto CSV da salvare come `portafoglio.csv`.
""".strip()

def generate_inflation_csv_prompt(
    country_name: str,
    start_date: date,
    end_date: date,
    use_simulation_period: bool,
    custom_start_date: date,
    custom_end_date: date,
    preferred_source: str,
    frequency: str,
) -> str:
    """Genera un prompt per creare un file inflazione.csv compatibile con l'app."""
    country = country_name.strip() if country_name.strip() else "[INSERISCI PAESE]"

    inflation_start = start_date if use_simulation_period else custom_start_date
    inflation_end = end_date if use_simulation_period else custom_end_date

    return f"""
Voglio creare un file CSV chiamato `inflazione.csv` da usare come input in questo simulatore Streamlit:

https://github.com/francolz/portfolio-strategy-simulator

Il simulatore consente di caricare un CSV storico dell'inflazione.

Il file deve contenere almeno queste colonne:

| Date | inflation_rate |
|---|---:|

Dove:

- `Date` deve essere una data in formato `YYYY-MM-DD`;
- `inflation_rate` deve essere il tasso di inflazione annualizzato espresso in forma decimale;
- esempio: `0.025` significa `2,5%`;
- la frequenza desiderata è: {frequency};
- il paese richiesto è: {country};
- il periodo richiesto è da {inflation_start} a {inflation_end}.

Fonte preferita:

{preferred_source}

Aiutami a creare un file `inflazione.csv` compatibile con il simulatore.

Istruzioni:

1. Trova una fonte affidabile per l'inflazione storica del paese indicato.
2. Preferisci fonti ufficiali o facilmente verificabili, ad esempio:
   - istituto statistico nazionale;
   - Eurostat;
   - FRED;
   - OECD;
   - World Bank;
   - banca centrale nazionale.
3. Se disponibili dati mensili, usa dati mensili.
4. Se sono disponibili solo dati annuali, usa dati annuali e spiegami il limite.
5. Il tasso `inflation_rate` deve rappresentare l'inflazione annua osservata nel periodo, preferibilmente variazione anno-su-anno dell'indice dei prezzi.
6. Non usare percentuali testuali nel CSV: usa valori decimali.
   - 2,5% deve diventare `0.025`;
   - -0,3% deve diventare `-0.003`.
7. Il CSV finale deve avere almeno queste colonne:
   - `Date`
   - `inflation_rate`
8. Se utile, puoi aggiungere colonne informative extra, per esempio:
   - `country`
   - `source`
   - `index_name`
   - `calculation`
9. Verifica che le date coprano il periodo richiesto.
10. Mostrami anche le prime e le ultime righe del dataset.

Formato finale desiderato:

```csv
Date,inflation_rate,country,source,calculation
2015-01-01,0.005,Italy,Eurostat/FRED,YoY CPI or HICP inflation
2015-02-01,0.002,Italy,Eurostat/FRED,YoY CPI or HICP inflation""".strip()


def render_sidebar() -> dict:
    """Renderizza tutti gli input utente nella sidebar e restituisce la configurazione."""
    st.sidebar.header("1. Portafoglio")

    with st.sidebar.expander("🤖 Non conosci i ticker Yahoo?", expanded=False):
        st.caption(
            "Inserisci nomi comuni di azioni, ETF o obbligazioni e genera un prompt "
            "da copiare in ChatGPT per creare il file portafoglio.xlsx."
        )

        raw_portfolio_description = st.text_area(
            "Lista strumenti e pesi desiderati",
            value="Enel 20\nFerrari 20\nMSCI World ETF 60",
            height=140,
            help=(
                "Esempio:\n"
                "Enel 20\n"
                "Ferrari 20\n"
                "MSCI World ETF 60"
            ),
        )

        portfolio_prompt = generate_portfolio_xlsx_prompt(raw_portfolio_description)

        st.text_area(
            "Prompt da copiare in ChatGPT",
            value=portfolio_prompt,
            height=320,
            help=(
                "Copia questo prompt in ChatGPT per ottenere un file Excel o CSV "
                "compatibile con il simulatore."
            ),
        )

        st.download_button(
            "Scarica prompt .txt",
            data=portfolio_prompt,
            file_name="prompt_creazione_portafoglio.txt",
            mime="text/plain",
            use_container_width=True,
        )

    portfolio_file = st.sidebar.file_uploader(
        "Carica portafoglio da Excel/CSV",
        type=["xlsx", "csv"],
        help=(
            "File atteso con colonne ticker e peso. "
            "Esempio: ticker | peso con valori FCT.MI | 50"
        ),
    )

    if portfolio_file is not None:
        try:
            tickers_raw, weights_raw, portfolio_preview = parse_portfolio_upload(portfolio_file)

            st.sidebar.success("Portafoglio caricato correttamente.")
            st.sidebar.dataframe(
                portfolio_preview,
                use_container_width=True,
                hide_index=True,
            )

            st.sidebar.text_input(
                "Ticker Yahoo Finance",
                value=tickers_raw,
                disabled=True,
                help="Valori letti dal file caricato.",
            )

            st.sidebar.text_input(
                "Pesi portafoglio",
                value=weights_raw,
                disabled=True,
                help="Valori letti dal file caricato.",
            )

        except ValueError as exc:
            st.sidebar.error(str(exc))
            tickers_raw = st.sidebar.text_input("Ticker Yahoo Finance", value=DEFAULT_TICKERS)
            weights_raw = st.sidebar.text_input(
                "Pesi portafoglio",
                value=DEFAULT_WEIGHTS,
                help="Esempio: 80, 20 oppure 0.8, 0.2",
            )

    else:
        tickers_raw = st.sidebar.text_input("Ticker Yahoo Finance", value=DEFAULT_TICKERS)
        weights_raw = st.sidebar.text_input(
            "Pesi portafoglio",
            value=DEFAULT_WEIGHTS,
            help="Esempio: 80, 20 oppure 0.8, 0.2",
        )

    start_date = st.sidebar.date_input(
        "Data inizio",
        value=pd.Timestamp(DEFAULT_START).date(),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
    )

    end_date = st.sidebar.date_input(
        "Data fine",
        value=date.today(),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
    )

    with st.sidebar.expander("🤖 Ask ChatGPT per configurare i parametri", expanded=False):
        st.caption(
            "Genera un prompt da copiare in ChatGPT per farti suggerire impostazioni "
            "realistiche di costi, fiscalità, TER, slippage, inflazione e risk-free rate."
        )

        broker_name = st.text_input(
            "Nome broker/intermediario",
            value="",
            placeholder="Esempio: Intesa, Mediolanum, UniCredit, Directa...",
        )

        try:
            preview_tickers = parse_tickers(tickers_raw)
            preview_weights = parse_weights(weights_raw, preview_tickers)

            prompt_portfolio_df = pd.DataFrame(
                {
                    "ticker": preview_tickers,
                    "peso": [
                        round(preview_weights[ticker] * 100, 2)
                        for ticker in preview_tickers
                    ],
                }
            )

            st.dataframe(
                prompt_portfolio_df,
                use_container_width=True,
                hide_index=True,
            )

            chatgpt_prompt = generate_chatgpt_configuration_prompt(
                broker_name=broker_name,
                portfolio_df=prompt_portfolio_df,
                start_date=start_date,
                end_date=end_date,
            )

            st.text_area(
                "Prompt da copiare in ChatGPT",
                value=chatgpt_prompt,
                height=360,
                help="Copia questo testo e incollalo in una nuova chat ChatGPT.",
            )

            st.download_button(
                "Scarica prompt .txt",
                data=chatgpt_prompt,
                file_name="prompt_configurazione_simulatore.txt",
                mime="text/plain",
                use_container_width=True,
            )

        except Exception as exc:
            st.warning(
                "Definisci prima un portafoglio valido per generare il prompt. "
                f"Dettaglio: {exc}"
            )

    with st.sidebar.expander("🤖 Genera prompt inflazione.csv", expanded=False):
        st.caption(
            "Genera un prompt da copiare in ChatGPT per creare un CSV storico "
            "dell'inflazione compatibile con il simulatore."
        )

        inflation_country = st.text_input(
            "Paese inflazione",
            value="Italia",
            placeholder="Esempio: Italia, Germania, Stati Uniti, Francia...",
        )

        use_simulation_period_for_inflation = st.checkbox(
            "Usa lo stesso periodo della simulazione",
            value=True,
        )

        custom_inflation_start = start_date
        custom_inflation_end = end_date

        if not use_simulation_period_for_inflation:
            custom_inflation_start = st.date_input(
                "Data inizio inflazione",
                value=start_date,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                key="custom_inflation_start_prompt",
            )

            custom_inflation_end = st.date_input(
                "Data fine inflazione",
                value=end_date,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                key="custom_inflation_end_prompt",
            )

        inflation_frequency_prompt = st.selectbox(
            "Frequenza desiderata",
            ["Mensile", "Annuale"],
            index=0,
        )

        preferred_inflation_source = st.selectbox(
            "Fonte preferita",
            [
                "Fonte ufficiale migliore disponibile",
                "Eurostat",
                "FRED",
                "ISTAT",
                "OECD",
                "World Bank",
                "Banca centrale nazionale",
            ],
            index=0,
        )

        inflation_prompt = generate_inflation_csv_prompt(
            country_name=inflation_country,
            start_date=start_date,
            end_date=end_date,
            use_simulation_period=use_simulation_period_for_inflation,
            custom_start_date=custom_inflation_start,
            custom_end_date=custom_inflation_end,
            preferred_source=preferred_inflation_source,
            frequency=inflation_frequency_prompt,
        )

        st.text_area(
            "Prompt da copiare in ChatGPT",
            value=inflation_prompt,
            height=340,
            help=(
                "Copia questo prompt in ChatGPT per ottenere un file inflazione.csv "
                "compatibile con il simulatore."
            ),
        )

        st.download_button(
            "Scarica prompt .txt",
            data=inflation_prompt,
            file_name="prompt_creazione_inflazione_csv.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.sidebar.header("2. Parametri PAC")
    pac_amount = st.sidebar.number_input(
        "Importo versamento periodico",
        min_value=1.0,
        value=500.0,
        step=50.0,
    )
    pac_frequency = st.sidebar.selectbox("Frequenza", ["Mensile", "Trimestrale"], index=0)
    use_custom_day = st.sidebar.checkbox("Imposta giorno del versamento", value=True)

    pac_day = None
    if use_custom_day:
        pac_day = int(
            st.sidebar.number_input(
                "Giorno del mese",
                min_value=1,
                max_value=31,
                value=1,
                step=1,
            )
        )

    buy_next_market_day = st.sidebar.checkbox(
        "Acquista al primo giorno di mercato disponibile",
        value=True,
    )

    st.sidebar.header("3. Buy and Hold")
    bh_mode = st.sidebar.radio(
        "Modalità capitale iniziale",
        ["Capitale manuale", "Uguale al capitale totale versato dal PAC"],
        index=1,
    )
    bh_initial_capital = st.sidebar.number_input(
        "Capitale iniziale manuale",
        min_value=1.0,
        value=10_000.0,
        step=500.0,
    )

    st.sidebar.header("4. Costi PAC")
    pac_costs = render_cost_inputs("pac", "PAC")

    st.sidebar.header("5. Costi Buy and Hold")
    bh_costs = render_cost_inputs("bh", "Buy and Hold")

    st.sidebar.header("6. Fiscalità e rischio")
    tax_rate = (
        st.sidebar.number_input(
            "Aliquota fiscale plusvalenze (%)",
            min_value=0.0,
            max_value=100.0,
            value=DEFAULT_TAX_RATE,
            step=0.5,
        )
        / 100.0
    )

    risk_free_rate = (
        st.sidebar.number_input(
            "Risk-free rate annuo (%)",
            min_value=-10.0,
            max_value=30.0,
            value=DEFAULT_RISK_FREE_RATE,
            step=0.25,
        )
        / 100.0
    )

    st.sidebar.header("7. Inflazione")
    inflation_mode = st.sidebar.radio(
        "Modalità inflazione",
        ["Tasso medio annuo manuale", "CSV storico"],
        index=0,
    )

    manual_inflation_rate = (
        st.sidebar.number_input(
            "Inflazione media annua (%)",
            min_value=-10.0,
            max_value=100.0,
            value=3.0,
            step=0.25,
        )
        / 100.0
    )

    inflation_csv = None
    if inflation_mode == "CSV storico":
        uploaded = st.sidebar.file_uploader("CSV inflazione", type=["csv"])
        inflation_csv = uploaded.getvalue() if uploaded is not None else None
        st.sidebar.caption(
            "Colonne attese: Date + inflation_rate. "
            "Il tasso deve essere annualizzato e in formato decimale: 0.025 = 2,5%."
        )

    inflation_capital_mode = st.sidebar.radio(
        "Capitale per confronto inflazione",
        ["Totale PAC", "Capitale Buy and Hold", "Manuale"],
        index=0,
    )

    inflation_manual_capital = st.sidebar.number_input(
        "Capitale nominale manuale inflazione",
        min_value=0.0,
        value=10_000.0,
        step=500.0,
    )

    run = st.sidebar.button(
        "Esegui simulazione",
        type="primary",
        use_container_width=True,
    )

    return {
        "run": run,
        "tickers_raw": tickers_raw,
        "weights_raw": weights_raw,
        "start_date": start_date,
        "end_date": end_date,
        "pac_amount": pac_amount,
        "pac_frequency": pac_frequency,
        "pac_day": pac_day,
        "buy_next_market_day": buy_next_market_day,
        "bh_mode": bh_mode,
        "bh_initial_capital": bh_initial_capital,
        "pac_costs": pac_costs,
        "bh_costs": bh_costs,
        "tax_rate": tax_rate,
        "risk_free_rate": risk_free_rate,
        "inflation_mode": inflation_mode,
        "manual_inflation_rate": manual_inflation_rate,
        "inflation_csv": inflation_csv,
        "inflation_capital_mode": inflation_capital_mode,
        "inflation_manual_capital": inflation_manual_capital,
    }



def render_cost_inputs(prefix: str, label: str) -> CostConfig:
    """Renderizza input costi e restituisce CostConfig."""
    with st.sidebar.expander(f"Dettaglio costi {label}", expanded=False):
        fixed_fee = st.number_input(f"Commissione fissa {label}", min_value=0.0, value=1.0 if prefix == "pac" else 5.0, step=0.5, key=f"{prefix}_fixed")
        percentage_fee = st.number_input(f"Commissione percentuale {label} (%)", min_value=0.0, value=0.10, step=0.05, key=f"{prefix}_pct") / 100.0
        fx_fee = st.number_input(f"Costi di cambio {label} (%)", min_value=0.0, value=0.0, step=0.05, key=f"{prefix}_fx") / 100.0
        slippage = st.number_input(f"Slippage {label} (%)", min_value=0.0, value=0.05, step=0.01, key=f"{prefix}_slippage") / 100.0
        annual_ter = st.number_input(f"TER annuo ETF {label} (%)", min_value=0.0, value=0.20, step=0.05, key=f"{prefix}_ter") / 100.0
    return CostConfig(
        fixed_fee=fixed_fee,
        percentage_fee=percentage_fee,
        fx_fee=fx_fee,
        slippage=slippage,
        annual_ter=annual_ter,
    )


def render_intro() -> None:
    """Mostra una schermata introduttiva prima della simulazione."""
    st.info("Configura i parametri nella sidebar e premi **Esegui simulazione**.")
    st.markdown(
        """
        ### Funzionalità incluse
        - Portafoglio multi-asset con pesi personalizzati.
        - Dati Yahoo Finance con prezzi **Adjusted Close**.
        - Confronto PAC, Buy and Hold e capitale reale eroso dall'inflazione.
        - Costi separati per PAC e Buy and Hold.
        - TER, fiscalità sulla plusvalenza positiva, CAGR, IRR, XIRR, Sharpe Ratio e Maximum Drawdown.
        - Export Excel multi-sheet e CSV.
        """
    )


def run_simulation(config: dict) -> dict:
    """Esegue download dati e simulazioni, restituendo risultati persistibili."""
    tickers = parse_tickers(config["tickers_raw"])
    weights = parse_weights(config["weights_raw"], tickers)
    start_ts = pd.Timestamp(config["start_date"]).normalize()
    end_ts = pd.Timestamp(config["end_date"]).normalize()
    if start_ts >= end_ts:
        raise ValueError("La data di inizio deve essere precedente alla data di fine.")

    with st.spinner("Download dati Yahoo Finance e preparazione simulazione..."):
        prices = download_adjusted_close(tuple(tickers), start_ts.strftime("%Y-%m-%d"), end_ts.strftime("%Y-%m-%d"))
        render_market_data_warning(
            requested_start_date=start_ts.date(),
            prices=prices,
            tickers=tickers,
        )
        weights = normalize_weights(weights, prices)
        inflation_unit = build_inflation_result(
            dates=prices.index,
            nominal_capital=1.0,
            mode=config["inflation_mode"],
            manual_rate=config["manual_inflation_rate"],
            csv_bytes=config["inflation_csv"],
        )

        pac_result = simulate_pac(
            prices=prices,
            weights=weights,
            start_date=start_ts,
            end_date=end_ts,
            contribution_amount=config["pac_amount"],
            frequency=config["pac_frequency"],
            day_of_month=config["pac_day"],
            buy_next_market_day=config["buy_next_market_day"],
            costs=config["pac_costs"],
            tax_rate=config["tax_rate"],
            risk_free_rate=config["risk_free_rate"],
            cumulative_inflation=inflation_unit.cumulative_inflation,
        )

        if config["bh_mode"] == "Uguale al capitale totale versato dal PAC":
            bh_capital = pac_result.summary["Capitale investito"]
        else:
            bh_capital = float(config["bh_initial_capital"])

        bh_result = simulate_buy_and_hold(
            prices=prices,
            weights=weights,
            start_date=start_ts,
            end_date=end_ts,
            initial_capital=bh_capital,
            buy_next_market_day=config["buy_next_market_day"],
            costs=config["bh_costs"],
            tax_rate=config["tax_rate"],
            risk_free_rate=config["risk_free_rate"],
            cumulative_inflation=inflation_unit.cumulative_inflation,
        )

        inflation_capital = choose_inflation_capital(config, pac_result, bh_result)
        inflation_result = build_inflation_result(
            dates=prices.index,
            nominal_capital=inflation_capital,
            mode=config["inflation_mode"],
            manual_rate=config["manual_inflation_rate"],
            csv_bytes=config["inflation_csv"],
        )

    return {
        "prices": prices,
        "weights": weights,
        "pac": pac_result,
        "bh": bh_result,
        "inflation": inflation_result,
    }


def build_inflation_result(
    dates: pd.DatetimeIndex,
    nominal_capital: float,
    mode: str,
    manual_rate: float,
    csv_bytes: bytes | None,
) -> InflationResult:
    """Crea il risultato inflazione dalla modalità selezionata."""
    if mode == "CSV storico":
        if not csv_bytes:
            st.warning("CSV inflazione non caricato: uso il tasso manuale come fallback.")
            return simulate_manual_inflation(dates, nominal_capital, manual_rate)
        return simulate_csv_inflation(dates, nominal_capital, BytesIO(csv_bytes))
    return simulate_manual_inflation(dates, nominal_capital, manual_rate)


def choose_inflation_capital(config: dict, pac_result: PACResult, bh_result: BuyHoldResult) -> float:
    """Determina il capitale nominale da usare per il confronto inflazione."""
    mode = config["inflation_capital_mode"]
    if mode == "Capitale Buy and Hold":
        return float(bh_result.summary["Capitale investito"])
    if mode == "Manuale":
        return float(config["inflation_manual_capital"])
    return float(pac_result.summary["Capitale investito"])


def render_results(
    prices: pd.DataFrame,
    weights: dict[str, float],
    pac: PACResult,
    bh: BuyHoldResult,
    inflation: InflationResult,
) -> None:
    """Renderizza le sei tab della dashboard."""
    st.success("Simulazione completata.")
    with st.expander("Portafoglio simulato", expanded=False):
        weights_df = pd.DataFrame({"Ticker": list(weights.keys()), "Peso": list(weights.values())})
        weights_df["Peso"] = weights_df["Peso"].map(lambda x: f"{x:.2%}")
        st.dataframe(weights_df, use_container_width=True, hide_index=True)
        st.caption(f"Dati disponibili dal {prices.index.min().date()} al {prices.index.max().date()} su {len(prices)} sedute comuni.")

    comparison = build_comparison_table(pac, bh, inflation)
    dashboard_summary = build_dashboard_summary(pac, bh, inflation)
    time_series = build_time_series(pac, bh, inflation)
    risk_table = build_risk_table(pac, bh)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "1. Dashboard Sintetica",
            "2. Evoluzione Capitale",
            "3. Dettaglio PAC",
            "4. Analisi Performance",
            "5. Dati Esportabili",
            "6. Glossario e Manuale",
        ]
    )

    with tab1:
        render_dashboard_tab(pac, bh, inflation, comparison)
    with tab2:
        render_capital_evolution_tab(time_series)
    with tab3:
        render_pac_detail_tab(pac)
    with tab4:
        render_performance_tab(pac, bh)
    with tab5:
        render_export_tab(dashboard_summary, pac, bh, time_series, risk_table, comparison)
    with tab6:
        st.markdown(full_manual_markdown())

def format_currency_compact(value: float, currency_symbol: str = "€") -> str:
    """Formatta importi grandi in modo compatto per KPI su schermi piccoli.

    Esempi:
    950      -> € 950
    12_500   -> € 12,5K
    300_000  -> € 300K
    1_250_000 -> € 1,25M
    """
    if value is None or not np.isfinite(value):
        return "n.d."

    abs_value = abs(value)

    if abs_value >= 1_000_000:
        formatted = f"{value / 1_000_000:.2f}M"
    elif abs_value >= 100_000:
        formatted = f"{value / 1_000:.0f}K"
    elif abs_value >= 10_000:
        formatted = f"{value / 1_000:.1f}K"
    else:
        formatted = f"{value:,.0f}"

    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{currency_symbol} {formatted}"


def render_dashboard_tab(pac: PACResult, bh: BuyHoldResult, inflation: InflationResult, comparison: pd.DataFrame) -> None:
    """Tab 1: KPI e tabella comparativa."""
    st.subheader("KPI principali")
    kpi_strategy = st.radio("Strategia KPI", ["PAC", "Buy & Hold"], horizontal=True)
    selected = pac.summary if kpi_strategy == "PAC" else bh.summary
    cols = st.columns(5)
    cols[0].metric("Capitale investito", format_currency_compact(selected["Capitale investito"]))
    cols[1].metric("Valore finale netto", format_currency_compact(selected["Valore finale netto"]))
    cols[2].metric("Profitto netto", format_currency_compact(selected["Profitto netto"]))
    cols[3].metric("CAGR", format_percentage(selected["CAGR"]))
    cols[4].metric("Maximum Drawdown", format_percentage(selected["Maximum Drawdown"]))

    st.subheader("Tabella comparativa")
    
    styled = comparison.style.apply(highlight_best, axis=1)

    currency_rows = [row for row in comparison.index if row in CURRENCY_ROWS]
    percentage_rows = [row for row in comparison.index if row in PERCENTAGE_ROWS]
    numeric_rows = [
        row
        for row in comparison.index
        if row not in CURRENCY_ROWS and row not in PERCENTAGE_ROWS
    ]

    if currency_rows:
        styled = styled.format(format_currency, subset=pd.IndexSlice[currency_rows, :])

    if percentage_rows:
        styled = styled.format(format_percentage, subset=pd.IndexSlice[percentage_rows, :])

    if numeric_rows:
        styled = styled.format(format_comparison_value, subset=pd.IndexSlice[numeric_rows, :])
    
    st.dataframe(styled, use_container_width=True)
    st.caption(
        "Il valore evidenziato indica il miglior risultato nella riga. Per costi e tasse è migliore il valore più basso; per il Maximum Drawdown è migliore il valore più vicino a zero."
    )

    st.subheader("Capitale non investito e inflazione")
    cols = st.columns(4)
    cols[0].metric("Capitale nominale", format_currency_compact(inflation.summary["Capitale nominale"]))
    cols[1].metric("Capitale reale", format_currency_compact(inflation.summary["Capitale reale"]))
    cols[2].metric("Perdita potere d'acquisto", format_currency_compact(inflation.summary["Perdita potere acquisto"]))
    cols[3].metric("Erosione", format_percentage(inflation.summary["Percentuale erosione"]))


def render_capital_evolution_tab(time_series: pd.DataFrame) -> None:
    """Tab 2: grafico evoluzione capitale."""
    st.subheader("Evoluzione del capitale")
    fig = go.Figure()
    for column in time_series.columns:
        fig.add_trace(go.Scatter(x=time_series.index, y=time_series[column], mode="lines", name=column))
    fig.update_layout(
        height=560,
        hovermode="x unified",
        yaxis_title="Valore",
        xaxis_title="Data",
        legend_title="Strategia",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_pac_detail_tab(pac: PACResult) -> None:
    """Tab 3: storico versamenti PAC."""
    st.subheader("Dettaglio operativo PAC")
    st.dataframe(pac.history, use_container_width=True, hide_index=True)
    st.caption("Le colonne per ticker mostrano prezzi e quote acquistate per ciascun asset del portafoglio.")


def render_performance_tab(pac: PACResult, bh: BuyHoldResult) -> None:
    """Tab 4: analisi performance e rischio."""
    st.subheader("Drawdown")
    drawdown_df = pd.concat([pac.drawdown_series, bh.drawdown_series], axis=1).dropna(how="all")
    drawdown_fig = line_figure(drawdown_df, "Drawdown", yaxis_title="Drawdown")
    st.plotly_chart(drawdown_fig, use_container_width=True)

    st.subheader("Rendimenti cumulati cash-flow adjusted")
    pac_returns = cash_flow_adjusted_returns(pac.value_series, pac.cash_flow_series)
    bh_returns = cash_flow_adjusted_returns(bh.value_series, None)
    cumulative_df = pd.DataFrame(
        {
            "PAC": (1.0 + pac_returns).cumprod() - 1.0,
            "Buy & Hold": (1.0 + bh_returns).cumprod() - 1.0,
        }
    ).dropna(how="all")
    st.plotly_chart(line_figure(cumulative_df, "Rendimenti cumulati", yaxis_title="Rendimento"), use_container_width=True)

    st.subheader("Rendimenti annuali")
    annual_df = pd.concat([pac.annual_returns, bh.annual_returns], axis=1).fillna(0.0)
    annual_fig = go.Figure()
    for column in annual_df.columns:
        annual_fig.add_trace(go.Bar(x=annual_df.index.astype(str), y=annual_df[column], name=column))
    annual_fig.update_layout(barmode="group", height=430, yaxis_title="Rendimento annuo", xaxis_title="Anno")
    st.plotly_chart(annual_fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuzione rendimenti giornalieri")
        hist_fig = go.Figure()
        hist_fig.add_trace(go.Histogram(x=pac_returns, name="PAC", opacity=0.65, nbinsx=60))
        hist_fig.add_trace(go.Histogram(x=bh_returns, name="Buy & Hold", opacity=0.65, nbinsx=60))
        hist_fig.update_layout(barmode="overlay", height=430, xaxis_title="Rendimento giornaliero", yaxis_title="Frequenza")
        st.plotly_chart(hist_fig, use_container_width=True)
    with col2:
        st.subheader("Confronto volatilità")
        vol_df = pd.DataFrame(
            {"Strategia": ["PAC", "Buy & Hold"], "Volatilità annualizzata": [pac.risk.annualized_volatility, bh.risk.annualized_volatility]}
        )
        vol_fig = go.Figure([go.Bar(x=vol_df["Strategia"], y=vol_df["Volatilità annualizzata"])])
        vol_fig.update_layout(height=430, yaxis_title="Volatilità")
        st.plotly_chart(vol_fig, use_container_width=True)


def render_export_tab(
    dashboard_summary: pd.DataFrame,
    pac: PACResult,
    bh: BuyHoldResult,
    time_series: pd.DataFrame,
    risk_table: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    """Tab 5: export Excel e CSV."""
    st.subheader("Download dati")
    excel_bytes = create_excel_export(
        dashboard_summary=dashboard_summary,
        pac_history=pac.history,
        buy_hold_history=bh.history,
        time_series=time_series,
        risk_metrics=risk_table,
        strategy_comparison=comparison,
    )
    st.download_button(
        "Scarica Excel multi-sheet (.xlsx)",
        data=excel_bytes,
        file_name="simulazione_portafoglio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.download_button("CSV confronto", dataframe_to_csv_bytes(comparison), "confronto_strategie.csv", "text/csv")
    col2.download_button("CSV storico PAC", dataframe_to_csv_bytes(pac.history), "storico_pac.csv", "text/csv")
    col3.download_button("CSV serie temporali", dataframe_to_csv_bytes(time_series), "serie_temporali.csv", "text/csv")

    st.subheader("Anteprima confronto")
    st.dataframe(comparison.style.format(format_comparison_value), use_container_width=True)


def build_comparison_table(pac: PACResult, bh: BuyHoldResult, inflation: InflationResult) -> pd.DataFrame:
    """Crea tabella comparativa tra PAC, Buy and Hold e inflazione."""
    rows = [
        "Capitale investito",
        "Costi",
        "Valore finale lordo",
        "Tasse",
        "Valore finale netto",
        "Profitto netto",
        "CAGR",
        "Rendimento reale",
        "Maximum Drawdown",
        "Sharpe Ratio",
    ]
    data = {
        "PAC": [pac.summary.get(row, np.nan) for row in rows],
        "Buy & Hold": [bh.summary.get(row, np.nan) for row in rows],
        "Inflazione": [inflation.summary.get(row, np.nan) for row in rows],
    }
    return pd.DataFrame(data, index=rows)


def build_dashboard_summary(pac: PACResult, bh: BuyHoldResult, inflation: InflationResult) -> pd.DataFrame:
    """Crea una tabella sintetica per export."""
    rows = []
    for strategy_name, summary in [
        ("PAC", pac.summary),
        ("Buy & Hold", bh.summary),
        ("Inflazione", inflation.summary),
    ]:
        row = {"Strategia": strategy_name}
        row.update(summary)
        rows.append(row)
    return pd.DataFrame(rows).set_index("Strategia")


def build_time_series(pac: PACResult, bh: BuyHoldResult, inflation: InflationResult) -> pd.DataFrame:
    """Crea serie temporali allineate per grafici ed export."""
    df = pd.concat(
        [
            pac.value_series_net.rename("PAC"),
            bh.value_series_net.rename("Buy & Hold"),
            inflation.series["Capitale reale"].rename("Capitale reale inflazione"),
        ],
        axis=1,
    )
    return df.ffill().dropna(how="all")


def build_risk_table(pac: PACResult, bh: BuyHoldResult) -> pd.DataFrame:
    """Crea tabella metriche rischio per export."""
    return pd.DataFrame(
        [
            {"Strategia": "PAC", **pac.summary},
            {"Strategia": "Buy & Hold", **bh.summary},
        ]
    ).set_index("Strategia")[
        ["Volatilità annualizzata", "Maximum Drawdown", "Drawdown corrente", "Sharpe Ratio"]
    ]

def highlight_best(row: pd.Series) -> list[str]:
    """Evidenzia il miglior valore solo tra PAC e Buy & Hold.

    La colonna Inflazione viene lasciata neutra perché rappresenta uno scenario
    di perdita di potere d'acquisto, non una vera strategia di investimento.
    """
    comparable_columns = [col for col in ["PAC", "Buy & Hold"] if col in row.index]
    numeric = pd.to_numeric(row[comparable_columns], errors="coerce")

    if numeric.dropna().empty:
        return ["" for _ in row]

    metric = str(row.name)
    if metric in LOWER_IS_BETTER:
        best = numeric.min()
    else:
        best = numeric.max()

    styles = []
    for col in row.index:
        if col not in comparable_columns:
            styles.append("")
            continue

        value = pd.to_numeric(row[col], errors="coerce")
        if pd.notna(value) and np.isclose(value, best):
            styles.append("background-color: #1f6f43; color: white; font-weight: 700")
        else:
            styles.append("")

    return styles


def format_comparison_value(value: float) -> str:
    """Formatta celle della tabella comparativa usando il nome riga gestito da Styler.

    Streamlit/Pandas passa solo il valore alla funzione, quindi usiamo un formato
    numerico neutro. I KPI principali usano invece formati valuta/percentuale.
    """
    if pd.isna(value):
        return "n.d."
    return f"{value:,.4f}"


def line_figure(df: pd.DataFrame, title: str, yaxis_title: str) -> go.Figure:
    """Crea grafico lineare Plotly multi-serie."""
    fig = go.Figure()
    for column in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[column], mode="lines", name=str(column)))
    fig.update_layout(height=450, title=title, hovermode="x unified", yaxis_title=yaxis_title, xaxis_title="Data")
    return fig


if __name__ == "__main__":
    main()
