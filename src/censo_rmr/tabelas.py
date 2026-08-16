"""Camada editorial para tabelas do diagnóstico.

Este módulo não calcula indicadores analíticos. Ele valida a presença das
colunas declaradas, seleciona/ordena campos e exporta a mesma tabela em CSV,
XLSX e metadados JSON para rastreabilidade.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import pandas as pd

from .csv_padrao import salvar_csv_rmr


def preparar_tabela(df: pd.DataFrame, spec: Mapping) -> pd.DataFrame:
    colunas = list(spec.get("colunas", []))
    faltantes = [c for c in colunas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Tabela {spec.get('id')} sem colunas obrigatórias: {faltantes}")
    out = df.loc[:, colunas].copy()
    for chave in ("CD_SETOR", "COD_MUN"):
        if chave in out.columns:
            out[chave] = out[chave].astype("string")
    return out


def salvar_xlsx(df: pd.DataFrame, caminho: str | Path, *, aba: str = "Tabela") -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=aba)
        ws = writer.book[aba]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for coluna in ws.columns:
            letra = coluna[0].column_letter
            largura = min(max(len(str(c.value)) if c.value is not None else 0 for c in coluna) + 2, 45)
            ws.column_dimensions[letra].width = max(largura, 10)
    return caminho


def exportar_tabela(
    df: pd.DataFrame,
    spec: Mapping,
    pasta_saida: str | Path,
) -> dict[str, str]:
    tabela = preparar_tabela(df, spec)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    base = str(spec.get("id", "tabela")).upper()
    csv_path = pasta / f"{base}.csv"
    xlsx_path = pasta / f"{base}.xlsx"
    meta_path = pasta / f"{base}.json"
    salvar_csv_rmr(tabela, csv_path)
    salvar_xlsx(tabela, xlsx_path, aba="Tabela")
    metadados = {
        "id": spec.get("id"),
        "titulo": spec.get("titulo"),
        "origem": spec.get("origem"),
        "colunas": list(tabela.columns),
        "linhas": len(tabela),
        "unidade": spec.get("unidade"),
        "fonte": spec.get("fonte"),
        "nota": spec.get("nota"),
        "arquivos": {"csv": str(csv_path), "xlsx": str(xlsx_path)},
    }
    meta_path.write_text(json.dumps(metadados, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"csv": str(csv_path), "xlsx": str(xlsx_path), "metadados": str(meta_path)}
