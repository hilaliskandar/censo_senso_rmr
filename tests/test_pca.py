import numpy as np
import pandas as pd

from censo_rmr.pca import calcular_pc1, kmo_global


def test_pc1_orientacao_positiva_e_nan_fora_dos_casos_completos():
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5, np.nan],
        "b": [2, 4, 6, 8, 10, 12],
        "c": [1.1, 2.1, 2.9, 4.2, 5.1, 6.0],
    })
    score, rel = calcular_pc1(df, ["a", "b", "c"], nome="pc", orientacao_positiva=["a", "b", "c"])
    assert score.notna().sum() == 5
    assert pd.isna(score.iloc[-1])
    assert rel.variancia_explicada_pc1 > 0.95
    assert all(v > 0 for v in rel.cargas.values())


def test_kmo_fica_entre_zero_e_um():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 3, 5, 7, 11], "c": [5, 4, 4, 2, 1]})
    k = kmo_global(df)
    assert 0 <= k <= 1
