"""Indicadores e classificação relativa de infraestrutura do entorno."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import pandas as pd


DIMENSOES_CENTRAIS = (
    "pct_sem_pavimentacao",
    "pct_sem_bueiro",
    "pct_sem_iluminacao",
    "pct_sem_calcada",
    "pct_calcada_com_obstaculo",
    "pct_sem_arvores",
)


@dataclass(frozen=True)
class ResultadoEntorno:
    limiares_p80: dict[str, float]
    n_setores: int
    origem_limiares: str


def classificar_entorno(
    df: pd.DataFrame,
    *,
    dimensoes: Sequence[str] = DIMENSOES_CENTRAIS,
    quantil: float = 0.80,
    limiares: Mapping[str, float] | None = None,
) -> tuple[pd.DataFrame, ResultadoEntorno]:
    faltantes = [c for c in dimensoes if c not in df.columns]
    if faltantes:
        raise ValueError(f"Indicadores do entorno ausentes: {faltantes}")
    out = df.copy()
    for c in dimensoes:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    if limiares is None:
        usados = {c: float(out[c].dropna().quantile(quantil)) for c in dimensoes}
        origem = f"P{int(round(quantil * 100))}_recalculado"
    else:
        aus = [c for c in dimensoes if c not in limiares]
        if aus:
            raise ValueError(f"Limiares explícitos ausentes para: {aus}")
        usados = {c: float(limiares[c]) for c in dimensoes}
        origem = "explicitos"

    flags = pd.DataFrame(index=out.index)
    for c in dimensoes:
        # Ausência de observação não é carência: permanece NA e nunca vira zero.
        flags[c] = out[c].ge(usados[c]).where(out[c].notna())

    out["n_dimensoes_entorno_validas"] = flags.notna().sum(axis=1)
    out["n_carencias_entorno_altas"] = flags.fillna(False).sum(axis=1).astype("Int64")
    out["precariedade_entorno"] = pd.Series(pd.NA, index=out.index, dtype="string")
    validos = out["n_dimensoes_entorno_validas"] > 0
    n = out["n_carencias_entorno_altas"]
    out.loc[validos & (n <= 1), "precariedade_entorno"] = "Baixa ou não identificada"
    out.loc[validos & (n == 2), "precariedade_entorno"] = "Moderada"
    out.loc[validos & (n >= 3), "precariedade_entorno"] = "Alta"
    return out, ResultadoEntorno(limiares_p80=usados, n_setores=len(out), origem_limiares=origem)
