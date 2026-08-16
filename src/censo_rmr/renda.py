"""Indicadores de rendimento do responsável no Censo 2022.

Este módulo separa a lógica analítica da leitura de arquivos. Ele reproduz as
regras identificadas no script histórico do Bloco 3, mas recebe os parâmetros
operacionais explicitamente e não contém caminhos de ambiente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd


COLUNAS_FONTE_RENDA = ("CD_SETOR", "V06001", "V06002", "V06004")


@dataclass(frozen=True)
class LimiaresRenda:
    p20: float
    p50: float
    p80: float


def validar_colunas(df: pd.DataFrame, colunas: tuple[str, ...] = COLUNAS_FONTE_RENDA) -> None:
    ausentes = [c for c in colunas if c not in df.columns]
    if ausentes:
        raise ValueError(f"Colunas obrigatórias ausentes: {ausentes}")


def preparar_renda_setorial(
    bruto: pd.DataFrame,
    municipios: Mapping[str, str],
) -> pd.DataFrame:
    """Transforma as variáveis de origem em uma tabela setorial padronizada.

    V06004 é o rendimento nominal médio mensal das pessoas responsáveis com
    rendimento no setor. Não deve ser interpretado como renda domiciliar per
    capita e não deve ser agregado por média simples para obter um valor
    municipal.
    """
    validar_colunas(bruto)
    df = bruto.loc[:, list(COLUNAS_FONTE_RENDA)].copy()
    df["CD_SETOR"] = df["CD_SETOR"].astype("string")
    df["COD_MUN"] = df["CD_SETOR"].str[:7]
    df = df[df["COD_MUN"].isin(municipios)].copy()
    df["MUNICIPIO"] = df["COD_MUN"].map(municipios)

    for c in ("V06001", "V06002"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # Compatibilidade com extrações em que o decimal veio como texto com vírgula.
    df["V06004"] = pd.to_numeric(
        df["V06004"].astype("string").str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df = df.rename(
        columns={
            "V06001": "RESP_DPPO",
            "V06002": "MORADORES_DPPO",
            "V06004": "RENDA_MEDIA_RESP_COM_RENDA",
        }
    )
    df["MORADORES_POR_RESP_DPPO"] = (
        df["MORADORES_DPPO"] / df["RESP_DPPO"].where(df["RESP_DPPO"] > 0)
    )
    return df


def selecionar_setores_validos_renda(
    df: pd.DataFrame,
    responsaveis_minimos: int = 20,
) -> pd.DataFrame:
    """Seleciona setores usados na distribuição relativa de rendimento."""
    return df[
        (df["RESP_DPPO"] >= responsaveis_minimos)
        & df["RENDA_MEDIA_RESP_COM_RENDA"].notna()
        & (df["RENDA_MEDIA_RESP_COM_RENDA"] > 0)
    ].copy()


def calcular_limiares_rmr(
    df: pd.DataFrame,
    responsaveis_minimos: int = 20,
) -> LimiaresRenda:
    validos = selecionar_setores_validos_renda(df, responsaveis_minimos)
    if validos.empty:
        raise ValueError("Nenhum setor válido para calcular os limiares de renda da RMR.")
    s = validos["RENDA_MEDIA_RESP_COM_RENDA"]
    return LimiaresRenda(
        p20=float(s.quantile(0.20)),
        p50=float(s.quantile(0.50)),
        p80=float(s.quantile(0.80)),
    )


def classificar_renda_relativa(df: pd.DataFrame, limiares: LimiaresRenda) -> pd.DataFrame:
    out = df.copy()
    out["FAIXA_RELATIVA_RENDA_SETOR"] = pd.cut(
        out["RENDA_MEDIA_RESP_COM_RENDA"],
        [-float("inf"), limiares.p20, limiares.p80, float("inf")],
        labels=["20% inferior RMR", "Faixa intermediária", "20% superior RMR"],
        include_lowest=True,
    )
    return out


def resumir_renda_municipios(
    df: pd.DataFrame,
    limiares: LimiaresRenda,
    responsaveis_minimos: int = 20,
) -> pd.DataFrame:
    """Produz resumo municipal sem fabricar uma renda municipal por média simples.

    As medidas municipais descrevem a distribuição dos valores setoriais e a
    participação de setores nos extremos relativos da RMR, reproduzindo o
    desenho do Bloco 3 histórico.
    """
    linhas: list[dict] = []
    for (cod, mun), g in df.groupby(["COD_MUN", "MUNICIPIO"], dropna=False):
        v = selecionar_setores_validos_renda(g, responsaveis_minimos)
        linhas.append(
            {
                "COD_MUN": cod,
                "MUNICIPIO": mun,
                "SETORES": len(g),
                "SETORES_RENDA_VALIDOS": len(v),
                "RESP_DPPO_OBSERVADOS": g["RESP_DPPO"].sum(),
                "MORADORES_DPPO_OBSERVADOS": g["MORADORES_DPPO"].sum(),
                "MEDIANA_SETOR_RENDA_MEDIA_RESP": v["RENDA_MEDIA_RESP_COM_RENDA"].median(),
                "P20_SETOR_RENDA_MEDIA_RESP": v["RENDA_MEDIA_RESP_COM_RENDA"].quantile(0.20),
                "P80_SETOR_RENDA_MEDIA_RESP": v["RENDA_MEDIA_RESP_COM_RENDA"].quantile(0.80),
                "PCT_SET_NO_20_INF_RMR": (
                    100 * (v["RENDA_MEDIA_RESP_COM_RENDA"] <= limiares.p20).mean()
                    if len(v)
                    else pd.NA
                ),
                "PCT_SET_NO_20_SUP_RMR": (
                    100 * (v["RENDA_MEDIA_RESP_COM_RENDA"] >= limiares.p80).mean()
                    if len(v)
                    else pd.NA
                ),
                "MEDIANA_MORADORES_POR_RESP_DPPO": v["MORADORES_POR_RESP_DPPO"].median(),
            }
        )
    return pd.DataFrame(linhas).sort_values(
        "MEDIANA_SETOR_RENDA_MEDIA_RESP", ascending=False, na_position="last"
    )


def auditar_ausencia_renda(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby(["COD_MUN", "MUNICIPIO"], as_index=False)
        .agg(
            SETORES=("CD_SETOR", "size"),
            RENDA_AUSENTE=("RENDA_MEDIA_RESP_COM_RENDA", lambda x: x.isna().sum()),
            RENDA_ZERO=("RENDA_MEDIA_RESP_COM_RENDA", lambda x: (x == 0).sum()),
            RESP_AUSENTE=("RESP_DPPO", lambda x: x.isna().sum()),
        )
    )
    out["PCT_RENDA_AUSENTE"] = 100 * out["RENDA_AUSENTE"] / out["SETORES"]
    return out
