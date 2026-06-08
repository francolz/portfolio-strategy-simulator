"""Contenuti testuali per manuale utente, metodologie e glossario."""

from __future__ import annotations


MANUAL_MARKDOWN = """
## Manuale operativo

### Scopo dell'applicazione

Questa applicazione confronta tre alternative sullo stesso orizzonte temporale:

1. **PAC**: versamenti periodici investiti in un portafoglio di ETF, fondi, azioni, obbligazioni o altri asset quotati.
2. **Buy and Hold**: investimento unico iniziale nello stesso portafoglio.
3. **Capitale non investito**: capitale mantenuto liquido e progressivamente eroso dall'inflazione.

L'obiettivo è mostrare l'impatto combinato di:

- andamento dei mercati;
- costi di negoziazione;
- slippage;
- eventuali costi annui aggiuntivi;
- fiscalità;
- inflazione;
- timing di ingresso nel mercato.

L'applicazione è pensata per simulazioni storiche, analisi comparative e studio del comportamento di diverse strategie di investimento.

---

### Come configurare una simulazione

#### 1. Configura il portafoglio

Puoi configurare il portafoglio in due modi.

##### Modalità manuale

- Inserisci i ticker Yahoo Finance separati da virgola, ad esempio `SWDA.MI, EIMI.MI`.
- Inserisci i pesi del portafoglio, ad esempio `80, 20`.
- I pesi possono essere espressi sia come percentuali (`80, 20`) sia come valori decimali (`0.8, 0.2`).
- Se non inserisci i pesi, il portafoglio viene considerato equiponderato.

##### Modalità da file Excel/CSV

Puoi caricare un file `.xlsx` oppure `.csv` contenente almeno due colonne:

| ticker | peso |
|---|---:|
| FCT.MI | 50 |
| LDO.MI | 20 |
| 1AIR.MI | 30 |

Il campo `ticker` deve contenere i simboli Yahoo Finance degli strumenti.

Il campo `peso` deve contenere il peso desiderato di ciascun asset.

I pesi possono essere indicati come percentuali:

`50, 20, 30`

oppure come valori decimali:

`0.5, 0.2, 0.3`

Se lo stesso ticker compare più volte nel file, i pesi vengono sommati.

Dopo il caricamento, l'app mostra un'anteprima del portafoglio importato e usa automaticamente quei ticker e quei pesi per la simulazione.

---

#### 2. Scegli il periodo di analisi

- Seleziona la data iniziale e la data finale della simulazione.
- Se la data selezionata non è un giorno di negoziazione, l'app utilizza il primo giorno di mercato disponibile secondo la logica impostata.
- Se uno o più ticker non hanno storico sufficiente su Yahoo Finance, l'app mostra un avviso e indica quali strumenti stanno limitando l'inizio effettivo della simulazione.

Esempio:

Se chiedi una simulazione dal 2010, ma un ETF ha dati solo dal 2014, l'app può iniziare la simulazione solo dal 2014, perché deve usare date comuni a tutti gli asset del portafoglio.

---

#### 3. Configura il PAC

- Inserisci l'importo del versamento periodico.
- Scegli la frequenza del versamento: mensile o trimestrale.
- Imposta il giorno del versamento.
- Puoi attivare l'opzione per acquistare al primo giorno di mercato disponibile.

Esempio:

| Parametro | Valore |
|---|---:|
| Importo versamento | 500 € |
| Frequenza | Mensile |
| Giorno versamento | 5 |
| Acquista primo giorno disponibile | Sì |

---

#### 4. Configura il Buy and Hold

Puoi scegliere due modalità:

| Modalità | Descrizione |
|---|---|
| Capitale manuale | Inserisci direttamente il capitale iniziale da investire |
| Uguale al totale versato dal PAC | Il Buy and Hold investe subito lo stesso capitale totale che il PAC verserà nel periodo |

La seconda modalità è spesso la più utile per confrontare:

`investire tutto subito`

contro

`investire gradualmente nel tempo`.

---

#### 5. Configura costi, fiscalità e rischio

Per PAC e Buy and Hold puoi impostare costi differenti:

- commissione fissa;
- commissione percentuale;
- costi di cambio;
- slippage;
- costo annuo aggiuntivo opzionale.

Puoi inoltre impostare:

- aliquota fiscale sulle plusvalenze;
- risk-free rate per il calcolo dello Sharpe Ratio.

---

### Nota importante su TER, Adjusted Close e costo annuo aggiuntivo

Nel simulatore il campo operativo è chiamato:

**Costo annuo aggiuntivo**

Questo campo non deve essere interpretato automaticamente come TER da applicare sempre.

Yahoo Finance `Adjusted Close` rettifica i prezzi per split e distribuzioni/dividendi. Non rettifica direttamente il TER.

Tuttavia, quando si usa un ticker reale di ETF scaricato da Yahoo Finance, il prezzo storico dell'ETF rappresenta già la performance reale del fondo. I costi interni del fondo, come il TER o ongoing charges, sono normalmente già riflessi nel NAV/prezzo storico del fondo.

Per questo motivo:

| Caso | Costo annuo aggiuntivo consigliato |
|---|---:|
| ETF reale scaricato da Yahoo Finance | 0% |
| Azione singola | 0% |
| BTP o obbligazione singola | 0% |
| Indice teorico non investibile | TER/costo dello strumento che vuoi simulare |
| Benchmark lordo o proxy non netto costi | TER/costo dello strumento che vuoi simulare |
| Simulazione conservativa/stress test | valore > 0%, ma sapendo che è una penalizzazione extra |

Quindi, per ETF reali come `SWDA.MI`, `CSSPX.MI`, `IWDE.MI`, `XDWD.MI`, nella maggior parte dei backtest storici il valore più pulito è:

`Costo annuo aggiuntivo = 0%`

Se inserisci un valore maggiore di 0%, stai simulando una penalizzazione aggiuntiva rispetto alla performance storica effettiva dell'ETF.

---

#### 6. Configura l'inflazione

Puoi usare due modalità:

##### Tasso medio annuo manuale

Inserisci un tasso medio annuo, ad esempio:

`2%`

L'app calcola il valore reale del capitale usando:

`valore reale = capitale nominale / (1 + inflazione)^anni`

##### CSV storico

Puoi caricare un file CSV con dati storici di inflazione.

Il CSV deve contenere almeno:

| Date | inflation_rate |
|---|---:|
| 2015-01-01 | 0.005 |
| 2015-02-01 | 0.002 |

Dove `inflation_rate` è il tasso di inflazione annualizzato espresso in forma decimale:

- `0.025` significa `2,5%`;
- `-0.003` significa `-0,3%`.

Per simulazioni storiche lunghe, il CSV è preferibile al tasso manuale.

---

#### 7. Esegui la simulazione

Clicca su **Esegui simulazione**.

L'app:

1. scarica i dati storici da Yahoo Finance;
2. normalizza i pesi del portafoglio;
3. simula PAC;
4. simula Buy and Hold;
5. simula capitale non investito eroso dall'inflazione;
6. calcola metriche di performance, rischio, fiscalità e inflazione;
7. aggiorna dashboard, grafici, tabelle ed export.

---

### Esempi pratici di configurazione realistica

Questi esempi aiutano a configurare l'app in modo coerente con un utilizzo realistico tramite banca o broker, come Intesa Sanpaolo, Mediolanum, UniCredit, Fineco, Directa o intermediari simili.

I valori indicati sono esempi ragionevoli e prudenziali, non tariffe ufficiali vincolanti.

Le commissioni effettive dipendono da:

- contratto;
- canale operativo;
- profilo cliente;
- mercato di negoziazione;
- promozioni;
- dimensione dell'ordine;
- eventuali commissioni minime e massime.

Prima di usare l'app per valutazioni precise, è opportuno verificare sempre il proprio foglio condizioni.

---

#### Nota importante sulle commissioni minime

Molti intermediari applicano commissioni del tipo:

`0,19% con minimo 7 €`

L'app non gestisce automaticamente soglie minime e massime.

Per simulare correttamente questo tipo di tariffa, puoi usare questa regola pratica:

- se l'ordine è piccolo e il minimo commissionale è dominante, inserisci la commissione minima come **commissione fissa** e lascia la commissione percentuale a `0`;
- se l'ordine è grande e la commissione percentuale è dominante, inserisci la percentuale e lascia la commissione fissa a `0`;
- se il broker applica davvero sia una componente fissa sia una componente percentuale, valorizza entrambe.

Esempio 1:

Ordine da 500 € con tariffa 0,19% minimo 7 €.

La commissione teorica percentuale sarebbe:

`500 × 0,19% = 0,95 €`

Poiché domina il minimo, nell'app ha senso usare:

| Campo | Valore |
|---|---:|
| Commissione fissa | 7 |
| Commissione percentuale | 0 |

Esempio 2:

Ordine da 10.000 € con tariffa 0,19% minimo 7 €.

La commissione teorica percentuale sarebbe:

`10.000 × 0,19% = 19 €`

In questo caso ha senso usare:

| Campo | Valore |
|---|---:|
| Commissione fissa | 0 |
| Commissione percentuale | 0,19 |

---

## Esempio 1 — ETF globale: SWDA.MI

Questo esempio simula un investimento in un ETF azionario globale ad accumulazione, come iShares Core MSCI World UCITS ETF.

### Asset

| Parametro | Valore suggerito |
|---|---:|
| Ticker | `SWDA.MI` |
| Peso | `100` |
| Periodo minimo consigliato | almeno 10 anni |
| Tipo strumento | ETF azionario globale |
| Dividendi | incorporati negli Adjusted Close |
| Costo annuo aggiuntivo | normalmente 0% se si usa il ticker reale |

### Parametri PAC

| Parametro | Valore suggerito |
|---|---:|
| Importo versamento periodico | 300 € - 1.000 € |
| Frequenza | Mensile |
| Giorno versamento | 5 oppure 15 |
| Acquisto primo giorno di mercato disponibile | Attivo |
| Commissione fissa PAC | 2,95 € - 7 € |
| Commissione percentuale PAC | 0% se si simula il minimo commissionale |
| Costi cambio PAC | 0% se l'acquisto avviene in euro |
| Slippage PAC | 0,01% - 0,05% |
| Costo annuo aggiuntivo PAC | 0% per backtest su ETF reale Yahoo |

Per versamenti piccoli, una commissione fissa può incidere molto. Questo è utile per simulare realisticamente l'effetto negativo delle commissioni minime sui PAC di importo ridotto.

### Parametri Buy and Hold

| Parametro | Valore suggerito |
|---|---:|
| Modalità capitale | Uguale al totale versato dal PAC oppure manuale |
| Commissione fissa Buy and Hold | 0 € se si usa la percentuale |
| Commissione percentuale Buy and Hold | 0,19% - 0,25% |
| Costi cambio Buy and Hold | 0% se l'acquisto avviene in euro |
| Slippage Buy and Hold | 0,01% - 0,05% |
| Costo annuo aggiuntivo Buy and Hold | 0% per backtest su ETF reale Yahoo |

Per un acquisto unico di importo elevato, la componente percentuale è spesso più realistica della sola commissione fissa.

### Fiscalità e rischio

| Parametro | Valore suggerito |
|---|---:|
| Aliquota fiscale plusvalenze | 26% |
| Risk-free rate | coerente con il periodo simulato |
| Inflazione | CSV storico Italia oppure tasso manuale |

### Interpretazione

Questo scenario è adatto per confrontare un PAC di lungo periodo con un investimento immediato in un ETF globale.

Se usi il ticker reale `SWDA.MI` da Yahoo Finance, il costo annuo aggiuntivo dovrebbe normalmente essere 0%. Se imposti un valore maggiore, stai simulando una penalizzazione ulteriore rispetto alla performance storica reale del fondo.

Lo slippage può essere basso perché si tratta normalmente di uno strumento liquido.

---

## Esempio 2 — Azione italiana: Enel

Questo esempio simula un investimento in una singola azione italiana, come Enel.

### Asset

| Parametro | Valore suggerito |
|---|---:|
| Ticker | `ENEL.MI` |
| Peso | `100` |
| Periodo minimo consigliato | almeno 5-10 anni |
| Tipo strumento | Azione italiana |
| Dividendi | incorporati negli Adjusted Close |
| Costo annuo aggiuntivo | 0% |

### Parametri PAC

| Parametro | Valore suggerito |
|---|---:|
| Importo versamento periodico | 500 € - 1.000 € |
| Frequenza | Mensile oppure trimestrale |
| Giorno versamento | 5 oppure 15 |
| Acquisto primo giorno di mercato disponibile | Attivo |
| Commissione fissa PAC | 5 € - 7 € |
| Commissione percentuale PAC | 0% se si simula il minimo commissionale |
| Costi cambio PAC | 0% |
| Slippage PAC | 0,05% - 0,10% |
| Costo annuo aggiuntivo PAC | 0% |

Per una singola azione il costo annuo aggiuntivo deve essere zero, perché non esiste un TER come per ETF o fondi.

### Parametri Buy and Hold

| Parametro | Valore suggerito |
|---|---:|
| Modalità capitale | Manuale oppure uguale al totale versato dal PAC |
| Commissione fissa Buy and Hold | 0 € se si usa la percentuale |
| Commissione percentuale Buy and Hold | 0,19% - 0,25% |
| Costi cambio Buy and Hold | 0% |
| Slippage Buy and Hold | 0,05% - 0,10% |
| Costo annuo aggiuntivo Buy and Hold | 0% |

### Fiscalità e rischio

| Parametro | Valore suggerito |
|---|---:|
| Aliquota fiscale plusvalenze | 26% |
| Risk-free rate | coerente con il periodo simulato |
| Inflazione | CSV storico Italia oppure tasso manuale |

### Interpretazione

Questo scenario è più concentrato e rischioso rispetto a un ETF globale. La volatilità e il Maximum Drawdown possono essere molto più elevati, perché il portafoglio dipende da una sola società.

Il costo annuo aggiuntivo va lasciato a zero.

I dividendi storici sono generalmente riflessi negli Adjusted Close scaricati da Yahoo Finance.

---

## Esempio 3 — BTP italiano

Questo esempio simula un investimento in un titolo di Stato italiano quotato. È utile per confrontare uno scenario obbligazionario con ETF o azioni.

### Asset

| Parametro | Valore suggerito |
|---|---:|
| Ticker | ticker Yahoo Finance del BTP scelto |
| Peso | `100` |
| Periodo minimo consigliato | coerente con la vita residua del titolo |
| Tipo strumento | Titolo di Stato italiano |
| Costo annuo aggiuntivo | 0% |

Nota: per i singoli BTP, Yahoo Finance può avere dati incompleti o ticker difficili da identificare. Se il grafico parte dopo la data selezionata, controlla il warning sulla prima data disponibile e valuta un ticker alternativo.

Per analisi obbligazionarie più robuste può essere più semplice usare un ETF obbligazionario governativo. In quel caso, se usi il ticker reale dell'ETF, il costo annuo aggiuntivo va normalmente lasciato a 0%.

### Parametri PAC

Un PAC su un singolo BTP è meno comune rispetto a un PAC su ETF. Ha più senso simulare acquisti periodici solo se vuoi rappresentare una strategia teorica di accumulo su obbligazioni o titoli di Stato.

| Parametro | Valore suggerito |
|---|---:|
| Importo versamento periodico | 1.000 € o multipli coerenti con il lotto minimo |
| Frequenza | Trimestrale |
| Giorno versamento | 5 oppure 15 |
| Acquisto primo giorno di mercato disponibile | Attivo |
| Commissione fissa PAC | 7 € - 12 € |
| Commissione percentuale PAC | 0% se si simula una commissione minima/fissa |
| Costi cambio PAC | 0% |
| Slippage PAC | 0,05% - 0,20% |
| Costo annuo aggiuntivo PAC | 0% |

### Parametri Buy and Hold

| Parametro | Valore suggerito |
|---|---:|
| Modalità capitale | Manuale |
| Capitale iniziale | importo effettivo che si vuole investire |
| Commissione fissa Buy and Hold | 7 € - 12 € |
| Commissione percentuale Buy and Hold | 0% - 0,10% |
| Costi cambio Buy and Hold | 0% |
| Slippage Buy and Hold | 0,05% - 0,20% |
| Costo annuo aggiuntivo Buy and Hold | 0% |

Per un BTP acquistato e mantenuto fino a scadenza, il Buy and Hold è spesso la modalità più coerente. Il PAC può essere usato solo come confronto teorico.

### Fiscalità e rischio

| Parametro | Valore suggerito |
|---|---:|
| Aliquota fiscale plusvalenze | 12,5% |
| Risk-free rate | coerente con il periodo simulato |
| Inflazione | CSV storico Italia oppure tasso manuale |

### Interpretazione

Il BTP ha una fiscalità agevolata rispetto ad azioni ed ETF azionari. Il costo annuo aggiuntivo va lasciato a zero, perché un singolo titolo di Stato non ha costi annui di gestione come un ETF.

Lo slippage può essere superiore rispetto a un ETF molto liquido, soprattutto su strumenti meno scambiati o in fasi di mercato volatili.

Attenzione: l'app usa gli Adjusted Close di Yahoo Finance. Per singoli BTP, la qualità dei dati può essere meno omogenea rispetto ad azioni ed ETF. Inoltre, la simulazione può non rappresentare perfettamente il rendimento effettivo a scadenza, le cedole incassate e il reinvestimento delle cedole.

---

## Riepilogo veloce dei valori consigliati

| Caso | Costo annuo aggiuntivo | Fiscalità | Slippage | Costi cambio | Commissioni PAC | Commissioni Buy and Hold |
|---|---:|---:|---:|---:|---:|---:|
| ETF reale da Yahoo Finance | 0% | 26% | 0,01% - 0,05% | 0% se quotato in EUR | fissa se rata piccola | percentuale o fissa secondo tariffa |
| Azione italiana | 0% | 26% | 0,05% - 0,10% | 0% | fissa se ordine piccolo | percentuale o fissa |
| BTP italiano | 0% | 12,5% | 0,05% - 0,20% | 0% | meno comune | fissa o percentuale |
| Indice teorico / benchmark lordo | TER dello strumento da simulare | dipende dallo strumento | basso | dipende | secondo ipotesi | secondo ipotesi |
| Simulazione conservativa | valore > 0% | dipende | secondo ipotesi | dipende | secondo ipotesi | secondo ipotesi |

Questi valori non sostituiscono le condizioni contrattuali del proprio intermediario, ma permettono di ottenere simulazioni più realistiche rispetto a uno scenario senza costi.

---

### Assistenti ChatGPT integrati

L'app include tre strumenti di supporto che generano prompt già pronti da copiare in ChatGPT. Questi assistenti non modificano direttamente la simulazione, ma aiutano l'utente a preparare meglio i dati e a scegliere parametri più realistici.

#### Non conosci i ticker Yahoo?

Permette di partire da nomi comuni di strumenti finanziari, ad esempio `Enel`, `Ferrari`, `MSCI World ETF`, e genera un prompt per ottenere un file `portafoglio.xlsx` compatibile con l'app.

#### Ask ChatGPT per configurare i parametri

Usa il portafoglio già definito e il nome del broker indicato dall'utente per generare un prompt che chiede suggerimenti realistici su:

- commissioni;
- slippage;
- fiscalità;
- inflazione;
- risk-free rate;
- eventuali costi annui aggiuntivi.

Il prompt include una nota metodologica per evitare di applicare automaticamente un costo annuo aggiuntivo su ETF reali già scaricati da Yahoo Finance.

#### Genera prompt inflazione.csv

Aiuta a creare un prompt per ottenere un file CSV storico dell'inflazione, scegliendo:

- paese;
- periodo;
- frequenza;
- fonte dati preferita.

Queste funzioni sono utili quando l'utente non conosce il ticker corretto, non sa quali costi inserire o vuole costruire un file di inflazione coerente con il periodo simulato.

---

### Come interpretare i risultati

- **Valore finale lordo**: valore prima della tassazione finale, dopo costi di acquisto ed eventuali costi annui aggiuntivi.
- **Valore finale netto**: valore finale dopo la tassazione della plusvalenza positiva.
- **Profitto netto**: valore finale netto meno capitale versato/investito.
- **CAGR**: crescita annua composta rispetto al capitale totale di riferimento.
- **IRR**: rendimento interno calcolato su flussi periodici.
- **XIRR**: rendimento annualizzato money-weighted con date reali dei flussi; è particolarmente utile per il PAC.
- **Maximum Drawdown**: perdita massima dai massimi storici durante il periodo.
- **Sharpe Ratio**: rendimento corretto per il rischio rispetto al tasso risk-free.
- **Rendimento reale**: rendimento corretto per l'inflazione cumulata.
- **Capitale reale inflazione**: potere d'acquisto residuo del capitale non investito.

### Come leggere grafici e tabelle

- La tabella comparativa evidenzia automaticamente il miglior risultato per metrica.
- Per costi e tasse è migliore il valore più basso.
- Per il Maximum Drawdown è migliore il valore più vicino a zero.
- Il grafico di evoluzione capitale mostra PAC, Buy and Hold e valore reale del capitale non investito.
- La sezione performance mostra drawdown, rendimenti cumulati, rendimenti annuali, distribuzione dei rendimenti e volatilità.

### Differenze tra PAC e Buy and Hold

Il PAC distribuisce il rischio di ingresso su più date. Può ridurre l'impatto di un investimento effettuato in un picco di mercato.

Il Buy and Hold investe subito tutto il capitale. Tende a beneficiare maggiormente dei mercati crescenti, ma è più esposto al timing iniziale.

Per confrontare economicamente le due strategie, le metriche più intuitive sono:

- valore finale netto;
- profitto netto;
- rendimento reale;
- capitale finale rispetto al capitale reale eroso dall'inflazione.

Per confrontare il rendimento annualizzato:

- il **CAGR** è naturale per il Buy and Hold;
- l'**XIRR** è più rappresentativo per il PAC perché considera le date effettive dei versamenti.
"""


