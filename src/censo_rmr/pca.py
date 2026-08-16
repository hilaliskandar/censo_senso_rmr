"""PCA por domínio, sem construção automática de índice único."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class ResultadoPCA:
    nome: str
    variaveis: tuple[str, ...]
    n_completos: int
    kmo: float
    autovalor_pc1: float
    variancia_explicada_pc1: float
    cargas: dict[str, float]


def kmo_global(df: pd.DataFrame) -> float:
    """Calcula KMO global a partir da matriz de correlações e correlações parciais."""
    x = df.to_numpy(dtype=float)
    if x.shape[1] < 2:
        raise ValueError("KMO requer ao menos duas variáveis.")
    r = np.corrcoef(x, rowvar=False)
    inv = np.linalg.pinv(r)
    d = np.sqrt(np.outer(np.diag(inv), np.diag(inv)))
    parcial = -inv / d
    np.fill_diagonal(parcial, 0.0)
    r2 = r**2
    np.fill_diagonal(r2, 0.0)
    p2 = parcial**2
    num = r2.sum()
    den = num + p2.sum()
    return float(num / den) if den else float("nan")


def calcular_pc1(
    df: pd.DataFrame,
    variaveis: Sequence[str],
    *,
    nome: str,
    orientacao_positiva: Sequence[str] | None = None,
) -> tuple[pd.Series, ResultadoPCA]:
    """Calcula PC1 em casos completos, devolvendo NaN nos demais setores.

    O sinal de uma componente é matematicamente arbitrário. Para tornar a
    reprodução estável, a orientação é fixada para que a correlação média do
    score com as variáveis declaradas em ``orientacao_positiva`` seja positiva.
    """
    variaveis = tuple(variaveis)
    faltantes = [v for v in variaveis if v not in df.columns]
    if faltantes:
        raise ValueError(f"Variáveis ausentes para PCA {nome}: {faltantes}")
    completo = df.loc[:, variaveis].apply(pd.to_numeric, errors="coerce").dropna()
    if len(completo) < 3:
        raise ValueError(f"PCA {nome} requer ao menos três casos completos.")

    scaler = StandardScaler()
    z = scaler.fit_transform(completo)
    pca = PCA(n_components=1)
    scores = pca.fit_transform(z)[:, 0]
    componentes = pca.components_[0].copy()

    anchors = tuple(orientacao_positiva or variaveis)
    idx = [variaveis.index(v) for v in anchors if v in variaveis]
    if not idx:
        raise ValueError(f"Nenhuma variável de orientação pertence à PCA {nome}.")
    if componentes[idx].mean() < 0:
        scores *= -1
        componentes *= -1

    serie = pd.Series(np.nan, index=df.index, name=nome, dtype=float)
    serie.loc[completo.index] = scores
    autovalor = float(pca.explained_variance_[0])
    cargas = componentes * np.sqrt(autovalor)
    relatorio = ResultadoPCA(
        nome=nome,
        variaveis=variaveis,
        n_completos=len(completo),
        kmo=kmo_global(completo),
        autovalor_pc1=autovalor,
        variancia_explicada_pc1=float(pca.explained_variance_ratio_[0]),
        cargas={v: float(c) for v, c in zip(variaveis, cargas)},
    )
    return serie, relatorio
