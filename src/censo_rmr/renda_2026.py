"""Revisão metodológica do rendimento do responsável — divulgação 2026.

A mediana V06006 é a medida principal de posição. V06004 (média) é mantida
como descrição e desempate analítico. Nenhuma das duas é renda domiciliar ou
per capita.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


VARIAVEIS_RENDA_2026 = ("CD_SETOR", "V06001", "V06002", "V06004", "V06005", "V06006")


def preparar_renda_2026(bruto: pd.DataFrame, municipios: Mapping[str, str]) -> pd.DataFrame:
    faltantes = [c for c in VARIAVEIS_RENDA_2026 if c not in bruto.columns]
    if faltantes:
        raise ValueError(f"Variáveis de renda 2026 ausentes: {faltantes}")
    df = bruto.loc[:, list(VARIAVEIS_RENDA_2026)].copy()
    df["CD_SETOR"] = df["CD_SETOR"].astype("string")
    df["COD_MUN"] = df["CD_SETOR"].str[:7]
    df = df[df["COD_MUN"].isin(municipios)].copy()
    df["MUNICIPIO"] = df["COD_MUN"].map(municipios)
    for c in VARIAVEIS_RENDA_2026[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.rename(
        columns={
            "V06001": "RESP_DPPO_NOVO",
            "V06002": "MORADORES_DPPO_NOVO",
            "V06004": "RENDA_MEDIA_NOVA",
            "V06005": "VAR_RENDA_NOVA",
            "V06006": "RENDA_MEDIANA_NOVA",
        }
    )
    df["CV_RENDA"] = np.sqrt(df["VAR_RENDA_NOVA"].clip(lower=0)) / df["RENDA_MEDIA_NOVA"].where(df["RENDA_MEDIA_NOVA"] > 0)
    df["RAZAO_MEDIA_MEDIANA"] = df["RENDA_MEDIA_NOVA"] / df["RENDA_MEDIANA_NOVA"].where(df["RENDA_MEDIANA_NOVA"] > 0)
    df["DIF_MEDIA_MEDIANA"] = df["RENDA_MEDIA_NOVA"] - df["RENDA_MEDIANA_NOVA"]
    return df


def classificar_mediana_1sm(df: pd.DataFrame, referencia: float = 1212.0) -> pd.DataFrame:
    out = df.copy()
    med = out["RENDA_MEDIANA_NOVA"]
    out["FAIXA_MEDIANA_1SM"] = np.select(
        [med < referencia, med == referencia, med > referencia],
        [f"Abaixo de R$ {referencia:,.0f}".replace(",", "."), f"Igual a R$ {referencia:,.0f}".replace(",", "."), f"Acima de R$ {referencia:,.0f}".replace(",", ".")],
        default=None,
    )
    out["BAIXO_REND_MEDIANA_REL"] = med < referencia
    return out


def quintil_operacional_mediana_media(df: pd.DataFrame, n_grupos: int = 5) -> pd.DataFrame:
    """Ordena por mediana e usa média apenas para desempatar, formando grupos quase iguais.

    O procedimento não cria linha de pobreza; é uma classificação ordinal para
    análises que exigem grupos aproximadamente equipopulosos de setores.
    """
    out = df.copy()
    validos = out[["RENDA_MEDIANA_NOVA", "RENDA_MEDIA_NOVA"]].notna().all(axis=1)
    idx = out.loc[validos].sort_values(
        ["RENDA_MEDIANA_NOVA", "RENDA_MEDIA_NOVA", "CD_SETOR"],
        kind="mergesort",
    ).index
    n = len(idx)
    if n < n_grupos:
        raise ValueError("Casos válidos insuficientes para quintis operacionais.")
    pos = np.arange(n)
    grupo = np.floor(pos * n_grupos / n).astype(int) + 1
    grupo = np.minimum(grupo, n_grupos)
    out["QUINTIL_OPER_MEDIANA_MEDIA"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out.loc[idx, "QUINTIL_OPER_MEDIANA_MEDIA"] = grupo
    out["BAIXO_REND_QUINTIL_OPER"] = out["QUINTIL_OPER_MEDIANA_MEDIA"].eq(1)

    # Escala contínua [0,1]: 1 indica maior desvantagem econômica relativa.
    rank = pd.Series(np.nan, index=out.index, dtype=float)
    if n == 1:
        rank.loc[idx] = 1.0
    else:
        rank.loc[idx] = 1.0 - (np.arange(n) / (n - 1))
    out["DESV_RENDA_RANK"] = rank
    return out


def resumir_sensibilidade_baixa_renda(df: pd.DataFrame, antiga_col: str | None = None) -> pd.DataFrame:
    linhas = []
    n_validos = int(df["RENDA_MEDIANA_NOVA"].notna().sum())
    specs = {
        "Mediana estrita < referência": df["BAIXO_REND_MEDIANA_REL"].fillna(False),
        "Quintil operacional mediana+média": df["BAIXO_REND_QUINTIL_OPER"].fillna(False),
    }
    if antiga_col and antiga_col in df.columns:
        specs["Classificação antiga"] = df[antiga_col].fillna(False).astype(bool)
    for nome, flag in specs.items():
        linhas.append(
            {
                "ESPECIFICACAO": nome,
                "SETORES_ECON_BAIXO": int(flag.sum()),
                "PCT_ECON_BAIXO": 100 * float(flag.sum()) / n_validos if n_validos else np.nan,
            }
        )
    return pd.DataFrame(linhas)
