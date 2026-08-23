"""Execucao em staging do bloco de sexo, cor ou raca, alfabetizacao e FCU."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Mapping

import geopandas as gpd
import pandas as pd

from .ancoras import carregar_ancoras, validar_ancoras
from .csv_padrao import salvar_csv_rmr
from .equidade import calcular_equidade_alfabetizacao, padronizar_equidade_ibge
from .io_ibge import ler_csv_ibge
from .territorial import preparar_atributos_malha


VARS_ALFA = [
    "V00852", "V00853", "V00854", "V00855", "V00856", "V00857",
    "V00858", "V00859", "V00860", "V00861", "V00862", "V00863",
    "V00864", "V00865", "V00866", "V00867", "V00868", "V00869",
    "V00870", "V00871", "V00872", "V00873", "V00876", "V00877",
    "V00880", "V00881", "V00882", "V00883", "V00886", "V00887",
    "V00890", "V00891", "V00892", "V00893", "V00896", "V00897",
]


def _recortar_rmr(df: pd.DataFrame, municipios: Mapping[str, str]) -> pd.DataFrame:
    out = df.copy()
    out["CD_SETOR"] = out["CD_SETOR"].astype("string").str.strip()
    out["COD_MUN"] = out["CD_SETOR"].str[:7]
    return out[out["COD_MUN"].isin(set(municipios))].drop(columns=["COD_MUN"]).copy()


def executar_equidade_fcu(
    demografia_csv: str | Path,
    cor_raca_csv: str | Path,
    alfabetizacao_csv: str | Path,
    malha_gpkg: str | Path,
    saida_staging: str | Path,
    municipios: Mapping[str, str],
    *,
    caminho_ancoras: str | Path | None = None,
) -> dict[str, Path | dict]:
    """Reconstroi o bloco de equidade/FCU em staging e valida casos-ancora."""
    pasta = Path(saida_staging) / "equidade_fcu"
    pasta.mkdir(parents=True, exist_ok=True)

    demo = ler_csv_ibge(demografia_csv, colunas=["CD_SETOR", "V01006", "V01008"])
    raca = ler_csv_ibge(cor_raca_csv, colunas=["CD_SETOR", "V01317", "V01318", "V01319", "V01320", "V01321"])
    alfa = ler_csv_ibge(alfabetizacao_csv, colunas=["CD_SETOR", *VARS_ALFA])
    demo = _recortar_rmr(demo, municipios)
    raca = _recortar_rmr(raca, municipios)
    alfa = _recortar_rmr(alfa, municipios)

    malha_bruta = gpd.read_file(malha_gpkg)
    malha_tab, auditoria_malha = preparar_atributos_malha(malha_bruta)
    malha_tab = _recortar_rmr(malha_tab, municipios)

    pad = padronizar_equidade_ibge(demo, raca, alfa, malha_tab)
    out = calcular_equidade_alfabetizacao(pad)
    out["COD_MUN"] = out["CD_SETOR"].str[:7]
    out["MUNICIPIO"] = out["COD_MUN"].map(municipios)

    ordem = [
        "CD_SETOR", "COD_MUN", "MUNICIPIO", "SETOR_FCU", "CD_FCU", "NM_FCU",
        "POP_TOTAL", "PCT_FEMININO", "PCT_BRANCA", "PCT_PRETA", "PCT_PARDA",
        "PCT_PRETA_PARDA", "PCT_AMARELA", "PCT_INDIGENA", "TAXA_NAO_ALF_15_MAIS",
        "TAXA_NAO_ALF_MASC", "TAXA_NAO_ALF_FEM", "GAP_NAO_ALF_FEM_MASC",
        "TAXA_NAO_ALF_BRANCA", "TAXA_NAO_ALF_PRETA", "TAXA_NAO_ALF_PARDA",
        "TAXA_NAO_ALF_PRETA_PARDA", "GAP_NAO_ALF_PPI_BRANCA",
    ]
    ordem = [c for c in ordem if c in out.columns]
    setorial = out[ordem].copy()
    caminho_setorial = pasta / "RMR_CENSO2022_EQUIDADE_FCU_SETOR.csv"
    salvar_csv_rmr(setorial, caminho_setorial)

    relatorio_ancoras: dict = {"executado": False, "ok": None}
    if caminho_ancoras is not None and Path(caminho_ancoras).exists():
        specs = carregar_ancoras(caminho_ancoras)
        resultado = validar_ancoras(setorial, specs["equidade_fcu"], conjunto="equidade_fcu")
        relatorio_ancoras = {**asdict(resultado), "ok": resultado.ok, "executado": True}

    auditoria = {
        "setores_saida": int(len(setorial)),
        "setores_por_municipio": {str(k): int(v) for k, v in setorial.groupby("COD_MUN").size().to_dict().items()},
        "malha": asdict(auditoria_malha),
        "ancoras": relatorio_ancoras,
        "promocao_permitida": False,
    }
    caminho_auditoria = pasta / "AUDITORIA_EQUIDADE_FCU.json"
    caminho_auditoria.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"setorial": caminho_setorial, "auditoria": caminho_auditoria, "resultado": auditoria}
