"""Cruzamentos setoriais entre rendimento, composição doméstica e demografia.

O script histórico usava limiares numéricos hardcoded provenientes de blocos
anteriores. Nesta versão, os limiares são derivados ou recebidos
explicitamente, preservando a rastreabilidade e permitindo análise de
sensibilidade.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .renda import LimiaresRenda, selecionar_setores_validos_renda


@dataclass(frozen=True)
class LimiaresCruzamentos:
    monoparental_alta: float
    unipessoal_alta: float
    estendida_alta: float
    jovem_alto: float
    idoso_alto: float


def calcular_limiares_cruzamentos(
    composicao_demografia: pd.DataFrame,
    quantil: float = 0.90,
    populacao_minima: int = 100,
    denominador_minimo: int = 20,
) -> LimiaresCruzamentos:
    """Calcula limiares relativos da própria RMR em vez de usar constantes ocultas.

    A regra padrão reproduz a lógica do processamento histórico: p90 entre
    setores com população e denominadores mínimos adequados.
    """
    requeridas = [
        "POP_TOTAL",
        "DOM_TIPO_DEN",
        "PCT_RESP_SEM_CONJ_COM_FILHOS",
        "PCT_DOM_UNIPESSOAL",
        "PCT_DOM_ESTENDIDA",
        "PCT_0_14",
        "PCT_60_MAIS",
    ]
    faltantes = [c for c in requeridas if c not in composicao_demografia.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {faltantes}")

    validos = composicao_demografia[
        (composicao_demografia["POP_TOTAL"] >= populacao_minima)
        & (composicao_demografia["DOM_TIPO_DEN"] >= denominador_minimo)
    ]
    if validos.empty:
        raise ValueError("Nenhum setor válido para calcular limiares dos cruzamentos.")

    q = lambda c: float(validos[c].quantile(quantil))
    return LimiaresCruzamentos(
        monoparental_alta=q("PCT_RESP_SEM_CONJ_COM_FILHOS"),
        unipessoal_alta=q("PCT_DOM_UNIPESSOAL"),
        estendida_alta=q("PCT_DOM_ESTENDIDA"),
        jovem_alto=q("PCT_0_14"),
        idoso_alto=q("PCT_60_MAIS"),
    )


def cruzar_renda_composicao(
    renda: pd.DataFrame,
    composicao_demografia: pd.DataFrame,
    limiares_renda: LimiaresRenda,
    limiares_cruzamentos: LimiaresCruzamentos,
    responsaveis_minimos: int = 20,
) -> pd.DataFrame:
    cols = [
        "CD_SETOR",
        "PCT_RESP_SEM_CONJ_COM_FILHOS",
        "PCT_DOM_UNIPESSOAL",
        "PCT_DOM_ESTENDIDA",
        "PCT_RESP_60_MAIS",
        "PCT_0_14",
        "PCT_60_MAIS",
    ]
    faltantes = [c for c in cols if c not in composicao_demografia.columns]
    if faltantes:
        raise ValueError(f"Colunas de composição/demografia ausentes: {faltantes}")

    d = renda.merge(composicao_demografia[cols], on="CD_SETOR", how="left", validate="one_to_one")
    validos = selecionar_setores_validos_renda(d, responsaveis_minimos)

    validos["RENDA_BAIXA_REL"] = validos["RENDA_MEDIA_RESP_COM_RENDA"] <= limiares_renda.p20
    validos["MONOP_ALTA"] = (
        validos["PCT_RESP_SEM_CONJ_COM_FILHOS"] >= limiares_cruzamentos.monoparental_alta
    )
    validos["UNIP_ALTA"] = validos["PCT_DOM_UNIPESSOAL"] >= limiares_cruzamentos.unipessoal_alta
    validos["ESTENDIDA_ALTA"] = validos["PCT_DOM_ESTENDIDA"] >= limiares_cruzamentos.estendida_alta
    validos["JOVEM_ALTO"] = validos["PCT_0_14"] >= limiares_cruzamentos.jovem_alto
    validos["IDOSO_ALTO"] = validos["PCT_60_MAIS"] >= limiares_cruzamentos.idoso_alto
    return validos


def resumir_cruzamentos_municipios(validos: pd.DataFrame) -> pd.DataFrame:
    linhas: list[dict] = []
    for (cod, mun), g in validos.groupby(["COD_MUN", "MUNICIPIO"], dropna=False):
        linhas.append(
            {
                "COD_MUN": cod,
                "MUNICIPIO": mun,
                "SETORES_VALIDOS": len(g),
                "PCT_RENDA_BAIXA_REL": 100 * g["RENDA_BAIXA_REL"].mean(),
                "PCT_RENDA_BAIXA_E_MONOP_ALTA": 100 * (g["RENDA_BAIXA_REL"] & g["MONOP_ALTA"]).mean(),
                "PCT_RENDA_BAIXA_E_ESTENDIDA_ALTA": 100 * (g["RENDA_BAIXA_REL"] & g["ESTENDIDA_ALTA"]).mean(),
                "PCT_RENDA_BAIXA_E_JOVEM_ALTO": 100 * (g["RENDA_BAIXA_REL"] & g["JOVEM_ALTO"]).mean(),
                "PCT_RENDA_BAIXA_E_IDOSO_UNIP_ALTO": 100
                * (g["RENDA_BAIXA_REL"] & g["IDOSO_ALTO"] & g["UNIP_ALTA"]).mean(),
            }
        )
    return pd.DataFrame(linhas).sort_values("PCT_RENDA_BAIXA_REL", ascending=False)
