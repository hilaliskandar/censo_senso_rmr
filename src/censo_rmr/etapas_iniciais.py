"""Executores dos primeiros blocos do pipeline em área de regressão.

Nenhuma função deste módulo escreve em `03_Tabelas_Indicadores`. Durante a
fase de validação, todos os produtos são gravados apenas em staging.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Mapping

import pandas as pd

from .composicao_domestica import calcular_indicadores, resumo_municipal
from .cruzamentos import calcular_limiares_cruzamentos, cruzar_renda_composicao, resumir_cruzamentos_municipios
from .csv_padrao import salvar_csv_rmr
from .demografia import calcular_limiares_heterogeneidade, preparar_demografia_setorial, resumir_demografia_municipios
from .io_ibge import ler_csv_ibge
from .renda import auditar_ausencia_renda, calcular_limiares_rmr, classificar_renda_relativa, preparar_renda_setorial, resumir_renda_municipios


def _pasta(saida: str | Path, etapa: str) -> Path:
    p = Path(saida) / etapa
    p.mkdir(parents=True, exist_ok=True)
    return p


def _salvar_json(obj: dict, caminho: Path) -> None:
    caminho.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def executar_demografia(fonte_csv: str | Path, saida_regressao: str | Path, municipios: Mapping[str, str], *, populacao_minima: int = 100) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "demografia")
    vars_demo = [f"V010{i:02d}" for i in range(6, 42)]
    bruto = ler_csv_ibge(fonte_csv, colunas=["CD_SETOR", *vars_demo])
    setorial = preparar_demografia_setorial(bruto, municipios)
    ordem = ["CD_SETOR", "COD_MUN", "MUNICIPIO", *vars_demo, "POP_TOTAL", "POP_0_14", "POP_15_29", "POP_30_59", "POP_60_MAIS", "POP_15_59", "PCT_0_14", "PCT_15_29", "PCT_30_59", "PCT_60_MAIS", "RAZAO_DEPENDENCIA", "INDICE_ENVELHECIMENTO", "RAZAO_SEXO_H_100M"]
    setorial = setorial[ordem]
    municipal = resumir_demografia_municipios(setorial)
    limiares = calcular_limiares_heterogeneidade(setorial, populacao_minima=populacao_minima)
    validos = setorial[setorial["POP_TOTAL"] >= populacao_minima].copy()
    validos["EXTREMO_JOVEM_P90"] = validos["PCT_0_14"] >= limiares["pct_0_14_p90"]
    validos["EXTREMO_IDOSO_P90"] = validos["PCT_60_MAIS"] >= limiares["pct_60_mais_p90"]
    extremos = validos[["CD_SETOR", "COD_MUN", "MUNICIPIO", "POP_TOTAL", "PCT_0_14", "PCT_60_MAIS", "INDICE_ENVELHECIMENTO", "EXTREMO_JOVEM_P90", "EXTREMO_IDOSO_P90"]].copy()
    paths = {"setorial": pasta / "RMR_CENSO2022_DEMOGRAFIA_SETOR.csv", "municipal": pasta / "RMR_CENSO2022_DEMOGRAFIA_MUNICIPIOS.csv", "extremos": pasta / "RMR_CENSO2022_DEMOGRAFIA_EXTREMOS_SETORIAIS.csv", "metadados": pasta / "METADADOS_BLOCO1_DEMOGRAFIA.json"}
    salvar_csv_rmr(setorial, paths["setorial"])
    salvar_csv_rmr(municipal, paths["municipal"])
    salvar_csv_rmr(extremos, paths["extremos"])
    _salvar_json({"etapa": "demografia", "setores_rmr": int(len(setorial)), "municipios": {k: int(v) for k, v in setorial.groupby("COD_MUN").size().to_dict().items()}, "limiares_heterogeneidade": limiares, "populacao_minima": populacao_minima}, paths["metadados"])
    return paths


def executar_composicao_domestica(fonte_csv: str | Path, saida_regressao: str | Path, municipios: Mapping[str, str], *, demografia_setorial: pd.DataFrame) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "composicao_domestica")
    bruto = ler_csv_ibge(fonte_csv)
    bruto["COD_MUN"] = bruto["CD_SETOR"].str[:7]
    bruto = bruto[bruto["COD_MUN"].isin(municipios)].copy()
    bruto["MUNICIPIO"] = bruto["COD_MUN"].map(municipios)
    indicadores = calcular_indicadores(bruto)
    demo_cols = ["CD_SETOR", "POP_TOTAL", "PCT_0_14", "PCT_60_MAIS", "INDICE_ENVELHECIMENTO", "RAZAO_DEPENDENCIA"]
    setorial = indicadores.merge(demografia_setorial[demo_cols], on="CD_SETOR", how="left", validate="one_to_one")
    ordem = ["CD_SETOR", "COD_MUN", "MUNICIPIO", "POP_TOTAL", "PCT_0_14", "PCT_60_MAIS", "INDICE_ENVELHECIMENTO", "RAZAO_DEPENDENCIA", "RESP_TOTAL", "RESP_HOMENS", "RESP_MULHERES", "PCT_RESP_FEM", "RESP_60_MAIS", "PCT_RESP_60_MAIS", "DOM_CONJ_DEN", "DOM_SEM_CONJUGE", "PCT_DOM_SEM_CONJUGE", "DOM_COMP_DEN", "DOM_RESP_SEM_CONJ_COM_FILHOS", "PCT_RESP_SEM_CONJ_COM_FILHOS", "DOM_TIPO_DEN", "DOM_UNIPESSOAL", "DOM_NUCLEAR", "DOM_ESTENDIDA", "DOM_COMPOSTA", "PCT_DOM_UNIPESSOAL", "PCT_DOM_NUCLEAR", "PCT_DOM_ESTENDIDA", "PCT_DOM_COMPOSTA", "DOM_UNIPESSOAL_RESP_H", "DOM_UNIPESSOAL_RESP_M", "PCT_UNIPESSOAL_RESP_FEM", "PCT_ESTENDIDA_RESP_FEM"]
    setorial_publicado = setorial[ordem].copy()
    municipal = resumo_municipal(indicadores)
    paths = {"setorial": pasta / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_SETOR.csv", "municipal": pasta / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_MUNICIPIOS.csv", "missing": pasta / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_MISSING.csv", "metadados": pasta / "METADADOS_BLOCO2_COMPOSICAO_DOMESTICA.json"}
    salvar_csv_rmr(setorial_publicado, paths["setorial"])
    salvar_csv_rmr(municipal, paths["municipal"])
    missing = indicadores.groupby(["COD_MUN", "MUNICIPIO"], as_index=False).agg(SETORES=("CD_SETOR", "size"), RESP_TOTAL_AUSENTE=("RESP_TOTAL", lambda x: int(x.isna().sum())), DOM_TIPO_DEN_AUSENTE=("DOM_TIPO_DEN", lambda x: int(x.isna().sum())))
    salvar_csv_rmr(missing, paths["missing"])
    _salvar_json({"etapa": "composicao_domestica", "setores_rmr": int(len(setorial_publicado))}, paths["metadados"])
    return paths


def executar_renda(fonte_csv: str | Path, saida_regressao: str | Path, municipios: Mapping[str, str], *, responsaveis_minimos: int = 20) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "renda")
    bruto = ler_csv_ibge(fonte_csv, colunas=["CD_SETOR", "V06001", "V06002", "V06004"])
    setorial = preparar_renda_setorial(bruto, municipios)
    limiares = calcular_limiares_rmr(setorial, responsaveis_minimos=responsaveis_minimos)
    setorial = classificar_renda_relativa(setorial, limiares)
    ordem = ["CD_SETOR", "COD_MUN", "MUNICIPIO", "RESP_DPPO", "MORADORES_DPPO", "RENDA_MEDIA_RESP_COM_RENDA", "MORADORES_POR_RESP_DPPO", "FAIXA_RELATIVA_RENDA_SETOR"]
    setorial = setorial[ordem]
    municipal = resumir_renda_municipios(setorial, limiares, responsaveis_minimos=responsaveis_minimos)
    missing = auditar_ausencia_renda(setorial)
    paths = {"setorial": pasta / "RMR_CENSO2022_RENDA_RESPONSAVEL_SETOR.csv", "municipal": pasta / "RMR_CENSO2022_RENDA_RESPONSAVEL_MUNICIPIOS.csv", "missing": pasta / "RMR_CENSO2022_RENDA_RESPONSAVEL_MISSING.csv", "metadados": pasta / "METADADOS_BLOCO3_RENDA.json"}
    salvar_csv_rmr(setorial, paths["setorial"])
    salvar_csv_rmr(municipal, paths["municipal"])
    salvar_csv_rmr(missing, paths["missing"])
    _salvar_json({"etapa": "renda", "setores_rmr": int(len(setorial)), "responsaveis_minimos": responsaveis_minimos, "limiares_rmr": asdict(limiares)}, paths["metadados"])
    return paths


def executar_cruzamentos(renda_setorial: pd.DataFrame, composicao_demografia: pd.DataFrame, saida_regressao: str | Path, *, responsaveis_minimos: int = 20, populacao_minima: int = 100, denominador_minimo: int = 20, quantil: float = 0.90) -> dict[str, Path]:
    pasta = _pasta(saida_regressao, "cruzamentos")
    lim_renda = calcular_limiares_rmr(renda_setorial, responsaveis_minimos=responsaveis_minimos)
    lim_cruza = calcular_limiares_cruzamentos(composicao_demografia, quantil=quantil, populacao_minima=populacao_minima, denominador_minimo=denominador_minimo)
    setorial = cruzar_renda_composicao(renda_setorial, composicao_demografia, lim_renda, lim_cruza, responsaveis_minimos=responsaveis_minimos)
    municipal = resumir_cruzamentos_municipios(setorial)
    paths = {"municipal": pasta / "RMR_CENSO2022_RENDA_CRUZAMENTOS_HABITACIONAIS.csv", "metadados": pasta / "METADADOS_CRUZAMENTOS_HABITACIONAIS.json"}
    salvar_csv_rmr(municipal, paths["municipal"])
    _salvar_json({"etapa": "cruzamentos", "responsaveis_minimos": responsaveis_minimos, "populacao_minima": populacao_minima, "denominador_minimo": denominador_minimo, "quantil": quantil, "limiares_renda": asdict(lim_renda), "limiares_cruzamentos": asdict(lim_cruza)}, paths["metadados"])
    return paths
