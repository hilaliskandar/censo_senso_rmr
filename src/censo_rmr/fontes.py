"""Carregamento e preparação das fontes declaradas do pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .aquisicao import ArquivoFonte, baixar_com_cache
from .io_ibge import extrair_csv_principal_zip


@dataclass(frozen=True)
class FontePreparada:
    nome: str
    arquivo_zip: ArquivoFonte
    csv: Path


def carregar_manifesto_fontes(
    principal: str | Path,
    complemento_renda: str | Path | None = None,
) -> dict:
    with Path(principal).open("r", encoding="utf-8") as f:
        dados = yaml.safe_load(f) or {}
    fontes = dict(dados.get("fontes", {}))
    if complemento_renda and Path(complemento_renda).exists():
        with Path(complemento_renda).open("r", encoding="utf-8") as f:
            extra = yaml.safe_load(f) or {}
        if "renda_responsavel" in extra:
            fontes["renda_responsavel"] = extra["renda_responsavel"]
    return {**dados, "fontes": fontes}


def preparar_fonte_csv(
    nome: str,
    spec: dict,
    pasta_cache: str | Path,
    *,
    reprocessar: bool = False,
) -> FontePreparada:
    url = spec.get("url_csv_zip")
    if not url:
        raise ValueError(f"Fonte {nome!r} não possui URL CSV ZIP verificada.")
    zip_baixado = baixar_com_cache(url, pasta_cache, reprocessar=reprocessar)
    pasta_extraida = Path(pasta_cache) / "extraidos" / nome
    preferencia = spec.get("preferencia_csv")
    csv = extrair_csv_principal_zip(
        zip_baixado.caminho,
        pasta_extraida,
        preferencia_nome=preferencia,
    )
    return FontePreparada(nome=nome, arquivo_zip=zip_baixado, csv=csv)
