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

1. **Configura il portafoglio**

   Puoi configurare il portafoglio in due modi:

   **Modalità manuale**

   - Inserisci i ticker Yahoo Finance separati da virgola, ad esempio `SWDA.MI, EIMI.MI`.
   - Inserisci i pesi del portafoglio, ad esempio `80, 20`.
   - I pesi possono essere espressi sia come percentuali (`80, 20`) sia come valori decimali (`0.8, 0.2`).
   - Se non inserisci i pesi, il portafoglio viene considerato equiponderato.

   **Modalità da file Excel/CSV**

   - Carica un file `.xlsx` oppure `.csv` contenente almeno due colonne: `ticker` e `peso`.
   - Esempio:

     | ticker | peso |
     |---|---:|
     | FCT.MI | 50 |
     | LDO.MI | 20 |
     | 1AIR.MI | 30 |

   - Il campo `ticker` deve contenere i simboli Yahoo Finance degli strumenti.
   - Il campo `peso` deve contenere il peso desiderato di ciascun asset.
   - I pesi possono essere indicati come percentuali (`50, 20, 30`) oppure come valori decimali (`0.5, 0.2, 0.3`).
   - Se lo stesso ticker compare più volte nel file, i pesi vengono sommati.
   - Dopo il caricamento, l'app mostra un'anteprima del portafoglio importato e usa automaticamente quei ticker e quei pesi per la simulazione.

2. **Scegli il periodo di analisi**

   - Seleziona la data iniziale e la data finale della simulazione.
   - Se la data selezionata non è un giorno di negoziazione, l'app utilizza il primo giorno di mercato disponibile secondo la logica impostata.

3. **Configura il PAC**

   - Inserisci l'importo del versamento periodico.
   - Scegli la frequenza del versamento: mensile o trimestrale.
   - Imposta il giorno del versamento.
   - Puoi attivare l'opzione per acquistare al primo giorno di mercato disponibile.

4. **Configura il Buy and Hold**

   - Scegli se inserire manualmente il capitale iniziale.
   - In alternativa, puoi impostare il capitale Buy and Hold uguale al capitale totale versato dal PAC nel periodo selezionato.

5. **Configura costi, fiscalità e rischio**

   - Inserisci commissioni fisse e percentuali per il PAC.
   - Inserisci commissioni fisse e percentuali per il Buy and Hold.
   - Imposta eventuali costi di cambio, slippage e TER annuo ETF.
   - Inserisci l'aliquota fiscale sulle plusvalenze.
   - Inserisci il tasso risk-free usato per il calcolo dello Sharpe Ratio.

6. **Configura l'inflazione**

   - Puoi inserire manualmente un tasso medio annuo di inflazione.
   - In alternativa, puoi caricare un CSV storico contenente i dati di inflazione.
   - Il CSV storico deve contenere una colonna data e una colonna con il tasso di inflazione annualizzato.

7. **Esegui la simulazione**

   - Clicca su **Esegui simulazione**.
   - L'app scarica i dati storici da Yahoo Finance, calcola le tre strategie e aggiorna dashboard, grafici, tabelle e file esportabili.

### Esempi pratici di configurazione realistica

Questi esempi aiutano a configurare l'app in modo coerente con un utilizzo realistico tramite una banca o un broker bancario tradizionale, come Intesa Sanpaolo, Mediolanum o UniCredit.

I valori indicati sono esempi ragionevoli e prudenziali, non tariffe ufficiali vincolanti. Le commissioni effettive dipendono dal contratto, dal canale operativo, dal profilo cliente, da eventuali promozioni e dal mercato di negoziazione. Prima di usare l'app per valutazioni precise, è sempre opportuno verificare il proprio foglio condizioni.

#### Nota importante sulle commissioni minime

Molti intermediari applicano commissioni del tipo:

`0,19% con minimo 7 €`

L'app non gestisce automaticamente soglie minime e massime. Per simulare correttamente questo tipo di tariffa, si può usare una regola pratica:

* se l'ordine è piccolo e il minimo commissionale è dominante, inserire la commissione minima come **commissione fissa** e lasciare la commissione percentuale a `0`;
* se l'ordine è grande e la commissione percentuale è dominante, inserire la percentuale e lasciare la commissione fissa a `0`;
* se il proprio broker applica davvero sia una componente fissa sia una componente percentuale, valorizzare entrambe.

Esempio:

* ordine da 500 € con tariffa 0,19% minimo 7 €: la commissione teorica percentuale sarebbe 0,95 €, quindi domina il minimo. Nell'app ha senso usare `Commissione fissa = 7` e `Commissione percentuale = 0`;
* ordine da 10.000 € con tariffa 0,19% minimo 7 €: la commissione percentuale sarebbe 19 €, quindi ha senso usare `Commissione fissa = 0` e `Commissione percentuale = 0,19`.

---

## Esempio 1 — ETF globale: SWDA.MI

Questo esempio simula un investimento in un ETF azionario globale ad accumulazione, come iShares Core MSCI World UCITS ETF.

