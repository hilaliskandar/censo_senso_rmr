"""Indicadores descritivos de sexo, cor ou raca, alfabetizacao e FCU.

O modulo recebe contagens padronizadas. O mapeamento Vxxxxx -> campo padronizado
fica na camada de aquisicao e nao e inferido aqui.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _pct(num: pd.Series, den: pd.Series) -> pd.Series:
    num = pd.to_numeric(num, errors="coerce")
    den = pd.to_numeric(den, errors="coerce")
    out = pd.Series(np.nan, index=num.index, dtype="float64")
    ok = num.notna() & den.notna() & den.gt(0)
    out.loc[ok] = 100.0 * num.loc[ok] / den.loc[ok]
    return out


def calcular_equidade_alfabetizacao(df: pd.DataFrame) -> pd.DataFrame:
    obrigatorias = [
        "POP_TOTAL", "POP_FEMININO", "POP_BRANCA", "POP_PRETA", "POP_PARDA",
        "POP_AMARELA", "POP_INDIGENA", "POP_15_MAIS", "NAO_ALF_15_MAIS",
    ]
    faltantes = [c for c in obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatorias ausentes: {faltantes}")

    out = df.copy()
    for c in obrigatorias:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["PCT_FEMININO"] = _pct(out["POP_FEMININO"], out["POP_TOTAL"])
    out["PCT_BRANCA"] = _pct(out["POP_BRANCA"], out["POP_TOTAL"])
    out["PCT_PRETA"] = _pct(out["POP_PRETA"], out["POP_TOTAL"])
    out["PCT_PARDA"] = _pct(out["POP_PARDA"], out["POP_TOTAL"])
    out["PCT_PRETA_PARDA"] = _pct(out["POP_PRETA"] + out["POP_PARDA"], out["POP_TOTAL"])
    out["PCT_AMARELA"] = _pct(out["POP_AMARELA"], out["POP_TOTAL"])
    out["PCT_INDIGENA"] = _pct(out["POP_INDIGENA"], out["POP_TOTAL"])
    out["TAXA_NAO_ALF_15_MAIS"] = _pct(out["NAO_ALF_15_MAIS"], out["POP_15_MAIS"])

    pares = {
        "MASC": ("NAO_ALF_MASC_15_MAIS", "POP_MASC_15_MAIS"),
        "FEM": ("NAO_ALF_FEM_15_MAIS", "POP_FEM_15_MAIS"),
        "BRANCA": ("NAO_ALF_BRANCA_15_MAIS", "POP_BRANCA_15_MAIS"),
        "PRETA": ("NAO_ALF_PRETA_15_MAIS", "POP_PRETA_15_MAIS"),
        "PARDA": ("NAO_ALF_PARDA_15_MAIS", "POP_PARDA_15_MAIS"),
    }
    for sufixo, (num, den) in pares.items():
        if num in out.columns and den in out.columns:
            out[f"TAXA_NAO_ALF_{sufixo}"] = _pct(out[num], out[den])

    if {"TAXA_NAO_ALF_FEM", "TAXA_NAO_ALF_MASC"}.issubset(out.columns):
        out["GAP_NAO_ALF_FEM_MASC"] = out["TAXA_NAO_ALF_FEM"] - out["TAXA_NAO_ALF_MASC"]

    if {"NAO_ALF_PRETA_15_MAIS", "NAO_ALF_PARDA_15_MAIS", "POP_PRETA_15_MAIS", "POP_PARDA_15_MAIS"}.issubset(out.columns):
        out["TAXA_NAO_ALF_PRETA_PARDA"] = _pct(
            out["NAO_ALF_PRETA_15_MAIS"] + out["NAO_ALF_PARDA_15_MAIS"],
            out["POP_PRETA_15_MAIS"] + out["POP_PARDA_15_MAIS"],
        )

    if {"TAXA_NAO_ALF_PRETA_PARDA", "TAXA_NAO_ALF_BRANCA"}.issubset(out.columns):
        out["GAP_NAO_ALF_PPI_BRANCA"] = out["TAXA_NAO_ALF_PRETA_PARDA"] - out["TAXA_NAO_ALF_BRANCA"]

    if "CD_FCU" in out.columns:
        cd = out["CD_FCU"].astype("string")
        out["SETOR_FCU"] = (cd.notna() & cd.str.strip().ne("")).astype("Int64")

    return out
