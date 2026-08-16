"""Orquestração reproduzível dos blocos iniciais do pipeline RMR."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from .configuracao import carregar_configuracao
from .contratos import carregar_produtos, verificar_produto
from .csv_padrao import ler_csv_rmr
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
    for nome in ("demografia", "composicao_domestica", "renda", "cruzamentos_habitacionais"):
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


def reprocessar_primeiros_blocos(ctx: dict) -> dict:
    cfg = ctx["cfg"]
    drive = ctx["drive"]
    pastas = cfg.dados["drive"]["pastas"]
    params = cfg.dados["parametros_operacionais"]
    cache = drive / pastas["cache_ibge"]
    staging = drive / pastas["regressao"] / "v0_primeiros_blocos"
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

    cruza_paths = executar_cruzamentos(
        renda_df,
        comp_df,
        staging,
        responsaveis_minimos=params["responsaveis_minimos_renda"],
        populacao_minima=params["populacao_minima_setor_heterogeneidade"],
        denominador_minimo=params["denominador_minimo_composicao"],
    )

    regressao = _comparar_primeiros_blocos(drive, staging)
    fontes_execucao = {
        f.nome: {
            "url": f.arquivo_zip.url,
            "arquivo": str(f.arquivo_zip.caminho),
            "sha256": f.arquivo_zip.sha256,
            "bytes": f.arquivo_zip.bytes,
            "reutilizado": f.arquivo_zip.reutilizado,
            "csv": str(f.csv),
        }
        for f in (demo_fonte, comp_fonte, renda_fonte)
    }
    relatorio = {
        "staging": str(staging),
        "fontes": fontes_execucao,
        "regressao": regressao,
        "todos_produtos_centrais_equivalentes": all(v.get("ok", False) for v in regressao.values()),
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
