"""Densidade convencional e densidade ajustada pela area efetivamente domiciliada."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ResultadoDensidade:
    limiar_alta_densidade: float
    quantil: float


def _div(num: pd.Series, den: pd.Series) -> pd.Series:
    num = pd.to_numeric(num, errors="coerce")
    den = pd.to_numeric(den, errors="coerce")
    out = pd.Series(np.nan, index=num.index, dtype="float64")
    ok = num.notna() & den.notna() & den.gt(0)
    out.loc[ok] = num.loc[ok] / den.loc[ok]
    return out


def calcular_densidade(
    df: pd.DataFrame,
    *,
    pop_col: str = "POP_TOTAL",
    area_dom_col: str = "AREA_DOM",
    area_total_col: str = "AREA_TOTAL",
    quantil_alta: float = 0.80,
    limiar_alta: float | None = None,
) -> tuple[pd.DataFrame, ResultadoDensidade]:
    """Calcula indicadores territoriais de densidade.

    As areas devem estar em km2. Densidade alta e uma classificacao relativa,
    nao uma medida de precariedade.
    """
    faltantes = [c for c in (pop_col, area_dom_col, area_total_col) if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatorias ausentes: {faltantes}")

    out = df.copy()
    out[pop_col] = pd.to_numeric(out[pop_col], errors="coerce")
    out[area_dom_col] = pd.to_numeric(out[area_dom_col], errors="coerce")
    out[area_total_col] = pd.to_numeric(out[area_total_col], errors="coerce")

    out["DENS_ADJ"] = _div(out[pop_col], out[area_dom_col])
    out["DENS_CONV"] = _div(out[pop_col], out[area_total_col])
    out["PCT_AREA_DOM"] = 100.0 * _div(out[area_dom_col], out[area_total_col])
    out["FATOR"] = _div(out["DENS_ADJ"], out["DENS_CONV"])

    if limiar_alta is None:
        limiar_alta = float(out["DENS_ADJ"].dropna().quantile(quantil_alta))
    out["ALTA_DENS_ADJ"] = out["DENS_ADJ"].ge(limiar_alta).where(out["DENS_ADJ"].notna())

    return out, ResultadoDensidade(float(limiar_alta), quantil_alta)
