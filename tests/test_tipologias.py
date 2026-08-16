import numpy as np
import pandas as pd

from censo_rmr.tipologias import ajustar_tipologia, alinhar_rotulos, avaliar_k, estabilidade_tipologia


def _dados():
    rng = np.random.default_rng(7)
    blocos = []
    for centro in (-3.0, -1.0, 1.0, 3.0):
        blocos.append(rng.normal(loc=centro, scale=0.25, size=(30, 4)))
    x = np.vstack(blocos)
    return pd.DataFrame(x, columns=["a", "b", "c", "d"])


def test_ajuste_tipologia_k4():
    s = ajustar_tipologia(_dados(), ["a", "b", "c", "d"], k=4, random_state=42)
    assert len(s.labels_kmeans) == 120
    assert len(np.unique(s.labels_kmeans)) == 4


def test_alinhamento_remove_permutacao_de_rotulos():
    ref = np.array([0, 0, 1, 1, 2, 2])
    cand = np.array([2, 2, 0, 0, 1, 1])
    assert np.array_equal(alinhar_rotulos(ref, cand), ref)


def test_avaliacao_k_retorna_metricas():
    r = avaliar_k(_dados(), ["a", "b", "c", "d"], ks=[4, 5], random_state=42)
    assert list(r["k"]) == [4, 5]
    assert set(["silhouette", "calinski_harabasz", "davies_bouldin", "ari_kmeans_ward"]).issubset(r.columns)


def test_estabilidade_produz_persistencias_e_cenarios():
    setores, cenarios = estabilidade_tipologia(
        _dados(),
        ["a", "b", "c", "d"],
        dominios={"ab": ["a", "b"], "cd": ["c", "d"]},
        k=4,
        bootstrap_repeticoes=5,
        random_state=42,
    )
    assert len(setores) == 120
    assert setores["PERSISTENCIA_ESTRUTURAL"].between(0, 1).all()
    assert setores["PERSISTENCIA_BOOTSTRAP"].between(0, 1).all()
    assert set(setores["ROBUSTEZ"]).issubset({"Robusta", "Intermediária", "Instável"})
    assert (cenarios["TIPO"] == "bootstrap").sum() == 5
