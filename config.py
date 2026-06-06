"""Configurazione centrale dell'applicazione."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

APP_TITLE = "Simulatore PAC vs Buy & Hold vs Inflazione"
APP_ICON = "📈"
DEFAULT_TICKERS = "SWDA.MI, EIMI.MI"
DEFAULT_WEIGHTS = "80, 20"
DEFAULT_START = "2015-01-01"
DEFAULT_TAX_RATE = 26.0
DEFAULT_RISK_FREE_RATE = 2.0
TRADING_DAYS_PER_YEAR = 252
DAYS_PER_YEAR = 365.25

Frequency = Literal["Mensile", "Trimestrale"]


@dataclass(frozen=True)
class CostConfig:
    """Parametri di costo applicabili a una strategia.

    Le percentuali sono espresse in forma decimale, quindi 0.01 indica 1%.
    """

    fixed_fee: float = 0.0
    percentage_fee: float = 0.0
    fx_fee: float = 0.0
    slippage: float = 0.0
    annual_ter: float = 0.0

    def explicit_cost_for(self, gross_amount: float) -> float:
        """Calcola i costi espliciti di una singola operazione.

        I costi espliciti includono commissione fissa, commissione percentuale,
        costo di cambio e slippage. Il TER è escluso perché viene modellato come
        erosione giornaliera del valore della posizione.
        """
        variable_cost = gross_amount * (self.percentage_fee + self.fx_fee + self.slippage)
        return max(0.0, self.fixed_fee + variable_cost)


@dataclass(frozen=True)
class TaxConfig:
    """Parametri fiscali della simulazione."""

    capital_gain_tax_rate: float = DEFAULT_TAX_RATE / 100.0
