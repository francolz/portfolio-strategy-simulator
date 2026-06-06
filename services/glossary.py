"""Contenuti testuali per manuale utente, metodologie e glossario."""

from __future__ import annotations

MANUAL_MARKDOWN = """
## Manuale operativo

### Scopo dell'applicazione
Questa applicazione confronta tre alternative sullo stesso orizzonte temporale:

1. **PAC**: versamenti periodici investiti in un portafoglio di ETF, fondi o asset quotati.
2. **Buy and Hold**: investimento unico iniziale nello stesso portafoglio.
3. **Capitale non investito**: capitale mantenuto liquido e progressivamente eroso dall'inflazione.

L'obiettivo è mostrare l'impatto combinato di mercato, costi, fiscalità e inflazione.

### Come configurare una simulazione
1. Inserisci i ticker Yahoo Finance separati da virgola, ad esempio `SWDA.MI, EIMI.MI`.
2. Inserisci i pesi del portafoglio, ad esempio `80, 20`. Se non inserisci nulla, il portafoglio sarà equiponderato.
3. Scegli data iniziale e finale.
4. Configura importo, frequenza e giorno del versamento PAC.
5. Configura capitale Buy and Hold: manuale o uguale al totale versato dal PAC.
6. Inserisci costi, TER, aliquota fiscale e tasso risk-free.
7. Scegli inflazione manuale o CSV storico.

### Come interpretare i risultati
- **Valore finale lordo**: valore prima della tassazione finale, dopo costi di acquisto e TER.
- **Valore finale netto**: valore finale dopo la tassazione della plusvalenza positiva.
- **Profitto netto**: valore finale netto meno capitale versato/investito.
- **CAGR**: crescita annua composta rispetto al capitale totale di riferimento.
- **XIRR**: rendimento annualizzato money-weighted con date reali dei flussi; è particolarmente utile per il PAC.
- **Maximum Drawdown**: perdita massima dai massimi storici durante il periodo.
- **Sharpe Ratio**: rendimento corretto per il rischio rispetto al tasso risk-free.

### Come leggere grafici e tabelle
- La tabella comparativa evidenzia automaticamente il miglior risultato per metrica.
- Il grafico di evoluzione capitale mostra PAC, Buy and Hold e valore reale del capitale non investito.
- La sezione performance mostra drawdown, rendimenti cumulati, rendimenti annuali, distribuzione dei rendimenti e volatilità.

### Differenze tra PAC e Buy and Hold
Il PAC distribuisce il rischio di ingresso su più date, quindi può ridurre l'impatto di un investimento effettuato in un picco di mercato. Il Buy and Hold investe subito tutto il capitale e tende a beneficiare maggiormente dei mercati crescenti, ma è più esposto al timing iniziale. L'XIRR è spesso la metrica più corretta per confrontare strategie con flussi in date diverse.
"""

METHODOLOGY_MARKDOWN = """
## Metodologie di calcolo

### Logica PAC
Per ogni versamento periodico l'applicazione:
1. individua la data richiesta;
2. sposta l'operazione al primo giorno di mercato disponibile, se l'opzione è attiva;
3. sottrae commissione fissa, commissione percentuale, cambio e slippage;
4. alloca il capitale netto sugli asset secondo i pesi;
5. acquista quote frazionarie;
6. calcola il valore giornaliero di ogni lotto;
7. applica il TER come erosione composta giornaliera;
8. somma tutti i lotti per ottenere il valore totale;
9. tassa solo la plusvalenza positiva finale.

### Logica Buy and Hold
L'investimento unico viene effettuato alla prima seduta disponibile. Il capitale netto dopo i costi viene allocato secondo i pesi del portafoglio. Le quote restano costanti fino alla fine del periodo, salvo l'effetto economico del TER modellato come drag giornaliero.

### Commissioni e costi
Per ogni acquisto:

`costi espliciti = commissione fissa + capitale lordo × (commissione percentuale + costo cambio + slippage)`

Il capitale effettivamente investito è:

`capitale netto = capitale lordo - costi espliciti`

### TER
Il TER annuo viene approssimato giornalmente:

`valore_lotto_t = valore_lordo_lotto_t × (1 - TER)^(giorni_dal_acquisto / 365,25)`

### Fiscalità
L'imposta si applica solo alla plusvalenza positiva finale:

`plusvalenza tassabile = max(valore finale lordo - capitale netto investito, 0)`

`imposta = plusvalenza tassabile × aliquota fiscale`

Se la plusvalenza è negativa, l'imposta è zero.

### Inflazione
Con tasso medio annuo costante:

`valore reale = capitale nominale / (1 + inflazione)^anni`

Con CSV storico, i tassi annui vengono trasformati in tassi giornalieri composti e cumulati nel tempo.

### CAGR

`CAGR = (valore finale / capitale iniziale o totale versato)^(1 / anni) - 1`

Per il PAC il CAGR è una misura sintetica rispetto al totale versato; per valutare correttamente flussi distribuiti nel tempo è preferibile usare XIRR.

### IRR
L'IRR è il tasso che rende nullo il valore attuale netto di flussi periodici equidistanti. Per il PAC viene annualizzato in base alla frequenza dei versamenti.

### XIRR
L'XIRR usa le date effettive dei flussi:

`Σ CF_i / (1 + r)^((data_i - data_0) / 365,25) = 0`

### Sharpe Ratio

`Sharpe = (rendimento medio giornaliero - risk-free giornaliero) / volatilità giornaliera × sqrt(252)`

### Maximum Drawdown

`drawdown_t = valore_t / massimo storico fino a t - 1`

Il Maximum Drawdown è il valore minimo della serie dei drawdown.

### Rendimento reale

`rendimento reale = (1 + rendimento nominale) / (1 + inflazione cumulata) - 1`
"""