METHODOLOGY_MARKDOWN = """
## Metodologie di calcolo

### Logica PAC

Per ogni versamento periodico l'applicazione:

1. individua la data richiesta;
2. sposta l'operazione al primo giorno di mercato disponibile, se l'opzione è attiva;
3. sottrae commissione fissa, commissione percentuale, costo cambio e slippage;
4. alloca il capitale netto sugli asset secondo i pesi;
5. acquista quote frazionarie;
6. calcola il valore giornaliero di ogni lotto;
7. applica l'eventuale costo annuo aggiuntivo come erosione composta giornaliera;
8. somma tutti i lotti per ottenere il valore totale;
9. calcola la plusvalenza finale;
10. tassa solo la plusvalenza positiva finale.

### Logica Buy and Hold

L'investimento unico viene effettuato alla prima seduta disponibile.

Il capitale netto dopo i costi viene allocato secondo i pesi del portafoglio.

Le quote restano costanti fino alla fine del periodo, salvo l'eventuale effetto economico del costo annuo aggiuntivo modellato come drag giornaliero.

### Commissioni e costi espliciti

Per ogni acquisto:

`costi espliciti = commissione fissa + capitale lordo × (commissione percentuale + costo cambio + slippage)`

Il capitale effettivamente investito è:

`capitale netto = capitale lordo - costi espliciti`

### Costo annuo aggiuntivo

Il simulatore consente di applicare un costo annuo aggiuntivo opzionale.

Quando impostato, viene approssimato giornalmente:

`valore_lotto_t = valore_lordo_lotto_t × (1 - costo_annuo_aggiuntivo)^(giorni_dal_acquisto / 365,25)`

Questo parametro è utile per:

- benchmark teorici;
- indici non investibili;
- simulazioni conservative;
- costi annui aggiuntivi non già incorporati nei prezzi.

Per ETF reali scaricati da Yahoo Finance, il valore consigliato è normalmente 0%.

### TER e prezzi storici reali

Il TER è il costo corrente interno di un ETF o fondo.

Non viene normalmente addebitato come commissione separata sul conto dell'investitore: è sostenuto internamente dal fondo e si riflette nella performance/NAV del fondo.

Yahoo Adjusted Close rettifica split e distribuzioni/dividendi. Non rettifica direttamente il TER.

Il motivo per cui normalmente non si reinserisce il TER nel simulatore, quando si usano ETF reali, è che il prezzo storico osservato dell'ETF riflette già la performance reale del fondo dopo i costi interni.

Quindi:

`ETF reale Yahoo Finance → costo annuo aggiuntivo consigliato = 0%`

`Indice teorico / benchmark lordo → costo annuo aggiuntivo = TER dello strumento che vuoi simulare`

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

Per il Buy and Hold il CAGR è una metrica naturale, perché il capitale viene investito all'inizio.

Per il PAC il CAGR è una misura sintetica rispetto al totale versato, ma non considera perfettamente il timing dei versamenti. Per valutare correttamente flussi distribuiti nel tempo è preferibile usare XIRR.

### IRR

L'IRR è il tasso che rende nullo il valore attuale netto di flussi periodici equidistanti.

Per il PAC viene annualizzato in base alla frequenza dei versamenti.

### XIRR

L'XIRR usa le date effettive dei flussi:

`Σ CF_i / (1 + r)^((data_i - data_0) / 365,25) = 0`

È particolarmente utile per il PAC, perché ogni versamento avviene in una data diversa.

Nel confronto tra PAC e Buy and Hold:

- per il PAC, XIRR è spesso la metrica annualizzata più rappresentativa;
- per il Buy and Hold, CAGR è normalmente sufficiente e molto leggibile.

### Sharpe Ratio

`Sharpe = (rendimento medio giornaliero - risk-free giornaliero) / volatilità giornaliera × sqrt(252)`

Lo Sharpe Ratio misura il rendimento ottenuto per unità di rischio assunto.

### Maximum Drawdown

`drawdown_t = valore_t / massimo storico fino a t - 1`

Il Maximum Drawdown è il valore minimo della serie dei drawdown.

Rappresenta la massima perdita percentuale dai massimi storici osservata nel periodo.

### Rendimento reale

`rendimento reale = (1 + rendimento nominale) / (1 + inflazione cumulata) - 1`

Il rendimento reale misura la crescita del capitale al netto dell'inflazione.

### Capitale non investito eroso dall'inflazione

La simulazione dell'inflazione mostra cosa sarebbe successo mantenendo il capitale non investito.

L'obiettivo non è rappresentare un rendimento finanziario, ma il decadimento del potere d'acquisto.

Esempio:

Se il capitale nominale resta 10.000 €, ma l'inflazione cumulata è 20%, il capitale reale diventa circa:

`10.000 / 1,20 = 8.333 €`

La perdita di potere d'acquisto è quindi circa 1.667 €.
"""


