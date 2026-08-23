"""Validação de casos-âncora contra produtos históricos da RMR."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


@dataclass(frozen=True)
class ResultadoAncora:
    conjunto: str
    total_campos: int
    campos_ok: int
    campos_divergentes: int
    setores_ausentes: tuple[str, ...]
    divergencias: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.campos_divergentes == 0 and not self.setores_ausentes


def carregar_ancoras(caminho: str | Path) -> dict:
    with Path(caminho).open("r", encoding="utf-8") as f:
        dados = yaml.safe_load(f) or {}
    if not isinstance(dados, dict):
        raise ValueError("Arquivo de âncoras inválido.")
    return dados


def validar_ancoras(df: pd.DataFrame, spec: dict, *, conjunto: str = "ancoras") -> ResultadoAncora:
    chave = spec.get("chave", "CD_SETOR")
    if chave not in df.columns:
        raise ValueError(f"Chave {chave!r} ausente no DataFrame.")

    tolerancia = float(spec.get("tolerancia_abs", 1e-9))
    casos = spec.get("casos", {})
    idx = df.copy()
    idx[chave] = idx[chave].astype("string").str.strip()
    idx = idx.set_index(chave, drop=False)

    setores_ausentes: list[str] = []
    divergencias: list[str] = []
    total = 0
    ok = 0

    for setor, esperado_campos in casos.items():
        setor = str(setor)
        if setor not in idx.index:
            setores_ausentes.append(setor)
            total += len(esperado_campos)
            continue
        linha = idx.loc[setor]
        if isinstance(linha, pd.DataFrame):
            divergencias.append(f"{setor}: chave duplicada")
            total += len(esperado_campos)
            continue

        for campo, esperado in esperado_campos.items():
            total += 1
            if campo not in linha.index:
                divergencias.append(f"{setor}/{campo}: campo ausente")
                continue
            observado = linha[campo]
            if esperado is None:
                passou = pd.isna(observado)
            elif isinstance(esperado, bool):
                passou = bool(observado) is esperado
            elif isinstance(esperado, (int, float)) and not isinstance(esperado, bool):
                try:
                    passou = bool(np.isclose(float(observado), float(esperado), rtol=0.0, atol=tolerancia, equal_nan=False))
                except (TypeError, ValueError):
                    passou = False
            else:
                passou = str(observado) == str(esperado)

            if passou:
                ok += 1
            else:
                divergencias.append(f"{setor}/{campo}: observado={observado!r}; esperado={esperado!r}")

    return ResultadoAncora(
        conjunto=conjunto,
        total_campos=total,
        campos_ok=ok,
        campos_divergentes=total - ok,
        setores_ausentes=tuple(setores_ausentes),
        divergencias=tuple(divergencias),
    )
