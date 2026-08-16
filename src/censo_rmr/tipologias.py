"""Tipologias territoriais exploratórias e testes de estabilidade.

O módulo implementa os procedimentos documentados nas Fases 7 e 8. A escolha
substantiva de variáveis e de k permanece em configuração externa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class AvaliacaoK:
    k: int
    silhouette: float
    calinski_harabasz: float
    davies_bouldin: float
    ari_kmeans_ward: float
    pct_cluster_minimo: float
    pct_cluster_maximo: float


@dataclass
class SolucaoTipologia:
    indice: pd.Index
    variaveis: tuple[str, ...]
    scaler: StandardScaler
    kmeans: KMeans
    z: np.ndarray
    labels_kmeans: np.ndarray
    labels_ward: np.ndarray


def _matriz_completa(df: pd.DataFrame, variaveis: Sequence[str]) -> pd.DataFrame:
    faltantes = [v for v in variaveis if v not in df.columns]
    if faltantes:
        raise ValueError(f"Variáveis ausentes para tipologia: {faltantes}")
    x = df.loc[:, variaveis].apply(pd.to_numeric, errors="coerce")
    return x.dropna()


def ajustar_tipologia(
    df: pd.DataFrame,
    variaveis: Sequence[str],
    *,
    k: int = 4,
    n_init: int = 50,
    random_state: int = 42,
) -> SolucaoTipologia:
    x = _matriz_completa(df, variaveis)
    if len(x) <= k:
        raise ValueError("Número insuficiente de casos completos para clustering.")
    scaler = StandardScaler()
    z = scaler.fit_transform(x)
    km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state)
    lab_km = km.fit_predict(z)
    lab_ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(z)
    return SolucaoTipologia(
        indice=x.index,
        variaveis=tuple(variaveis),
        scaler=scaler,
        kmeans=km,
        z=z,
        labels_kmeans=lab_km,
        labels_ward=lab_ward,
    )


def avaliar_k(
    df: pd.DataFrame,
    variaveis: Sequence[str],
    ks: Sequence[int] = (4, 5, 6, 7, 8),
    *,
    n_init: int = 50,
    random_state: int = 42,
) -> pd.DataFrame:
    linhas = []
    for k in ks:
        s = ajustar_tipologia(df, variaveis, k=k, n_init=n_init, random_state=random_state)
        cont = np.bincount(s.labels_kmeans, minlength=k)
        pct = 100 * cont / cont.sum()
        linhas.append(
            AvaliacaoK(
                k=k,
                silhouette=float(silhouette_score(s.z, s.labels_kmeans)),
                calinski_harabasz=float(calinski_harabasz_score(s.z, s.labels_kmeans)),
                davies_bouldin=float(davies_bouldin_score(s.z, s.labels_kmeans)),
                ari_kmeans_ward=float(adjusted_rand_score(s.labels_kmeans, s.labels_ward)),
                pct_cluster_minimo=float(pct.min()),
                pct_cluster_maximo=float(pct.max()),
            ).__dict__
        )
    return pd.DataFrame(linhas)


def alinhar_rotulos(referencia: np.ndarray, candidato: np.ndarray) -> np.ndarray:
    """Alinha rótulos por máxima concordância usando algoritmo Húngaro."""
    ref_vals = np.unique(referencia)
    cand_vals = np.unique(candidato)
    tabela = np.zeros((len(ref_vals), len(cand_vals)), dtype=int)
    for i, r in enumerate(ref_vals):
        for j, c in enumerate(cand_vals):
            tabela[i, j] = int(((referencia == r) & (candidato == c)).sum())
    i, j = linear_sum_assignment(-tabela)
    mapa = {cand_vals[cj]: ref_vals[ri] for ri, cj in zip(i, j)}
    return np.array([mapa.get(x, x) for x in candidato])


def concordancia_pareada(referencia: np.ndarray, candidato: np.ndarray) -> float:
    alinhado = alinhar_rotulos(referencia, candidato)
    return float(100 * np.mean(referencia == alinhado))


def _labels_percentis(x: pd.DataFrame, k: int, n_init: int, random_state: int) -> np.ndarray:
    p = x.rank(method="average", pct=True).to_numpy(dtype=float)
    return KMeans(n_clusters=k, n_init=n_init, random_state=random_state).fit_predict(p)


def _labels_loo(
    x: pd.DataFrame,
    cols: Sequence[str],
    k: int,
    n_init: int,
    random_state: int,
) -> np.ndarray:
    z = StandardScaler().fit_transform(x.loc[:, cols])
    return KMeans(n_clusters=k, n_init=n_init, random_state=random_state).fit_predict(z)


def _bootstrap_labels(
    x: pd.DataFrame,
    *,
    k: int,
    n_init: int,
    random_state: int,
    repeticoes: int,
    fracao: float,
) -> list[np.ndarray]:
    rng = np.random.default_rng(random_state)
    n = len(x)
    m = max(k + 1, int(round(n * fracao)))
    resultados = []
    xv = x.to_numpy(dtype=float)
    for b in range(repeticoes):
        amostra = rng.choice(n, size=m, replace=False)
        scaler = StandardScaler().fit(xv[amostra])
        z_amostra = scaler.transform(xv[amostra])
        km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state + b + 1).fit(z_amostra)
        resultados.append(km.predict(scaler.transform(xv)))
    return resultados


def estabilidade_tipologia(
    df: pd.DataFrame,
    variaveis: Sequence[str],
    *,
    dominios: Mapping[str, Sequence[str]] | None = None,
    k: int = 4,
    n_init: int = 50,
    random_state: int = 42,
    bootstrap_repeticoes: int = 30,
    bootstrap_fracao: float = 0.80,
    robusta_min: float = 0.80,
    intermediaria_min: float = 0.60,
    fronteira_percentual: float = 0.20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Executa transformação, Ward, LOO variável/domínio e bootstrap.

    Retorna tabela por setor/caso completo e resumo dos cenários. Persistência
    estrutural exclui bootstrap, conforme a metodologia recuperada da Fase 8.
    """
    x = _matriz_completa(df, variaveis)
    base = ajustar_tipologia(x, variaveis, k=k, n_init=n_init, random_state=random_state)
    ref = base.labels_kmeans

    cenarios_estruturais: dict[str, np.ndarray] = {
        "ward": base.labels_ward,
        "transformacao_percentil": _labels_percentis(x, k, n_init, random_state),
    }
    for v in variaveis:
        cols = [c for c in variaveis if c != v]
        if len(cols) >= 2:
            cenarios_estruturais[f"loo_variavel:{v}"] = _labels_loo(x, cols, k, n_init, random_state)
    for nome, remover in (dominios or {}).items():
        cols = [c for c in variaveis if c not in set(remover)]
        if len(cols) >= 2:
            cenarios_estruturais[f"loo_dominio:{nome}"] = _labels_loo(x, cols, k, n_init, random_state)

    alinhados_estruturais = {nome: alinhar_rotulos(ref, lab) for nome, lab in cenarios_estruturais.items()}
    boots = _bootstrap_labels(
        x,
        k=k,
        n_init=n_init,
        random_state=random_state,
        repeticoes=bootstrap_repeticoes,
        fracao=bootstrap_fracao,
    )
    boots_alinhados = [alinhar_rotulos(ref, lab) for lab in boots]

    matriz_e = np.vstack([lab == ref for lab in alinhados_estruturais.values()])
    matriz_b = np.vstack([lab == ref for lab in boots_alinhados])
    persist_e = matriz_e.mean(axis=0) if len(matriz_e) else np.ones(len(ref))
    persist_b = matriz_b.mean(axis=0) if len(matriz_b) else np.ones(len(ref))
    persist_geral = np.vstack([matriz_e, matriz_b]).mean(axis=0)

    dist = base.kmeans.transform(base.z)
    ordenadas = np.sort(dist, axis=1)
    margem = ordenadas[:, 1] - ordenadas[:, 0]
    corte_fronteira = float(np.quantile(margem, fronteira_percentual))

    classificacao = np.where(
        persist_e >= robusta_min,
        "Robusta",
        np.where(persist_e >= intermediaria_min, "Intermediária", "Instável"),
    )
    setores = pd.DataFrame(
        {
            "CLUSTER_BASE": ref,
            "PERSISTENCIA_GERAL": persist_geral,
            "PERSISTENCIA_ESTRUTURAL": persist_e,
            "PERSISTENCIA_BOOTSTRAP": persist_b,
            "ROBUSTEZ": classificacao,
            "MARGEM_CENTROIDE": margem,
            "FRONTEIRA": margem <= corte_fronteira,
        },
        index=x.index,
    )

    linhas = []
    for nome, lab in cenarios_estruturais.items():
        alinhado = alinhados_estruturais[nome]
        linhas.append(
            {
                "CENARIO": nome,
                "ARI": float(adjusted_rand_score(ref, lab)),
                "CONCORDANCIA_PAREADA": float(100 * np.mean(ref == alinhado)),
                "TIPO": "estrutural",
            }
        )
    for i, (lab, alinhado) in enumerate(zip(boots, boots_alinhados), start=1):
        linhas.append(
            {
                "CENARIO": f"bootstrap_{i:02d}",
                "ARI": float(adjusted_rand_score(ref, lab)),
                "CONCORDANCIA_PAREADA": float(100 * np.mean(ref == alinhado)),
                "TIPO": "bootstrap",
            }
        )
    return setores, pd.DataFrame(linhas)