### Asset

| Parametro                  |                 Valore suggerito |
| -------------------------- | -------------------------------: |
| Ticker                     |                        `SWDA.MI` |
| Peso                       |                            `100` |
| Periodo minimo consigliato |                   almeno 10 anni |
| Tipo strumento             |            ETF azionario globale |
| Dividendi                  | incorporati negli Adjusted Close |

### Parametri PAC

| Parametro                                    |                                             Valore suggerito |
| -------------------------------------------- | -----------------------------------------------------------: |
| Importo versamento periodico                 |                                              300 € - 1.000 € |
| Frequenza                                    |                                                      Mensile |
| Giorno versamento                            |                                                  5 oppure 15 |
| Acquisto primo giorno di mercato disponibile |                                                       Attivo |
| Commissione fissa PAC                        |                                                    5 € - 7 € |
| Commissione percentuale PAC                  |               0% se si sta simulando il minimo commissionale |
| Costi cambio PAC                             | 0% se l'acquisto avviene in euro senza conversione valutaria |
| Slippage PAC                                 |                                                0,03% - 0,05% |
| TER annuo ETF PAC                            |                                                        0,20% |

Per versamenti piccoli, una commissione fissa di 5-7 € può incidere molto. Questo è utile per simulare realisticamente l'effetto negativo delle commissioni minime sui PAC di importo ridotto.

### Parametri Buy and Hold

| Parametro                            |                                             Valore suggerito |
| ------------------------------------ | -----------------------------------------------------------: |
| Modalità capitale                    |              Uguale al totale versato dal PAC oppure manuale |
| Commissione fissa Buy and Hold       |                                 0 € se si usa la percentuale |
| Commissione percentuale Buy and Hold |                                                0,19% - 0,25% |
| Costi cambio Buy and Hold            | 0% se l'acquisto avviene in euro senza conversione valutaria |
| Slippage Buy and Hold                |                                                0,03% - 0,05% |
| TER annuo ETF Buy and Hold           |                                                        0,20% |

Per un acquisto unico di importo elevato, la componente percentuale è spesso più realistica della sola commissione fissa.

### Fiscalità e rischio

| Parametro                    |                     Valore suggerito |
| ---------------------------- | -----------------------------------: |
| Aliquota fiscale plusvalenze |                                  26% |
| Risk-free rate               |                              2% - 3% |
| Inflazione                   | CSV storico Italia oppure 2% manuale |

### Interpretazione

Questo scenario è adatto per confrontare un PAC di lungo periodo con un investimento immediato in un ETF globale. Il TER deve essere valorizzato perché SWDA è un ETF. Lo slippage può essere basso perché si tratta normalmente di uno strumento liquido.

---

## Esempio 2 — Azione italiana: Enel

Questo esempio simula un investimento in una singola azione italiana, come Enel.

### Asset

| Parametro                  |                 Valore suggerito |
| -------------------------- | -------------------------------: |
| Ticker                     |                        `ENEL.MI` |
| Peso                       |                            `100` |
| Periodo minimo consigliato |                 almeno 5-10 anni |
| Tipo strumento             |                  Azione italiana |
| Dividendi                  | incorporati negli Adjusted Close |

### Parametri PAC

| Parametro                                    |                               Valore suggerito |
| -------------------------------------------- | ---------------------------------------------: |
| Importo versamento periodico                 |                                500 € - 1.000 € |
| Frequenza                                    |                     Mensile oppure trimestrale |
| Giorno versamento                            |                                    5 oppure 15 |
| Acquisto primo giorno di mercato disponibile |                                         Attivo |
| Commissione fissa PAC                        |                                      5 € - 7 € |
| Commissione percentuale PAC                  | 0% se si sta simulando il minimo commissionale |
| Costi cambio PAC                             |                                             0% |
| Slippage PAC                                 |                                  0,05% - 0,10% |
| TER annuo ETF PAC                            |                                             0% |

Per una singola azione il TER deve essere zero, perché il TER è un costo tipico di ETF e fondi, non delle azioni.

### Parametri Buy and Hold

| Parametro                            |                                Valore suggerito |
| ------------------------------------ | ----------------------------------------------: |
| Modalità capitale                    | Manuale oppure uguale al totale versato dal PAC |
| Commissione fissa Buy and Hold       |                    0 € se si usa la percentuale |
| Commissione percentuale Buy and Hold |                                   0,19% - 0,25% |
| Costi cambio Buy and Hold            |                                              0% |
| Slippage Buy and Hold                |                                   0,05% - 0,10% |
| TER annuo ETF Buy and Hold           |                                              0% |

### Fiscalità e rischio

| Parametro                    |                     Valore suggerito |
| ---------------------------- | -----------------------------------: |
| Aliquota fiscale plusvalenze |                                  26% |
| Risk-free rate               |                              2% - 3% |
| Inflazione                   | CSV storico Italia oppure 2% manuale |

### Interpretazione