GLOSSARY = {
    "PAC": (
        "Piano di Accumulo del Capitale: strategia che investe importi periodici. "
        "Riduce il rischio di concentrare tutto l'ingresso in una sola data, ma in mercati fortemente crescenti può rendere meno del Buy and Hold."
    ),
    "Buy and Hold": (
        "Strategia che investe il capitale in un'unica soluzione e mantiene la posizione nel tempo senza operazioni intermedie. "
        "È molto esposta al timing iniziale, ma beneficia pienamente dei mercati crescenti."
    ),
    "ETF": (
        "Exchange Traded Fund: fondo quotato in borsa che replica un indice, un settore, un paniere di obbligazioni o altre esposizioni finanziarie. "
        "Può essere ad accumulazione o distribuzione, fisico o sintetico."
    ),
    "TER": (
        "Total Expense Ratio: costo corrente interno di un fondo o ETF. "
        "Non viene normalmente pagato come commissione separata sul conto, ma si riflette nella performance/NAV del fondo. "
        "Quando si usano prezzi storici reali di ETF, non va normalmente reinserito nel simulatore."
    ),
    "Costo annuo aggiuntivo": (
        "Parametro opzionale del simulatore che applica un costo annuo composto giornalmente. "
        "Per ETF reali scaricati da Yahoo Finance va normalmente lasciato a 0%. "
        "È utile per benchmark teorici, simulazioni conservative o costi non già incorporati nei prezzi."
    ),
    "CAGR": (
        "Compound Annual Growth Rate: tasso annuo composto che trasforma il capitale iniziale nel valore finale nel periodo osservato. "
        "È molto utile per il Buy and Hold."
    ),
    "IRR": (
        "Internal Rate of Return: tasso interno di rendimento che rende nullo il valore attuale netto di flussi periodici. "
        "È utile quando ci sono versamenti o prelievi nel tempo."
    ),
    "XIRR": (
        "Versione dell'IRR che usa date reali dei flussi. "
        "È particolarmente utile per il PAC perché i versamenti avvengono in date diverse."
    ),
    "Drawdown": (
        "Perdita percentuale rispetto al massimo storico precedente del valore della strategia. "
        "Indica quanto una strategia è scesa dai propri massimi."
    ),
    "Maximum Drawdown": (
        "Peggior drawdown registrato nel periodo. "
        "È una delle misure più intuitive del rischio storico."
    ),
    "Volatilità": (
        "Misura della variabilità dei rendimenti. "
        "Una volatilità alta indica oscillazioni più ampie del valore della strategia."
    ),
    "Sharpe Ratio": (
        "Indicatore di rendimento corretto per il rischio. "
        "Valori più alti indicano migliore compensazione per la volatilità assunta rispetto al tasso risk-free."
    ),
    "Plusvalenza": (
        "Differenza positiva tra valore finale lordo e capitale netto investito. "
        "È la base su cui viene applicata la tassazione finale."
    ),
    "Tassazione": (
        "Imposta applicata alla plusvalenza positiva. "
        "Se la plusvalenza è negativa, l'imposta è pari a zero nel simulatore."
    ),
    "Inflazione": (
        "Aumento generale dei prezzi che riduce il potere d'acquisto del capitale nel tempo."
    ),
    "Potere d'acquisto": (
        "Quantità di beni e servizi acquistabili con un certo capitale. "
        "Diminuisce quando i prezzi aumentano."
    ),
    "Slippage": (
        "Scostamento tra prezzo atteso e prezzo effettivo di esecuzione di un ordine. "
        "Nell'app viene modellato come costo percentuale."
    ),
    "Commissione": (
        "Costo esplicito applicato dall'intermediario per eseguire l'acquisto. "
        "Può essere fissa, percentuale o una combinazione delle due."
    ),
    "Adjusted Close": (
        "Prezzo di chiusura rettificato per split e distribuzioni/dividendi. "
        "È usato per simulazioni storiche più coerenti, soprattutto su strumenti con dividendi o split."
    ),
    "Risk Free Rate": (
        "Tasso privo di rischio usato come riferimento per calcolare lo Sharpe Ratio. "
        "Nel simulatore è parametrizzabile."
    ),
}


def glossary_markdown() -> str:
    """Restituisce il glossario in formato Markdown."""
    rows = ["## Glossario finanziario"]

    for term, definition in GLOSSARY.items():
        rows.append(f"### {term}\n{definition}")

    return "\n\n".join(rows)


def full_manual_markdown() -> str:
    """Restituisce manuale completo, metodologie e glossario."""
    return "\n\n".join(
        [
            MANUAL_MARKDOWN,
            METHODOLOGY_MARKDOWN,
            glossary_markdown(),
        ]
    )