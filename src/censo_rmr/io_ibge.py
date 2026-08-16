"""Leitura padronizada das fontes tabulares do IBGE."""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd


ALIASES_CHAVE_SETOR = ("CD_SETOR", "CD_setor", "CD_Setor", "cd_setor")


def normalizar_chave_setor(df: pd.DataFrame) -> pd.DataFrame:
    presentes = [c for c in ALIASES_CHAVE_SETOR if c in df.columns]
    if not presentes:
        raise ValueError(f"Chave setorial não encontrada. Aliases aceitos: {ALIASES_CHAVE_SETOR}")
    if "CD_SETOR" in presentes:
        out = df.copy()
    else:
        out = df.rename(columns={presentes[0]: "CD_SETOR"}).copy()
    out["CD_SETOR"] = out["CD_SETOR"].astype("string").str.strip()
    return out


def detectar_separador(caminho: str | Path, encoding: str = "utf-8-sig") -> str:
    with Path(caminho).open("r", encoding=encoding, errors="replace", newline="") as f:
        amostra = f.read(8192)
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=";,\t|")
        return dialeto.delimiter
    except csv.Error:
        return ";"


def ler_csv_ibge(
    caminho: str | Path,
    *,
    colunas: Iterable[str] | None = None,
    encoding: str = "utf-8-sig",
    separador: str | None = None,
) -> pd.DataFrame:
    """Lê CSV do IBGE preservando a chave territorial como texto."""
    caminho = Path(caminho)
    sep = separador or detectar_separador(caminho, encoding=encoding)
    cabecalho = pd.read_csv(caminho, sep=sep, encoding=encoding, nrows=0)
    nomes = list(cabecalho.columns)
    chave_original = next((c for c in ALIASES_CHAVE_SETOR if c in nomes), None)
    if chave_original is None:
        raise ValueError("Arquivo não contém chave de setor reconhecida.")

    usecols = None
    if colunas is not None:
        solicitadas = set(colunas)
        solicitadas.discard("CD_SETOR")
        usecols = [chave_original] + [c for c in nomes if c in solicitadas]
        ausentes = sorted(solicitadas - set(nomes))
        if ausentes:
            raise ValueError(f"Colunas solicitadas ausentes no CSV: {ausentes}")

    df = pd.read_csv(
        caminho,
        sep=sep,
        encoding=encoding,
        usecols=usecols,
        dtype={chave_original: "string"},
        low_memory=False,
    )
    return normalizar_chave_setor(df)


def listar_csvs_zip(caminho_zip: str | Path) -> list[str]:
    with zipfile.ZipFile(caminho_zip) as zf:
        return [n for n in zf.namelist() if not n.endswith("/") and n.lower().endswith(".csv")]


def extrair_csv_principal_zip(
    caminho_zip: str | Path,
    pasta_destino: str | Path,
    *,
    preferencia_nome: str | None = None,
) -> Path:
    """Extrai um CSV de um ZIP, exigindo seleção inequívoca."""
    caminho_zip = Path(caminho_zip)
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    csvs = listar_csvs_zip(caminho_zip)
    if not csvs:
        raise ValueError(f"Nenhum CSV encontrado em {caminho_zip}")

    escolhido: str | None = None
    if preferencia_nome:
        matches = [n for n in csvs if preferencia_nome.lower() in Path(n).name.lower()]
        if len(matches) == 1:
            escolhido = matches[0]
        elif len(matches) > 1:
            raise ValueError(f"Mais de um CSV corresponde à preferência {preferencia_nome!r}: {matches}")
    if escolhido is None:
        if len(csvs) != 1:
            raise ValueError(f"ZIP contém múltiplos CSVs; informe preferencia_nome. Encontrados: {csvs}")
        escolhido = csvs[0]

    alvo = (pasta_destino / Path(escolhido).name).resolve()
    raiz = pasta_destino.resolve()
    if raiz not in alvo.parents:
        raise ValueError(f"Caminho inseguro no ZIP: {escolhido}")
    with zipfile.ZipFile(caminho_zip) as zf, zf.open(escolhido) as origem, alvo.open("wb") as destino:
        destino.write(origem.read())
    return alvo