Questo scenario è più concentrato e rischioso rispetto all'ETF globale. La volatilità e il Maximum Drawdown possono essere molto più elevati, perché il portafoglio dipende da una sola società. Il TER va lasciato a zero. I dividendi storici sono generalmente riflessi negli Adjusted Close scaricati da Yahoo Finance.

---

## Esempio 3 — BTP italiano

Questo esempio simula un investimento in un titolo di Stato italiano quotato. È utile per confrontare uno scenario obbligazionario con ETF o azioni.

### Asset

| Parametro                  |                        Valore suggerito |
| -------------------------- | --------------------------------------: |
| Ticker                     |     ticker Yahoo Finance del BTP scelto |
| Peso                       |                                   `100` |
| Periodo minimo consigliato | coerente con la vita residua del titolo |
| Tipo strumento             |                Titolo di Stato italiano |
| TER                        |                                      0% |

Nota: per i singoli BTP, Yahoo Finance può avere dati incompleti o ticker difficili da identificare. Se il grafico parte dopo la data selezionata, controllare il warning sulla prima data disponibile e valutare un ticker alternativo. Per analisi obbligazionarie più robuste può essere più semplice usare un ETF obbligazionario governativo, ricordando però che in quel caso va inserito il relativo TER.

### Parametri PAC

Un PAC su un singolo BTP è meno comune rispetto a un PAC su ETF. Ha più senso simulare acquisti periodici solo se si vuole rappresentare una strategia di accumulo su obbligazioni o titoli di Stato.

| Parametro                                    |                                Valore suggerito |
| -------------------------------------------- | ----------------------------------------------: |
| Importo versamento periodico                 | 1.000 € o multipli coerenti con il lotto minimo |
| Frequenza                                    |                                     Trimestrale |
| Giorno versamento                            |                                     5 oppure 15 |
| Acquisto primo giorno di mercato disponibile |                                          Attivo |
| Commissione fissa PAC                        |                                      7 € - 12 € |
| Commissione percentuale PAC                  |    0% se si simula una commissione minima/fissa |
| Costi cambio PAC                             |                                              0% |
| Slippage PAC                                 |                                   0,05% - 0,20% |
| TER annuo ETF PAC                            |                                              0% |

### Parametri Buy and Hold

| Parametro                            |                         Valore suggerito |
| ------------------------------------ | ---------------------------------------: |
| Modalità capitale                    |                                  Manuale |
| Capitale iniziale                    | importo effettivo che si vuole investire |
| Commissione fissa Buy and Hold       |                               7 € - 12 € |
| Commissione percentuale Buy and Hold |                               0% - 0,10% |
| Costi cambio Buy and Hold            |                                       0% |
| Slippage Buy and Hold                |                            0,05% - 0,20% |
| TER annuo ETF Buy and Hold           |                                       0% |

Per un BTP acquistato e mantenuto fino a scadenza, il Buy and Hold è spesso la modalità più coerente. Il PAC può essere usato solo come confronto teorico.

### Fiscalità e rischio

| Parametro                    |                     Valore suggerito |
| ---------------------------- | -----------------------------------: |
| Aliquota fiscale plusvalenze |                                12,5% |
| Risk-free rate               |                              2% - 3% |
| Inflazione                   | CSV storico Italia oppure 2% manuale |

### Interpretazione

Il BTP ha una fiscalità agevolata rispetto ad azioni ed ETF azionari. Il TER va lasciato a zero, perché un singolo titolo di Stato non ha costi annui di gestione come un ETF. Lo slippage può essere superiore rispetto a un ETF molto liquido, soprattutto su strumenti meno scambiati o in fasi di mercato volatili.

Attenzione: l'app usa gli Adjusted Close di Yahoo Finance. Per singoli BTP, la qualità dei dati può essere meno omogenea rispetto ad azioni ed ETF. Inoltre, la simulazione può non rappresentare perfettamente il rendimento effettivo a scadenza, le cedole incassate e il reinvestimento delle cedole. Per questo motivo, i risultati sui BTP vanno interpretati come una simulazione indicativa basata sui prezzi storici disponibili.

---

## Riepilogo veloce dei valori consigliati

| Caso         |   TER | Fiscalità |      Slippage | Costi cambio |             Commissioni PAC |    Commissioni Buy and Hold |
| ------------ | ----: | --------: | ------------: | -----------: | --------------------------: | --------------------------: |
| ETF SWDA.MI  | 0,20% |       26% | 0,03% - 0,05% |           0% | fissa 5-7 € se rata piccola |               0,19% - 0,25% |
| Azione Enel  |    0% |       26% | 0,05% - 0,10% |           0% | fissa 5-7 € se rata piccola |               0,19% - 0,25% |
| BTP italiano |    0% |     12,5% | 0,05% - 0,20% |           0% |                fissa 7-12 € | fissa 7-12 € oppure 0-0,10% |

Questi valori non sostituiscono le condizioni contrattuali del proprio intermediario, ma permettono di ottenere simulazioni più realistiche rispetto a uno scenario senza costi.


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
