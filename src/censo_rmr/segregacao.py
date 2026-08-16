"""Índices clássicos de segregação racial em setores censitários.

Os índices são aspatiais e dependem da escala/zoneamento. Autocorrelação
espacial deve ser analisada em módulo separado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class IndicesSegregacao:
    n_setores: int
    pop_obs: float
    grupo_x: float
    grupo_y: float
    dissimilaridade: float
    isolamento_x: float
    isolamento_y: float
    exposicao_x_a_y: float
    exposicao_y_a_x: float


def reconstruir_contagens_raciais(
    df: pd.DataFrame,
    *,
    pop_col: str = "POP_TOTAL",
    pct_branca: str = "PCT_BRANCA",
    pct_preta: str = "PCT_PRETA",
    pct_parda: str = "PCT_PARDA",
) -> pd.DataFrame:
    """Reconstrói contagens equivalentes como população observada × participação oficial."""
    requeridas = [pop_col, pct_branca, pct_preta, pct_parda]
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas raciais ausentes: {faltantes}")
    out = df.copy()
    pop = pd.to_numeric(out[pop_col], errors="coerce")
    for pct in (pct_branca, pct_preta, pct_parda):
        out[pct] = pd.to_numeric(out[pct], errors="coerce")
    out["N_BRANCA"] = pop * out[pct_branca] / 100
    out["N_PRETA"] = pop * out[pct_preta] / 100
    out["N_PARDA"] = pop * out[pct_parda] / 100
    out["N_PPI"] = out["N_PRETA"] + out["N_PARDA"]
    return out


def calcular_indices(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    *,
    total_col: str = "POP_TOTAL",
) -> IndicesSegregacao:
    """Calcula D, isolamento de X/Y e exposições cruzadas."""
    dados = df[[x_col, y_col, total_col]].apply(pd.to_numeric, errors="coerce").dropna()
    dados = dados[(dados[total_col] > 0) & (dados[x_col] >= 0) & (dados[y_col] >= 0)]
    x = dados[x_col].to_numpy(dtype=float)
    y = dados[y_col].to_numpy(dtype=float)
    t = dados[total_col].to_numpy(dtype=float)
    X = x.sum()
    Y = y.sum()
    if X <= 0 or Y <= 0:
        raise ValueError("Grupos X e Y precisam ter totais positivos.")
    d = 0.5 * np.abs(x / X - y / Y).sum()
    pxx = ((x / X) * (x / t)).sum()
    pyy = ((y / Y) * (y / t)).sum()
    pxy = ((x / X) * (y / t)).sum()
    pyx = ((y / Y) * (x / t)).sum()
    return IndicesSegregacao(
        n_setores=len(dados),
        pop_obs=float(t.sum()),
        grupo_x=float(X),
        grupo_y=float(Y),
        dissimilaridade=float(d),
        isolamento_x=float(pxx),
        isolamento_y=float(pyy),
        exposicao_x_a_y=float(pxy),
        exposicao_y_a_x=float(pyx),
    )


def calcular_pares_raciais(
    df: pd.DataFrame,
    *,
    grupo: Sequence[str] = ("COD_MUN", "MUNICIPIO"),
    total_col: str = "POP_TOTAL",
) -> pd.DataFrame:
    pares = [
        ("Branca x Preta", "N_BRANCA", "N_PRETA"),
        ("Branca x Parda", "N_BRANCA", "N_PARDA"),
        ("Branca x Preta+Parda", "N_BRANCA", "N_PPI"),
    ]
    linhas = []
    for chave, sub in df.groupby(list(grupo), dropna=False):
        if not isinstance(chave, tuple):
            chave = (chave,)
        base = dict(zip(grupo, chave))
        for nome, x, y in pares:
            r = calcular_indices(sub, x, y, total_col=total_col)
            linhas.append(
                {
                    **base,
                    "PAR": nome,
                    "N_SETORES": r.n_setores,
                    "POP_OBS": r.pop_obs,
                    "GRUPO_X": r.grupo_x,
                    "GRUPO_Y": r.grupo_y,
                    "DISSIMILARIDADE_D": r.dissimilaridade,
                    "ISOLAMENTO_X": r.isolamento_x,
                    "ISOLAMENTO_Y": r.isolamento_y,
                    "EXPOSICAO_X_A_Y": r.exposicao_x_a_y,
                    "EXPOSICAO_Y_A_X": r.exposicao_y_a_x,
                }
            )
    return pd.DataFrame(linhas)
