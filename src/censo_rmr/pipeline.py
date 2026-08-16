"""Orquestração reproduzível dos blocos do pipeline RMR em staging."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from .aquisicao import baixar_com_cache
from .configuracao import carregar_configuracao
from .contratos import carregar_produtos, verificar_produto
from .csv_padrao import ler_csv_rmr
from .etapas_densidade import executar_densidade_oficial
from .etapas_equidade import executar_equidade_fcu
from .etapas_iniciais import executar_composicao_domestica, executar_cruzamentos, executar_demografia, executar_renda
from .fontes import carregar_manifesto_fontes, preparar_fonte_csv
from .regressao import comparar_csvs


class ModoPipeline(str, Enum):
    AUDITAR = "AUDITAR"
    REPROCESSAR_EM_STAGING = "REPROCESSAR_EM_STAGING"


def carregar_contexto(repo: str | Path, drive_raiz: str | Path) -> dict:
    repo = Path(repo)
    drive_raiz = Path(drive_raiz)
    cfg = carregar_configuracao(repo / "config/config.yaml")
    fontes = carregar_manifesto_fontes(
        repo / "config/fontes.yaml",
        repo / "config/fonte_renda_2026.yaml",
    )
    produtos = carregar_produtos(repo / "config/produtos.yaml")
    return {"repo": repo, "drive": drive_raiz, "cfg": cfg, "fontes": fontes, "produtos": produtos}


def auditar_historico(ctx: dict) -> dict:
    drive = ctx["drive"]
    resultados = {}
    for nome in (
        "demografia", "composicao_domestica", "renda", "cruzamentos_habitacionais",
        "equidade_fcu", "densidade_ajustada",
    ):
        if nome not in ctx["produtos"].get("produtos", {}):
            continue
        v = verificar_produto(drive, ctx["produtos"], nome)
        resultados[nome] = {
            "ok": v.ok,
            "pasta": str(v.pasta),
            "presentes": list(v.presentes),
            "ausentes": list(v.ausentes),
        }
    return resultados


def _comparar_primeiros_blocos(drive: Path, staging: Path) -> dict:
    historico = drive / "03_Tabelas_Indicadores"
    pares = {
        "demografia_setorial": (
            staging / "demografia/RMR_CENSO2022_DEMOGRAFIA_SETOR.csv",
            historico / "RMR_CENSO2022_DEMOGRAFIA_SETOR.csv",
            "CD_SETOR",
        ),
        "demografia_municipal": (
            staging / "demografia/RMR_CENSO2022_DEMOGRAFIA_MUNICIPIOS.csv",
            historico / "RMR_CENSO2022_DEMOGRAFIA_MUNICIPIOS.csv",
            "COD_MUN",
        ),
        "composicao_setorial": (
            staging / "composicao_domestica/RMR_CENSO2022_COMPOSICAO_DOMESTICA_SETOR.csv",
            historico / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_SETOR.csv",
            "CD_SETOR",
        ),
        "composicao_municipal": (
            staging / "composicao_domestica/RMR_CENSO2022_COMPOSICAO_DOMESTICA_MUNICIPIOS.csv",
            historico / "RMR_CENSO2022_COMPOSICAO_DOMESTICA_MUNICIPIOS.csv",
            "COD_MUN",
        ),
        "renda_setorial": (
            staging / "renda/RMR_CENSO2022_RENDA_RESPONSAVEL_SETOR.csv",
            historico / "RMR_CENSO2022_RENDA_RESPONSAVEL_SETOR.csv",
            "CD_SETOR",
        ),
        "renda_municipal": (
            staging / "renda/RMR_CENSO2022_RENDA_RESPONSAVEL_MUNICIPIOS.csv",
            historico / "RMR_CENSO2022_RENDA_RESPONSAVEL_MUNICIPIOS.csv",
            "COD_MUN",
        ),
        "cruzamentos_municipal": (
            staging / "cruzamentos/RMR_CENSO2022_RENDA_CRUZAMENTOS_HABITACIONAIS.csv",
            historico / "RMR_CENSO2022_RENDA_CRUZAMENTOS_HABITACIONAIS.csv",
            "COD_MUN",
        ),
    }
    saida = {}
    for nome, (novo, ref, chave) in pares.items():
        if not novo.exists() or not ref.exists():
            saida[nome] = {"ok": False, "erro": "arquivo ausente", "novo": str(novo), "referencia": str(ref)}
            continue
        try:
            r = comparar_csvs(novo, ref, chave=chave)
            saida[nome] = r.como_dict()
        except Exception as exc:
            saida[nome] = {"ok": False, "erro": f"{type(exc).__name__}: {exc}"}
    return saida


def _fonte_manifesto(f) -> dict:
    return {
        "url": f.arquivo_zip.url,
        "arquivo": str(f.arquivo_zip.caminho),
        "sha256": f.arquivo_zip.sha256,
        "bytes": f.arquivo_zip.bytes,
        "reutilizado": f.arquivo_zip.reutilizado,
        "csv": str(f.csv),
    }


def _fonte_area_pronta(spec: dict) -> bool:
    url = str(spec.get("url_download_direto", ""))
    mapa = spec.get("mapa_colunas", {}) or {}
    return (
        url.startswith("http")
        and "pendente" not in url.lower()
        and {"CD_SETOR", "AREA_DOM"}.issubset(mapa)
    )


def reprocessar_primeiros_blocos(ctx: dict) -> dict:
    cfg = ctx["cfg"]
    drive = ctx["drive"]
    repo = ctx["repo"]
    pastas = cfg.dados["drive"]["pastas"]
    params = cfg.dados["parametros_operacionais"]
    cache = drive / pastas["cache_ibge"]
    staging = drive / pastas["regressao"] / "v1_upstream"
    staging.mkdir(parents=True, exist_ok=True)

    fontes_cfg = ctx["fontes"]["fontes"]
    demo_fonte = preparar_fonte_csv("demografia", fontes_cfg["demografia"], cache, reprocessar=False)
    comp_fonte = preparar_fonte_csv("composicao_domestica", fontes_cfg["composicao_domestica"], cache, reprocessar=False)
    renda_fonte = preparar_fonte_csv("renda_responsavel", fontes_cfg["renda_responsavel"], cache, reprocessar=False)

    demo_paths = executar_demografia(
        demo_fonte.csv,
        staging,
        cfg.municipios,
        populacao_minima=params["populacao_minima_setor_heterogeneidade"],
    )
    demo_df = ler_csv_rmr(demo_paths["setorial"])

    comp_paths = executar_composicao_domestica(
        comp_fonte.csv,
        staging,
        cfg.municipios,
        demografia_setorial=demo_df,
    )
    comp_df = ler_csv_rmr(comp_paths["setorial"])

    renda_paths = executar_renda(
        renda_fonte.csv,
        staging,
        cfg.municipios,
        responsaveis_minimos=params["responsaveis_minimos_renda"],
    )
    renda_df = ler_csv_rmr(renda_paths["setorial"])

    executar_cruzamentos(
        renda_df,
        comp_df,
        staging,
        responsaveis_minimos=params["responsaveis_minimos_renda"],
        populacao_minima=params["populacao_minima_setor_heterogeneidade"],
        denominador_minimo=params["denominador_minimo_composicao"],
    )

    raca_fonte = preparar_fonte_csv("cor_ou_raca", fontes_cfg["cor_ou_raca"], cache, reprocessar=False)
    alfa_fonte = preparar_fonte_csv("alfabetizacao", fontes_cfg["alfabetizacao"], cache, reprocessar=False)
    malha_spec = fontes_cfg["malha_setores_pe"]
    malha_arquivo = baixar_com_cache(malha_spec["url_gpkg"], cache, reprocessar=False)

    equidade = executar_equidade_fcu(
        demo_fonte.csv,
        raca_fonte.csv,
        alfa_fonte.csv,
        malha_arquivo.caminho,
        staging,
        cfg.municipios,
        caminho_ancoras=repo / "config/ancoras_regressao.yaml",
    )

    # Densidade e deliberadamente condicional: sem URL binaria e nomes de
    # colunas confirmados da publicacao oficial, registra bloqueio e nao infere.
    area_spec = fontes_cfg.get("area_domiciliada_densidade_ajustada", {})
    if _fonte_area_pronta(area_spec):
        area_arquivo = baixar_com_cache(area_spec["url_download_direto"], cache, reprocessar=False)
        densidade = executar_densidade_oficial(
            demo_df,
            malha_arquivo.caminho,
            area_arquivo.caminho,
            area_spec["mapa_colunas"],
            staging,
            cfg.municipios,
            caminho_ancoras=repo / "config/ancoras_regressao.yaml",
        )["resultado"]
        densidade["status"] = "executado_em_staging"
    else:
        densidade = {
            "status": "bloqueado_por_fonte",
            "motivo": "URL binaria e/ou mapa de colunas da tabela oficial de area domiciliada ainda nao confirmados",
            "promocao_permitida": False,
        }

    regressao = _comparar_primeiros_blocos(drive, staging)
    fontes_execucao = {
        "demografia": _fonte_manifesto(demo_fonte),
        "composicao_domestica": _fonte_manifesto(comp_fonte),
        "renda_responsavel": _fonte_manifesto(renda_fonte),
        "cor_ou_raca": _fonte_manifesto(raca_fonte),
        "alfabetizacao": _fonte_manifesto(alfa_fonte),
        "malha_setores_pe": {
            "url": malha_arquivo.url,
            "arquivo": str(malha_arquivo.caminho),
            "sha256": malha_arquivo.sha256,
            "bytes": malha_arquivo.bytes,
            "reutilizado": malha_arquivo.reutilizado,
        },
    }
    relatorio = {
        "staging": str(staging),
        "fontes": fontes_execucao,
        "regressao": regressao,
        "equidade_fcu": equidade["resultado"],
        "densidade_ajustada": densidade,
        "todos_produtos_centrais_equivalentes": all(v.get("ok", False) for v in regressao.values()),
        "ancoras_equidade_ok": bool(equidade["resultado"]["ancoras"].get("ok", False)),
        "promocao_permitida": False,
    }
    (staging / "RELATORIO_REGRESSAO.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return relatorio


def executar(modo: ModoPipeline | str, repo: str | Path, drive_raiz: str | Path) -> dict:
    modo = ModoPipeline(modo)
    ctx = carregar_contexto(repo, drive_raiz)
    if modo is ModoPipeline.AUDITAR:
        return {"modo": modo.value, "historico": auditar_historico(ctx)}
    if modo is ModoPipeline.REPROCESSAR_EM_STAGING:
        return {"modo": modo.value, **reprocessar_primeiros_blocos(ctx)}
    raise ValueError(modo)
