"""Convenções de CSV usadas nos produtos históricos da RMR."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def salvar_csv_rmr(df: pd.DataFrame, caminho: str | Path) -> Path:
    """Grava CSV compatível com os produtos históricos: ;, decimal vírgula, BOM."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        caminho,
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )
    return caminho


def ler_csv_rmr(caminho: str | Path) -> pd.DataFrame:
    return pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"CD_SETOR": "string", "COD_MUN": "string"},
        low_memory=False,
    )
