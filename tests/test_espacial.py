import geopandas as gpd
import numpy as np
from shapely.geometry import box

from censo_rmr.espacial import estabilidade_lisa, lisa_local, moran_global


def _grade():
    geoms = []
    valores = []
    codigos = []
    n = 0
    for i in range(3):
        for j in range(3):
            n += 1
            geoms.append(box(i, j, i + 1, j + 1))
            valores.append(float(i + j))
            codigos.append(f"{n:015d}")
    return gpd.GeoDataFrame({"CD_SETOR": codigos, "x": valores}, geometry=geoms, crs="EPSG:3857")


def test_moran_global_retorna_universo():
    gdf = _grade()
    r = moran_global(gdf, "x", permutacoes=19, seed=7)
    assert r.n == 9
    assert np.isfinite(r.moran_i)


def test_lisa_queen_e_knn_podem_ser_comparados():
    gdf = _grade()
    q = lisa_local(gdf, "x", tipo_peso="queen", permutacoes=19, correcao="nenhuma", seed=7)
    k = lisa_local(gdf, "x", tipo_peso="knn", k=3, permutacoes=19, correcao="nenhuma", seed=7)
    est, resumo = estabilidade_lisa(q, k)
    assert len(est) == 9
    assert 0 <= resumo["jaccard_significativos"] <= 1


def test_lisa_fdr_expoe_p_ajustado():
    gdf = _grade()
    q = lisa_local(gdf, "x", permutacoes=19, correcao="fdr_bh", seed=7)
    assert "P_FDR" in q.columns
    assert q["P_FDR"].notna().all()
