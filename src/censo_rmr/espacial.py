"""Autocorrelação espacial, LISA e estabilidade entre matrizes de vizinhança."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import geopandas as gpd
import numpy as np
import pandas as pd
from esda.moran import Moran, Moran_BV, Moran_Local, Moran_Local_BV
from libpysal.weights import KNN, Queen
from statsmodels.stats.multitest import multipletests


CLASSE_Q = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}


@dataclass(frozen=True)
class MoranGlobalResultado:
    variavel: str
    n: int
    isolados: int
    moran_i: float
    p_permutacao: float
    sim_media: float
    sim_dp: float


def dissolver_chave(gdf: gpd.GeoDataFrame, chave: str = "CD_SETOR") -> gpd.GeoDataFrame:
    """Garante uma geometria por chave antes da construção dos pesos."""
    if chave not in gdf.columns:
        raise ValueError(f"Chave {chave} ausente na base espacial.")
    if not gdf[chave].duplicated().any():
        return gdf.copy()
    atributos = [c for c in gdf.columns if c not in {"geometry", chave}]
    # Conserva o primeiro valor não espacial por chave; atributos analíticos
    # devem ser agregados antes desta função quando houver divergência real.
    base = gdf[[chave, "geometry"]].dissolve(by=chave, as_index=False)
    if atributos:
        attrs = gdf.groupby(chave, as_index=False)[atributos].first()
        base = base.merge(attrs, on=chave, how="left", validate="one_to_one")
    return gpd.GeoDataFrame(base, geometry="geometry", crs=gdf.crs)


def _pesos(
    gdf: gpd.GeoDataFrame,
    tipo: Literal["queen", "knn"] = "queen",
    *,
    k: int = 6,
    simetrizar: bool = True,
):
    if tipo == "queen":
        w = Queen.from_dataframe(gdf, use_index=True)
    elif tipo == "knn":
        w = KNN.from_dataframe(gdf, k=k, use_index=True)
        if simetrizar:
            w = w.symmetrize()
    else:
        raise ValueError(f"Tipo de peso desconhecido: {tipo}")
    w.transform = "R"
    return w


def _base_valida(gdf: gpd.GeoDataFrame, colunas: list[str], chave: str) -> gpd.GeoDataFrame:
    faltantes = [c for c in [chave, *colunas, "geometry"] if c not in gdf.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes para análise espacial: {faltantes}")
    out = gdf[[chave, *colunas, "geometry"]].copy()
    for c in colunas:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=colunas + ["geometry"]).copy()
    out = dissolver_chave(out, chave=chave).set_index(chave, drop=False)
    return out


def moran_global(
    gdf: gpd.GeoDataFrame,
    variavel: str,
    *,
    chave: str = "CD_SETOR",
    tipo_peso: Literal["queen", "knn"] = "queen",
    k: int = 6,
    permutacoes: int = 999,
    seed: int | None = 42,
) -> MoranGlobalResultado:
    base = _base_valida(gdf, [variavel], chave)
    w = _pesos(base, tipo_peso, k=k)
    if seed is not None:
        np.random.seed(seed)
    m = Moran(base[variavel].to_numpy(), w, permutations=permutacoes, two_tailed=True)
    isolados = sum(len(v) == 0 for v in w.neighbors.values())
    return MoranGlobalResultado(
        variavel=variavel,
        n=len(base),
        isolados=int(isolados),
        moran_i=float(m.I),
        p_permutacao=float(m.p_sim),
        sim_media=float(m.EI_sim),
        sim_dp=float(m.seI_sim),
    )


def _classes_local(q: np.ndarray, p: np.ndarray, alpha: float) -> np.ndarray:
    return np.array([CLASSE_Q.get(int(qi), "NS") if pi < alpha else "NS" for qi, pi in zip(q, p)], dtype=object)


def lisa_local(
    gdf: gpd.GeoDataFrame,
    variavel: str,
    *,
    chave: str = "CD_SETOR",
    tipo_peso: Literal["queen", "knn"] = "queen",
    k: int = 6,
    permutacoes: int = 999,
    alpha: float = 0.05,
    correcao: Literal["nenhuma", "fdr_bh"] = "fdr_bh",
    seed: int = 42,
) -> pd.DataFrame:
    base = _base_valida(gdf, [variavel], chave)
    w = _pesos(base, tipo_peso, k=k)
    ml = Moran_Local(
        base[variavel].to_numpy(),
        w,
        permutations=permutacoes,
        seed=seed,
        n_jobs=1,
        keep_simulations=False,
    )
    p_bruto = np.asarray(ml.p_sim, dtype=float)
    if correcao == "fdr_bh":
        rejeita, p_aj, _, _ = multipletests(p_bruto, alpha=alpha, method="fdr_bh")
        p_usado = p_aj
    elif correcao == "nenhuma":
        rejeita = p_bruto < alpha
        p_aj = np.full(len(p_bruto), np.nan)
        p_usado = p_bruto
    else:
        raise ValueError(correcao)
    classes = np.array([CLASSE_Q.get(int(q), "NS") if ok else "NS" for q, ok in zip(ml.q, rejeita)], dtype=object)
    return pd.DataFrame(
        {
            chave: base[chave].astype("string").to_numpy(),
            "VALOR": base[variavel].to_numpy(),
            "LISA_I": np.asarray(ml.Is, dtype=float),
            "P_BRUTO": p_bruto,
            "P_FDR": p_aj,
            "SIGNIFICATIVO": rejeita,
            "CLASSE_LISA": classes,
            "PESO": tipo_peso,
        }
    )


def estabilidade_lisa(
    queen: pd.DataFrame,
    knn: pd.DataFrame,
    *,
    chave: str = "CD_SETOR",
) -> tuple[pd.DataFrame, dict]:
    a = queen[[chave, "SIGNIFICATIVO", "CLASSE_LISA"]].rename(columns={"SIGNIFICATIVO": "SIG_Q", "CLASSE_LISA": "CLASSE_Q"})
    b = knn[[chave, "SIGNIFICATIVO", "CLASSE_LISA"]].rename(columns={"SIGNIFICATIVO": "SIG_K", "CLASSE_LISA": "CLASSE_K"})
    m = a.merge(b, on=chave, how="outer", validate="one_to_one")
    m["MESMA_CLASSE"] = m["CLASSE_Q"].eq(m["CLASSE_K"])
    m["CLUSTER_ESTAVEL_SIGNIFICATIVO"] = m["SIG_Q"].fillna(False) & m["SIG_K"].fillna(False) & m["MESMA_CLASSE"] & m["CLASSE_Q"].ne("NS")
    sq = set(m.loc[m["SIG_Q"].fillna(False), chave].dropna())
    sk = set(m.loc[m["SIG_K"].fillna(False), chave].dropna())
    uniao = sq | sk
    resumo = {
        "n_queen_significativos": len(sq),
        "n_knn_significativos": len(sk),
        "n_intersecao_significativos": len(sq & sk),
        "jaccard_significativos": len(sq & sk) / len(uniao) if uniao else 1.0,
        "n_cluster_estavel_significativo": int(m["CLUSTER_ESTAVEL_SIGNIFICATIVO"].sum()),
    }
    return m, resumo


def moran_bivariado_global(
    gdf: gpd.GeoDataFrame,
    x: str,
    y: str,
    *,
    chave: str = "CD_SETOR",
    tipo_peso: Literal["queen", "knn"] = "queen",
    k: int = 6,
    permutacoes: int = 999,
) -> dict:
    base = _base_valida(gdf, [x, y], chave)
    w = _pesos(base, tipo_peso, k=k)
    m = Moran_BV(base[x].to_numpy(), base[y].to_numpy(), w, permutations=permutacoes)
    return {
        "X_FOCAL": x,
        "Y_VIZINHANCA": y,
        "N": len(base),
        "ISOLADOS": int(sum(len(v) == 0 for v in w.neighbors.values())),
        "MORAN_BIVAR_I": float(m.I),
        "P_PERMUTACAO": float(m.p_sim),
        "SIM_MEDIA": float(m.EI_sim),
        "SIM_DP": float(m.seI_sim),
    }


def lisa_bivariado(
    gdf: gpd.GeoDataFrame,
    x: str,
    y: str,
    *,
    chave: str = "CD_SETOR",
    tipo_peso: Literal["queen", "knn"] = "queen",
    k: int = 6,
    permutacoes: int = 999,
    alpha: float = 0.05,
    correcao: Literal["nenhuma", "fdr_bh"] = "fdr_bh",
    seed: int = 42,
) -> pd.DataFrame:
    base = _base_valida(gdf, [x, y], chave)
    w = _pesos(base, tipo_peso, k=k)
    ml = Moran_Local_BV(
        base[x].to_numpy(),
        base[y].to_numpy(),
        w,
        permutations=permutacoes,
        seed=seed,
        n_jobs=1,
        keep_simulations=False,
    )
    p_bruto = np.asarray(ml.p_sim, dtype=float)
    if correcao == "fdr_bh":
        rejeita, p_aj, _, _ = multipletests(p_bruto, alpha=alpha, method="fdr_bh")
    elif correcao == "nenhuma":
        rejeita = p_bruto < alpha
        p_aj = np.full(len(p_bruto), np.nan)
    else:
        raise ValueError(correcao)
    classes = np.array([CLASSE_Q.get(int(q), "NS") if ok else "NS" for q, ok in zip(ml.q, rejeita)], dtype=object)
    return pd.DataFrame(
        {
            chave: base[chave].astype("string").to_numpy(),
            "X": base[x].to_numpy(),
            "Y": base[y].to_numpy(),
            "LISA_BV_I": np.asarray(ml.Is, dtype=float),
            "P_BRUTO": p_bruto,
            "P_FDR": p_aj,
            "SIGNIFICATIVO": rejeita,
            "CLASSE_LISA_BV": classes,
            "PESO": tipo_peso,
        }
    )
