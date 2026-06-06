"""Funzioni fiscali della simulazione."""

from __future__ import annotations


def capital_gain_tax(final_gross_value: float, tax_basis: float, tax_rate: float) -> tuple[float, float]:
    """Calcola plusvalenza tassabile e imposta finale.

    La tassazione viene applicata solo alla plusvalenza positiva finale:

        plusvalenza = max(valore_finale_lordo - prezzo_di_carico_fiscale, 0)
        imposta = plusvalenza * aliquota

    Se la plusvalenza è negativa o nulla, l'imposta è pari a zero.
    """
    gain = max(float(final_gross_value) - float(tax_basis), 0.0)
    tax = gain * max(float(tax_rate), 0.0)
    return gain, tax
