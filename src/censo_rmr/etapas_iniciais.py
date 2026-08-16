"""Executores dos primeiros blocos do pipeline em área de regressão.

Nenhuma função deste módulo escreve em `03_Tabelas_Indicadores`. Durante a
fase de validação, todos os produtos são gravados apenas em uma pasta de
staging/regressão informada explicitamente pelo chamador.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Mapping

import pandas as pd

from .composicao_domestica import calcular_indicadores, resumo_municipal
from .cruzamentos import (
    calcular_limiares_cruzamentos,
    cruzar_renda_composicao,
    resumir_cruzamentos_municipios,
)
from .demografia import (
    calcular_limiares_heterogeneidade,
    preparar_demografia_setorial,
    resumir_demografia_municipios,
)
from .io_ibge import ler_csv_ibge
from .renda import (
    auditar_ausencia_renda,
    calcular_limiares_rmr,
    classificar_renda_relativa,
    preparar_renda_setorial,
    resumir_renda_municipios,
)


def _pasta(saida: str | Path, etapa: str) -> Path:
    p = Path(saida) / etapa
    p.mkdir(parents=True, exist_ok=True)
    return p


def _salvar_json(obj: dict, caminho: Path) -> None:
    caminho.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def executar_demografia(
    fonte_csv: str | Path,
    saida_regressao: str | Path,
    municipios: Mapping[str, str],
    *,
    populacao_minima: int = 100,
) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "demografia")
    bruto = ler_csv_ibge(fonte_csv, colunas=["CD_SETOR", *[f"V010{i:02d}" for i in range(6, 42)]])
    setorial = preparar_demografia_setorial(bruto, municipios)
    municipal = resumir_demografia_municipios(setorial)
    limiares = calcular_limiares_heterogeneidade(setorial, populacao_minima=populacao_minima)

    validos = setorial[setorial["POP_TOTAL"] >= populacao_minima].copy()
    validos["EXTREMO_JOVEM_P90"] = validos["PCT_0_14"] >= limiares["pct_0_14_p90"]
    validos["EXTREMO_IDOSO_P90"] = validos["PCT_60_MAIS"] >= limiares["pct_60_mais_p90"]
    extremos = validos[
        ["CD_SETOR", "COD_MUN", "MUNICIPIO", "POP_TOTAL", "PCT_0_14", "PCT_60_MAIS", "INDICE_ENVELHECIMENTO", "EXTREMO_JOVEM_P90", "EXTREMO_IDOSO_P90"]
    ].copy()

    paths = {
        "setorial": pasta / "RMR_CENSO2022_DEMOGRAFIA_SETOR.csv",
        "municipal": pasta / "RMR_CENSO2022_DEMOGRAFIA_MUNICIPIOS.csv",
        "extremos": pasta / "RMR_CENSO2022_DEMOGRAFIA_EXTREMOS_SETORIAIS.csv",
        "metadados": pasta / "METADADOS_BLOCO1_DEMOGRAFIA.json",
    }
    setorial.to_csv(paths["setorial"], index=False)
    municipal.to_csv(paths["municipal"], index=False)
    extremos.to_csv(paths["extremos"], index=False)
    _salvar_json(
        {
            "etapa": "demografia",
            "setores_rmr": int(len(setorial)),
            "municipios": {k: int(v) for k, v in setorial.groupby("COD_MUN").size().to_dict().items()},
            "limiares_heterogeneidade": limiares,
            "populacao_minima": populacao_minima,
        },
        paths["metadados"],
    )
    return paths


def executar_composicao_domestica(
    fonte_csv: str | Path,
    saida_regressao: str | Path,
    municipios: Mapping[str, str],
    *,
    demografia_setorial: pd.DataFrame | None = None,
) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "composicao_domestica")
    # O módulo define sua própria lista de variáveis-fonte; a leitura integral
    # desta fonte evita duplicar aqui um segundo dicionário operacional.
    bruto = ler_csv_ibge(fonte_csv)
    bruto["COD_MUN"] = bruto["CD_SETOR"].str[:7]
    bruto = bruto[bruto["COD_MUN"].isin(municipios)].copy()
    bruto["MUNICIPIO"] = bruto["COD_MUN"].map(municipios)
    setorial = calcular_indicadores(bruto)

    if demografia_setorial is not None:
        cols = ["CD_SETOR", "POP_TOTAL", "PCT_0_14", "PCT_60_MAIS"]
        disp = [c for c in cols if c in demografia_setorial.columns]
        setorial = setorial.merge(
            demografia_setorial[disp], on="CD_SETOR", how="left", validate="one_to_one"
        )

    municipal = resumo_municipal(setorial)
    paths = {
        "setorial": pasta / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_SETOR.csv",
        "municipal": pasta / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_MUNICIPIOS.csv",
        "missing": pasta / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_MISSING.csv",
        "metadados": pasta / "METADADOS_BLOCO2_COMPOSICAO_DOMESTICA.json",
    }
    setorial.to_csv(paths["setorial"], index=False)
    municipal.to_csv(paths["municipal"], index=False)

    missing = (
        setorial.groupby(["COD_MUN", "MUNICIPIO"], as_index=False)
        .agg(
            SETORES=("CD_SETOR", "size"),
            RESP_TOTAL_AUSENTE=("RESP_TOTAL", lambda x: int(x.isna().sum())),
            DOM_TIPO_DEN_AUSENTE=("DOM_TIPO_DEN", lambda x: int(x.isna().sum())),
        )
    )
    missing.to_csv(paths["missing"], index=False)
    _salvar_json(
        {"etapa": "composicao_domestica", "setores_rmr": int(len(setorial))},
        paths["metadados"],
    )
    return paths


def executar_renda(
    fonte_csv: str | Path,
    saida_regressao: str | Path,
    municipios: Mapping[str, str],
    *,
    responsaveis_minimos: int = 20,
) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "renda")
    bruto = ler_csv_ibge(fonte_csv, colunas=["CD_SETOR", "V06001", "V06002", "V06004"])
    setorial = preparar_renda_setorial(bruto, municipios)
    limiares = calcular_limiares_rmr(setorial, responsaveis_minimos=responsaveis_minimos)
    setorial = classificar_renda_relativa(setorial, limiares)
    municipal = resumir_renda_municipios(setorial, limiares, responsaveis_minimos=responsaveis_minimos)
    missing = auditar_ausencia_renda(setorial)

    paths = {
        "setorial": pasta / "RMR_CENSO2022_RENDA_RESPONSAVEL_SETOR.csv",
        "municipal": pasta / "RMR_CENSO2022_RENDA_RESPONSAVEL_MUNICIPIOS.csv",
        "missing": pasta / "RMR_CENSO2022_RENDA_RESPONSAVEL_MISSING.csv",
        "metadados": pasta / "METADADOS_BLOCO3_RENDA.json",
    }
    setorial.to_csv(paths["setorial"], index=False)
    municipal.to_csv(paths["municipal"], index=False)
    missing.to_csv(paths["missing"], index=False)
    _salvar_json(
        {
            "etapa": "renda",
            "setores_rmr": int(len(setorial)),
            "responsaveis_minimos": responsaveis_minimos,
            "limiares_rmr": asdict(limiares),
        },
        paths["metadados"],
    )
    return paths


def executar_cruzamentos(
    renda_setorial: pd.DataFrame,
    composicao_demografia: pd.DataFrame,
    saida_regressao: str | Path,
    *,
    responsaveis_minimos: int = 20,
    populacao_minima: int = 100,
    denominador_minimo: int = 20,
    quantil: float = 0.90,
) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "cruzamentos")
    lim_renda = calcular_limiares_rmr(renda_setorial, responsaveis_minimos=responsaveis_minimos)
    lim_cruza = calcular_limiares_cruzamentos(
        composicao_demografia,
        quantil=quantil,
        populacao_minima=populacao_minima,
        denominador_minimo=denominador_minimo,
    )
    setorial = cruzar_renda_composicao(
        renda_setorial,
        composicao_demografia,
        lim_renda,
        lim_cruza,
        responsaveis_minimos=responsaveis_minimos,
    )
    municipal = resumir_cruzamentos_municipios(setorial)
    paths = {
        "municipal": pasta / "RMR_CENSO2022_RENDA_CRUZAMENTOS_HABITACIONAIS.csv",
        "metadados": pasta / "METADADOS_CRUZAMENTOS_HABITACIONAIS.json",
    }
    municipal.to_csv(paths["municipal"], index=False)
    _salvar_json(
        {
            "etapa": "cruzamentos",
            "responsaveis_minimos": responsaveis_minimos,
            "populacao_minima": populacao_minima,
            "denominador_minimo": denominador_minimo,
            "quantil": quantil,
            "limiares_renda": asdict(lim_renda),
            "limiares_cruzamentos": asdict(lim_cruza),
        },
        paths["metadados"],
    )
    return paths
