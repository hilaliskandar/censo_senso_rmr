"""Indicadores demográficos setoriais do Censo 2022.

Mapeamento das variáveis baseado no dicionário oficial dos Agregados por
Setores Censitários do IBGE e nos metadados históricos do Bloco 1 da RMR.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd


COLUNAS_DEMOGRAFIA = tuple(f"V010{i:02d}" for i in range(6, 42))
COLUNAS_FONTE_DEMOGRAFIA = tuple(["CD_SETOR"] + list(COLUNAS_DEMOGRAFIA))

FAIXAS_TOTAL = {
    "0_4": "V01031",
    "5_9": "V01032",
    "10_14": "V01033",
    "15_19": "V01034",
    "20_24": "V01035",
    "25_29": "V01036",
    "30_39": "V01037",
    "40_49": "V01038",
    "50_59": "V01039",
    "60_69": "V01040",
    "70_MAIS": "V01041",
}


def _pct(num: pd.Series, den: pd.Series) -> pd.Series:
    return 100 * num / den.where(den != 0)


def normalizar_chave_setor(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza a chave original `CD_setor` para a convenção canônica `CD_SETOR`."""
    if "CD_SETOR" in df.columns:
        return df
    if "CD_setor" in df.columns:
        return df.rename(columns={"CD_setor": "CD_SETOR"})
    raise ValueError("Chave setorial ausente: esperado 'CD_SETOR' ou 'CD_setor'.")


def validar_colunas(df: pd.DataFrame) -> None:
    faltantes = [c for c in COLUNAS_DEMOGRAFIA if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas demográficas obrigatórias ausentes: {faltantes}")


def preparar_demografia_setorial(
    bruto: pd.DataFrame,
    municipios: Mapping[str, str],
) -> pd.DataFrame:
    """Recorta a RMR e calcula os indicadores do Bloco 1.

    Valores não numéricos, inclusive marcações de supressão como ``X``, são
    tratados como ausentes e nunca convertidos em zero.
    """
    normalizado = normalizar_chave_setor(bruto)
    validar_colunas(normalizado)
    df = normalizado.loc[:, ["CD_SETOR", *COLUNAS_DEMOGRAFIA]].copy()
    df["CD_SETOR"] = df["CD_SETOR"].astype("string")
    df["COD_MUN"] = df["CD_SETOR"].str[:7]
    df = df[df["COD_MUN"].isin(municipios)].copy()
    df["MUNICIPIO"] = df["COD_MUN"].map(municipios)

    for c in COLUNAS_DEMOGRAFIA:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["POP_TOTAL"] = df["V01006"]
    df["POP_0_14"] = df[["V01031", "V01032", "V01033"]].sum(axis=1, min_count=1)
    df["POP_15_29"] = df[["V01034", "V01035", "V01036"]].sum(axis=1, min_count=1)
    df["POP_30_59"] = df[["V01037", "V01038", "V01039"]].sum(axis=1, min_count=1)
    df["POP_60_MAIS"] = df[["V01040", "V01041"]].sum(axis=1, min_count=1)
    df["POP_15_59"] = df[
        ["V01034", "V01035", "V01036", "V01037", "V01038", "V01039"]
    ].sum(axis=1, min_count=1)

    df["PCT_0_14"] = _pct(df["POP_0_14"], df["POP_TOTAL"])
    df["PCT_15_29"] = _pct(df["POP_15_29"], df["POP_TOTAL"])
    df["PCT_30_59"] = _pct(df["POP_30_59"], df["POP_TOTAL"])
    df["PCT_60_MAIS"] = _pct(df["POP_60_MAIS"], df["POP_TOTAL"])
    df["RAZAO_DEPENDENCIA"] = _pct(df["POP_0_14"] + df["POP_60_MAIS"], df["POP_15_59"])
    df["INDICE_ENVELHECIMENTO"] = _pct(df["POP_60_MAIS"], df["POP_0_14"])
    df["RAZAO_SEXO_H_100M"] = _pct(df["V01007"], df["V01008"])
    return df


def resumir_demografia_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega contagens e recalcula proporções no nível municipal."""
    soma_cols = [
        "POP_TOTAL",
        "POP_0_14",
        "POP_15_29",
        "POP_30_59",
        "POP_60_MAIS",
        "POP_15_59",
        "V01007",
        "V01008",
    ]
    agg = (
        df.groupby(["COD_MUN", "MUNICIPIO"], as_index=False)
        .agg(SETORES=("CD_SETOR", "count"), **{c: (c, "sum") for c in soma_cols})
    )
    agg["PCT_0_14"] = _pct(agg["POP_0_14"], agg["POP_TOTAL"])
    agg["PCT_15_29"] = _pct(agg["POP_15_29"], agg["POP_TOTAL"])
    agg["PCT_30_59"] = _pct(agg["POP_30_59"], agg["POP_TOTAL"])
    agg["PCT_60_MAIS"] = _pct(agg["POP_60_MAIS"], agg["POP_TOTAL"])
    agg["RAZAO_DEPENDENCIA"] = _pct(agg["POP_0_14"] + agg["POP_60_MAIS"], agg["POP_15_59"])
    agg["INDICE_ENVELHECIMENTO"] = _pct(agg["POP_60_MAIS"], agg["POP_0_14"])
    agg["RAZAO_SEXO_H_100M"] = _pct(agg["V01007"], agg["V01008"])
    return agg


def calcular_limiares_heterogeneidade(
    df: pd.DataFrame,
    populacao_minima: int = 100,
    quantil: float = 0.90,
) -> dict[str, float]:
    validos = df[df["POP_TOTAL"] >= populacao_minima]
    if validos.empty:
        raise ValueError("Nenhum setor válido para heterogeneidade demográfica.")
    return {
        "pct_0_14_p90": float(validos["PCT_0_14"].quantile(quantil)),
        "pct_60_mais_p90": float(validos["PCT_60_MAIS"].quantile(quantil)),
    }
