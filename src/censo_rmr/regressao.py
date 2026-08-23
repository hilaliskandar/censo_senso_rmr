"""Comparação reproduzível entre produtos novos e referências históricas."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .io_ibge import detectar_separador


@dataclass(frozen=True)
class ResultadoRegressao:
    chave: str
    linhas_novo: int
    linhas_referencia: int
    chaves_apenas_novo: int
    chaves_apenas_referencia: int
    colunas_comparadas: tuple[str, ...]
    colunas_ausentes_novo: tuple[str, ...]
    colunas_ausentes_referencia: tuple[str, ...]
    divergencias_numericas: int
    divergencias_textuais: int
    maior_erro_absoluto: float
    maior_erro_relativo: float

    @property
    def ok(self) -> bool:
        return (
            self.chaves_apenas_novo == 0
            and self.chaves_apenas_referencia == 0
            and not self.colunas_ausentes_novo
            and not self.colunas_ausentes_referencia
            and self.divergencias_numericas == 0
            and self.divergencias_textuais == 0
        )

    def como_dict(self) -> dict:
        return {**asdict(self), "ok": self.ok}


def _erro_relativo(a: np.ndarray, b: np.ndarray, atol: float) -> np.ndarray:
    den = np.maximum(np.abs(b), atol)
    return np.abs(a - b) / den


def comparar_dataframes(
    novo: pd.DataFrame,
    referencia: pd.DataFrame,
    *,
    chave: str = "CD_SETOR",
    colunas: Iterable[str] | None = None,
    atol: float = 1e-8,
    rtol: float = 1e-7,
) -> ResultadoRegressao:
    """Compara dois produtos pelo universo, esquema e valores."""
    for nome, df in (("novo", novo), ("referência", referencia)):
        if chave not in df.columns:
            raise ValueError(f"Chave {chave!r} ausente em {nome}.")
        if df[chave].duplicated().any():
            raise ValueError(f"Chave {chave!r} duplicada em {nome}.")

    n = novo.copy()
    r = referencia.copy()
    n[chave] = n[chave].astype("string")
    r[chave] = r[chave].astype("string")

    cn = set(n.columns) - {chave}
    cr = set(r.columns) - {chave}
    alvo = set(colunas) if colunas is not None else (cn & cr)
    aus_n = tuple(sorted(alvo - cn))
    aus_r = tuple(sorted(alvo - cr))
    comparaveis = tuple(sorted(alvo & cn & cr))

    kn = set(n[chave].dropna())
    kr = set(r[chave].dropna())
    apenas_n = kn - kr
    apenas_r = kr - kn

    comum = n[[chave, *comparaveis]].merge(
        r[[chave, *comparaveis]],
        on=chave,
        how="inner",
        suffixes=("__novo", "__ref"),
        validate="one_to_one",
    )

    div_num = 0
    div_txt = 0
    max_abs = 0.0
    max_rel = 0.0

    for c in comparaveis:
        a = comum[f"{c}__novo"]
        b = comum[f"{c}__ref"]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            av = a.to_numpy(dtype=float, na_value=np.nan)
            bv = b.to_numpy(dtype=float, na_value=np.nan)
            iguais = np.isclose(av, bv, rtol=rtol, atol=atol, equal_nan=True)
            div_num += int((~iguais).sum())
            validos = ~(np.isnan(av) | np.isnan(bv))
            if validos.any():
                abs_err = np.abs(av[validos] - bv[validos])
                rel_err = _erro_relativo(av[validos], bv[validos], atol)
                max_abs = max(max_abs, float(abs_err.max(initial=0.0)))
                max_rel = max(max_rel, float(rel_err.max(initial=0.0)))
        else:
            sa = a.astype("string").fillna("<NA>")
            sb = b.astype("string").fillna("<NA>")
            div_txt += int((sa != sb).sum())

    return ResultadoRegressao(
        chave=chave,
        linhas_novo=len(n),
        linhas_referencia=len(r),
        chaves_apenas_novo=len(apenas_n),
        chaves_apenas_referencia=len(apenas_r),
        colunas_comparadas=comparaveis,
        colunas_ausentes_novo=aus_n,
        colunas_ausentes_referencia=aus_r,
        divergencias_numericas=div_num,
        divergencias_textuais=div_txt,
        maior_erro_absoluto=max_abs,
        maior_erro_relativo=max_rel,
    )


def diagnosticar_regressao(
    novo: pd.DataFrame,
    referencia: pd.DataFrame,
    *,
    chave: str = "CD_SETOR",
    colunas: Iterable[str] | None = None,
    atol: float = 1e-8,
    rtol: float = 1e-7,
    max_amostras: int = 20,
) -> dict:
    """Produz diagnóstico compacto para uma regressão integral.

    A função complementa :func:`comparar_dataframes`: além dos totais, retorna
    amostras das chaves que aparecem apenas em uma das bases e das divergências
    por coluna. O objetivo é permitir que uma execução em staging seja
    investigável sem inspeção manual de milhares de linhas.
    """
    if max_amostras < 1:
        raise ValueError("max_amostras deve ser >= 1")

    resumo = comparar_dataframes(
        novo,
        referencia,
        chave=chave,
        colunas=colunas,
        atol=atol,
        rtol=rtol,
    )

    n = novo.copy()
    r = referencia.copy()
    n[chave] = n[chave].astype("string")
    r[chave] = r[chave].astype("string")
    kn = set(n[chave].dropna())
    kr = set(r[chave].dropna())

    comparaveis = list(resumo.colunas_comparadas)
    comum = n[[chave, *comparaveis]].merge(
        r[[chave, *comparaveis]],
        on=chave,
        how="inner",
        suffixes=("__novo", "__ref"),
        validate="one_to_one",
    )

    por_coluna: dict[str, dict] = {}
    for c in comparaveis:
        a = comum[f"{c}__novo"]
        b = comum[f"{c}__ref"]
        amostras: list[dict] = []

        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            av = a.to_numpy(dtype=float, na_value=np.nan)
            bv = b.to_numpy(dtype=float, na_value=np.nan)
            iguais = np.isclose(av, bv, rtol=rtol, atol=atol, equal_nan=True)
            pos = np.flatnonzero(~iguais)
            for i in pos[:max_amostras]:
                novo_v = av[i]
                ref_v = bv[i]
                amostras.append(
                    {
                        chave: str(comum.iloc[i][chave]),
                        "novo": None if np.isnan(novo_v) else float(novo_v),
                        "referencia": None if np.isnan(ref_v) else float(ref_v),
                        "erro_absoluto": None
                        if np.isnan(novo_v) or np.isnan(ref_v)
                        else float(abs(novo_v - ref_v)),
                    }
                )
            total_div = int(len(pos))
            tipo = "numerica"
        else:
            sa = a.astype("string").fillna("<NA>")
            sb = b.astype("string").fillna("<NA>")
            mask = (sa != sb).to_numpy()
            pos = np.flatnonzero(mask)
            for i in pos[:max_amostras]:
                amostras.append(
                    {
                        chave: str(comum.iloc[i][chave]),
                        "novo": None if pd.isna(a.iloc[i]) else str(a.iloc[i]),
                        "referencia": None if pd.isna(b.iloc[i]) else str(b.iloc[i]),
                    }
                )
            total_div = int(len(pos))
            tipo = "textual"

        if total_div:
            por_coluna[c] = {
                "tipo": tipo,
                "divergencias": total_div,
                "amostras": amostras,
            }

    return {
        "resumo": resumo.como_dict(),
        "amostra_chaves_apenas_novo": sorted(map(str, kn - kr))[:max_amostras],
        "amostra_chaves_apenas_referencia": sorted(map(str, kr - kn))[:max_amostras],
        "divergencias_por_coluna": por_coluna,
    }


def _ler_csv_auto(caminho: str | Path, chave: str) -> pd.DataFrame:
    caminho = Path(caminho)
    sep = detectar_separador(caminho)
    decimal = "," if sep == ";" else "."
    return pd.read_csv(
        caminho,
        sep=sep,
        decimal=decimal,
        encoding="utf-8-sig",
        dtype={chave: "string", "COD_MUN": "string"},
        low_memory=False,
    )


def comparar_csvs(
    novo: str | Path,
    referencia: str | Path,
    *,
    chave: str = "CD_SETOR",
    colunas: Iterable[str] | None = None,
    atol: float = 1e-8,
    rtol: float = 1e-7,
) -> ResultadoRegressao:
    a = _ler_csv_auto(novo, chave)
    b = _ler_csv_auto(referencia, chave)
    return comparar_dataframes(a, b, chave=chave, colunas=colunas, atol=atol, rtol=rtol)