GLOSSARY = {
    "PAC": "Piano di Accumulo del Capitale: strategia che investe importi periodici, riducendo il rischio di concentrare l'ingresso in una sola data.",
    "Buy and Hold": "Strategia che investe il capitale in un'unica soluzione e mantiene la posizione nel tempo senza operazioni intermedie.",
    "ETF": "Exchange Traded Fund: fondo quotato in borsa che replica un indice, un settore, un paniere di obbligazioni o altre esposizioni finanziarie.",
    "TER": "Total Expense Ratio: costo annuo ricorrente di un fondo o ETF, espresso in percentuale del patrimonio investito.",
    "CAGR": "Compound Annual Growth Rate: tasso annuo composto che trasforma il capitale iniziale nel valore finale nel periodo osservato.",
    "IRR": "Internal Rate of Return: tasso interno di rendimento che rende nullo il valore attuale netto di flussi periodici.",
    "XIRR": "Versione dell'IRR che usa date reali dei flussi, utile quando i versamenti non sono perfettamente equidistanti.",
    "Drawdown": "Perdita percentuale rispetto al massimo storico precedente del valore della strategia.",
    "Maximum Drawdown": "Peggior drawdown registrato nel periodo, cioè la massima perdita dai massimi storici.",
    "Volatilità": "Misura della variabilità dei rendimenti. Una volatilità alta indica oscillazioni più ampie.",
    "Sharpe Ratio": "Indicatore di rendimento corretto per il rischio. Valori più alti indicano migliore compensazione per la volatilità assunta.",
    "Plusvalenza": "Differenza positiva tra valore finale lordo e capitale netto investito. È la base su cui viene applicata la tassazione finale.",
    "Tassazione": "Imposta applicata alla plusvalenza positiva. Se la plusvalenza è negativa, l'imposta è pari a zero.",
    "Inflazione": "Aumento generale dei prezzi che riduce il potere d'acquisto del capitale nel tempo.",
    "Potere d'acquisto": "Quantità di beni e servizi acquistabili con un certo capitale. Diminuisce quando i prezzi aumentano.",
    "Slippage": "Scostamento tra prezzo atteso e prezzo effettivo di esecuzione di un ordine. Nell'app viene modellato come costo percentuale.",
    "Commissione": "Costo esplicito applicato dall'intermediario per eseguire l'acquisto.",
    "Adjusted Close": "Prezzo di chiusura rettificato per dividendi e split, usato per simulazioni storiche più corrette.",
    "Risk Free Rate": "Tasso privo di rischio usato come riferimento per calcolare lo Sharpe Ratio.",
}


def glossary_markdown() -> str:
    """Restituisce il glossario in formato Markdown."""
    rows = ["## Glossario finanziario"]
    for term, definition in GLOSSARY.items():
        rows.append(f"### {term}\n{definition}")
    return "\n\n".join(rows)


def full_manual_markdown() -> str:
    """Restituisce manuale completo, metodologie e glossario."""
    return "\n\n".join([MANUAL_MARKDOWN, METHODOLOGY_MARKDOWN, glossary_markdown()])
