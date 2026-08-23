"""Execucao em staging da densidade convencional e ajustada oficial."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Mapping

import geopandas as gpd
import pandas as pd

from .ancoras import carregar_ancoras, validar_ancoras
from .csv_padrao import salvar_csv_rmr
from .densidade import calcular_densidade
from .territorial import integrar_area_e_malha, normalizar_area_domiciliada_oficial, preparar_atributos_malha


def _ler_tabela(caminho: str | Path) -> pd.DataFrame:
    p = Path(caminho)
    ext = p.suffix.lower()
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    if ext == ".ods":
        return pd.read_excel(p, engine="odf")
    if ext == ".csv":
        return pd.read_csv(p, sep=None, engine="python", dtype="string")
    raise ValueError(f"Formato nao suportado para area domiciliada: {ext}")


def executar_densidade_oficial(
    populacao_setorial: pd.DataFrame,
    malha_gpkg: str | Path,
    area_domiciliada_arquivo: str | Path,
    mapa_colunas_area: dict[str, str],
    saida_staging: str | Path,
    municipios: Mapping[str, str],
    *,
    caminho_ancoras: str | Path | None = None,
    limiar_alta: float | None = None,
    tolerancia_densidade_oficial: float = 1e-6,
) -> dict[str, Path | dict]:
    """Calcula densidade usando AREA_DOM publicada pelo IBGE e audita a recomposicao."""
    pasta = Path(saida_staging) / "densidade_ajustada"
    pasta.mkdir(parents=True, exist_ok=True)

    pop = populacao_setorial[["CD_SETOR", "POP_TOTAL"]].copy()
    pop["CD_SETOR"] = pop["CD_SETOR"].astype("string").str.strip()
    pop["COD_MUN"] = pop["CD_SETOR"].str[:7]
    pop = pop[pop["COD_MUN"].isin(set(municipios))].drop(columns=["COD_MUN"])
    if pop["CD_SETOR"].duplicated().any():
        raise ValueError("Populacao setorial deve ter CD_SETOR unico")

    malha_bruta = gpd.read_file(malha_gpkg)
    malha, aud_malha = preparar_atributos_malha(malha_bruta)
    malha["COD_MUN"] = malha["CD_SETOR"].str[:7]
    malha = malha[malha["COD_MUN"].isin(set(municipios))].drop(columns=["COD_MUN"])

    area_bruta = _ler_tabela(area_domiciliada_arquivo)
    area = normalizar_area_domiciliada_oficial(area_bruta, mapa_colunas=mapa_colunas_area)
    integrado = integrar_area_e_malha(malha, area)
    integrado = integrado.merge(pop, on="CD_SETOR", how="left", validate="one_to_one")
    integrado = integrado.rename(columns={"AREA_KM2": "AREA_TOTAL"})

    calculado, meta = calcular_densidade(integrado, limiar_alta=limiar_alta)
    calculado["COD_MUN"] = calculado["CD_SETOR"].str[:7]
    calculado["MUNICIPIO"] = calculado["COD_MUN"].map(municipios)

    comparacao_oficial = {"disponivel": False, "ok": None}
    if "DENS_ADJ_OFICIAL" in calculado.columns:
        dif = (pd.to_numeric(calculado["DENS_ADJ"], errors="coerce") - pd.to_numeric(calculado["DENS_ADJ_OFICIAL"], errors="coerce")).abs()
        validos = dif.notna()
        comparacao_oficial = {
            "disponivel": True,
            "n_comparados": int(validos.sum()),
            "max_abs": float(dif[validos].max()) if validos.any() else None,
            "divergentes": int((dif[validos] > tolerancia_densidade_oficial).sum()),
            "tolerancia_abs": float(tolerancia_densidade_oficial),
        }
        comparacao_oficial["ok"] = comparacao_oficial["divergentes"] == 0

    ordem = [
        "CD_SETOR", "COD_MUN", "MUNICIPIO", "AREA_DOM", "AREA_TOTAL", "DENS_ADJ", "DENS_CONV",
        "PCT_AREA_DOM", "FATOR", "SETOR_FCU", "CD_FCU", "NM_FCU", "ALTA_DENS_ADJ", "DENS_ADJ_OFICIAL",
    ]
    ordem = [c for c in ordem if c in calculado.columns]
    setorial = calculado[ordem].copy()
    caminho_setorial = pasta / "RMR_CENSO2022_DENSIDADE_AJUSTADA_SETOR.csv"
    salvar_csv_rmr(setorial, caminho_setorial)

    relatorio_ancoras: dict = {"executado": False, "ok": None}
    if caminho_ancoras is not None and Path(caminho_ancoras).exists():
        specs = carregar_ancoras(caminho_ancoras)
        resultado = validar_ancoras(setorial, specs["densidade_ajustada"], conjunto="densidade_ajustada")
        relatorio_ancoras = {**asdict(resultado), "ok": resultado.ok, "executado": True}

    cobertura_area = calculado["_join_area_dom"].astype("string").value_counts(dropna=False).to_dict()
    auditoria = {
        "setores_saida": int(len(setorial)),
        "malha": asdict(aud_malha),
        "cobertura_area_domiciliada": {str(k): int(v) for k, v in cobertura_area.items()},
        "limiar_alta_densidade": meta.limiar_alta_densidade,
        "quantil_alta": meta.quantil,
        "comparacao_densidade_oficial": comparacao_oficial,
        "ancoras": relatorio_ancoras,
        "promocao_permitida": False,
    }
    caminho_auditoria = pasta / "AUDITORIA_DENSIDADE_AJUSTADA.json"
    caminho_auditoria.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"setorial": caminho_setorial, "auditoria": caminho_auditoria, "resultado": auditoria}
