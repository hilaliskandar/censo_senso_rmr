"""Indicadores habitacionais derivados dos agregados setoriais do Censo 2022.

O módulo calcula dimensões observáveis sem convertê-las automaticamente em um
índice único. Valores suprimidos permanecem ausentes.
"""

from __future__ import annotations

import pandas as pd


VARIAVEIS = (
    "V00001", "V00002", "V00005", "V00022", "V00023", "V00024", "V00025", "V00026",
    "V00050", "V00052", "V00464", "V00200", "V00201", "V00236", "V00237", "V00238",
    "V00312", "V00313", "V00314", "V00315", "V00316", "V00399", "V00400", "V00401", "V00402",
)


def _num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def _pct(num: pd.Series, den: pd.Series) -> pd.Series:
    return 100 * num / den.where(den > 0)


def calcular_indicadores_habitacao(bruto: pd.DataFrame) -> pd.DataFrame:
    faltantes = [c for c in VARIAVEIS if c not in bruto.columns]
    if faltantes:
        raise ValueError(f"Variáveis habitacionais ausentes: {faltantes}")
    out = _num(bruto, list(VARIAVEIS))
    dppo = out["V00001"]

    out["PCT_IMPROVISADOS"] = _pct(out["V00002"], out["V00001"] + out["V00002"])
    out["PCT_CORTICO"] = _pct(out["V00050"], dppo)
    out["PCT_ESTRUTURA_DEGRADADA"] = _pct(out["V00052"], dppo)
    out["MORADORES_POR_DPPO"] = out["V00005"] / dppo.where(dppo > 0)
    out["PCT_DPPO_6MAIS"] = _pct(out[["V00022", "V00023", "V00024", "V00025", "V00026"]].sum(axis=1, min_count=1), dppo)
    out["PCT_SEM_LIGACAO_REDE_AGUA"] = _pct(out["V00464"], dppo)
    out["PCT_AGUA_SO_TERRENO"] = _pct(out["V00200"], dppo)
    out["PCT_AGUA_NAO_ENCANADA"] = _pct(out["V00201"], dppo)
    out["PCT_BANHEIRO_COMPARTILHADO"] = _pct(out["V00236"], dppo)
    out["PCT_SO_SANITARIO_BURACO"] = _pct(out["V00237"], dppo)
    out["PCT_SEM_BANHEIRO_SANITARIO"] = _pct(out["V00238"], dppo)
    out["PCT_ESGOTO_PRECARIO"] = _pct(out[["V00312", "V00313", "V00314", "V00315", "V00316"]].sum(axis=1, min_count=1), dppo)
    out["PCT_ESGOTO_VALA_CORPO_DAGUA"] = _pct(out[["V00313", "V00314"]].sum(axis=1, min_count=1), dppo)
    out["PCT_LIXO_INADEQUADO"] = _pct(out[["V00399", "V00400", "V00401", "V00402"]].sum(axis=1, min_count=1), dppo)
    out["PCT_LIXO_AREA_PUBLICA"] = _pct(out["V00401"], dppo)
    return out


def colunas_indicadores() -> list[str]:
    return [
        "PCT_IMPROVISADOS", "PCT_CORTICO", "PCT_ESTRUTURA_DEGRADADA", "MORADORES_POR_DPPO",
        "PCT_DPPO_6MAIS", "PCT_SEM_LIGACAO_REDE_AGUA", "PCT_AGUA_SO_TERRENO",
        "PCT_AGUA_NAO_ENCANADA", "PCT_BANHEIRO_COMPARTILHADO", "PCT_SO_SANITARIO_BURACO",
        "PCT_SEM_BANHEIRO_SANITARIO", "PCT_ESGOTO_PRECARIO", "PCT_ESGOTO_VALA_CORPO_DAGUA",
        "PCT_LIXO_INADEQUADO", "PCT_LIXO_AREA_PUBLICA",
    ]
