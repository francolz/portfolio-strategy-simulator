# Simulatore PAC vs Buy & Hold vs Inflazione

Applicazione web Streamlit per simulare e confrontare strategie di investimento su un portafoglio multi-asset usando dati storici reali di Yahoo Finance tramite `yfinance`.

## Funzionalità principali

- Portafoglio multi-asset con ticker Yahoo Finance e pesi personalizzati.
- Download prezzi **Adjusted Close** per includere automaticamente dividendi e split.
- Simulazione PAC mensile o trimestrale.
- Simulazione Buy and Hold con capitale manuale o pari al totale versato dal PAC.
- Capitale non investito con erosione inflazionistica manuale o da CSV storico.
- Costi separati per PAC e Buy and Hold: commissione fissa, percentuale, cambio, slippage, TER.
- Fiscalità sulle sole plusvalenze positive finali.
- Metriche avanzate: CAGR, IRR, XIRR, rendimento reale, volatilità, Maximum Drawdown, Sharpe Ratio, efficienza dei costi.
- Dashboard con 6 tab: sintesi, evoluzione capitale, dettaglio PAC, performance, export, glossario/manuale.
- Export Excel multi-sheet e CSV.

## Struttura progetto

```text
portfolio_strategy_simulator/
├── app.py
├── requirements.txt
├── config.py
├── README.md
├── services/
│   ├── __init__.py
│   ├── market_data.py
│   ├── pac_simulator.py
│   ├── buy_hold_simulator.py
│   ├── inflation.py
│   ├── taxes.py
│   ├── metrics.py
│   └── glossary.py
├── utils/
│   ├── __init__.py
│   ├── export.py
│   ├── dates.py
│   └── helpers.py
└── assets/
    └── .gitkeep
```

## Installazione

Richiede Python 3.10+.

```bash
cd portfolio_strategy_simulator
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows PowerShell/CMD
pip install --upgrade pip
pip install -r requirements.txt
```

## Esecuzione

```bash
streamlit run app.py
```

Apri il browser all'indirizzo mostrato da Streamlit, in genere `http://localhost:8501`.

## Esempio rapido

- Ticker: `SWDA.MI, EIMI.MI`
- Pesi: `80, 20`
- Data inizio: `2015-01-01`
- Data fine: oggi
- PAC: 500 € mensili, giorno 1
- Buy and Hold: capitale uguale al totale versato dal PAC
- Inflazione manuale: 3% annuo
- Aliquota fiscale: 26%
- Risk-free rate: 2%

## CSV inflazione

Il CSV deve contenere una colonna data e una colonna tasso annuo. I nomi sono flessibili.

Esempio:

```csv
Date,Inflation
2015-01-01,0.002
2016-01-01,0.001
2017-01-01,0.012
```

Sono accettati anche valori percentuali come `2.5`, interpretati come `2,5%`.

## Note metodologiche

- I prezzi usati sono Adjusted Close.
- Il TER è modellato come erosione composta giornaliera del valore di ciascun lotto.
- Le imposte si applicano solo se la plusvalenza finale è positiva.
- Per il PAC, CAGR e rendimento totale sono calcolati sul capitale totale versato; XIRR è la metrica più adatta per flussi distribuiti nel tempo.
- Le metriche di rischio del PAC usano rendimenti giornalieri corretti per i flussi di versamento.

## Disclaimer

L'applicazione è pensata per analisi educative e di simulazione. Non costituisce consulenza finanziaria, fiscale o di investimento.
