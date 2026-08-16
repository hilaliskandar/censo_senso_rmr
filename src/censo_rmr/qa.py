from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import pandas as pd


@dataclass
class ResultadoQA:
    teste: str
    passou: bool
    detalhe: str
    severidade: str = "erro"

    def as_dict(self) -> dict:
        return asdict(self)


def qa_chave_unica(df: pd.DataFrame, chave: str) -> ResultadoQA:
    duplicados = int(df[chave].duplicated().sum())
    return ResultadoQA(
        teste=f"chave_unica:{chave}",
        passou=duplicados == 0,
        detalhe=f"duplicados={duplicados}",
    )


def qa_nao_nulo(df: pd.DataFrame, coluna: str) -> ResultadoQA:
    ausentes = int(df[coluna].isna().sum())
    return ResultadoQA(
        teste=f"nao_nulo:{coluna}",
        passou=ausentes == 0,
        detalhe=f"ausentes={ausentes}",
    )


def qa_intervalo(
    df: pd.DataFrame, coluna: str, minimo: float, maximo: float
) -> ResultadoQA:
    serie = pd.to_numeric(df[coluna], errors="coerce").dropna()
    invalidos = int(((serie < minimo) | (serie > maximo)).sum())
    return ResultadoQA(
        teste=f"intervalo:{coluna}",
        passou=invalidos == 0,
        detalhe=f"fora_intervalo={invalidos}; intervalo=[{minimo}, {maximo}]",
    )


def qa_cobertura_join(
    total_esquerda: int, total_resultado: int, tolerancia_perda: float = 0.0
) -> ResultadoQA:
    if total_esquerda == 0:
        return ResultadoQA(
            teste="cobertura_join",
            passou=False,
            detalhe="universo esquerdo vazio",
        )
    perda = max(total_esquerda - total_resultado, 0) / total_esquerda
    return ResultadoQA(
        teste="cobertura_join",
        passou=perda <= tolerancia_perda,
        detalhe=f"perda={perda:.6f}; tolerancia={tolerancia_perda:.6f}",
    )


def consolidar_resultados(resultados: Iterable[ResultadoQA]) -> pd.DataFrame:
    return pd.DataFrame([r.as_dict() for r in resultados])


def interromper_se_critico(resultados: Iterable[ResultadoQA]) -> None:
    falhas = [r for r in resultados if not r.passou and r.severidade == "erro"]
    if falhas:
        resumo = "; ".join(f"{r.teste}: {r.detalhe}" for r in falhas)
        raise RuntimeError(f"Gate de QA reprovado: {resumo}")
