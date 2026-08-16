import math

import pandas as pd

from censo_rmr.segregacao import calcular_indices, reconstruir_contagens_raciais


def test_reconstroi_contagens_por_participacao():
    df = pd.DataFrame({"POP_TOTAL": [100], "PCT_BRANCA": [30], "PCT_PRETA": [20], "PCT_PARDA": [50]})
    out = reconstruir_contagens_raciais(df).iloc[0]
    assert out["N_BRANCA"] == 30
    assert out["N_PRETA"] == 20
    assert out["N_PARDA"] == 50
    assert out["N_PPI"] == 70


def test_distribuicao_identica_tem_dissimilaridade_zero():
    df = pd.DataFrame({"x": [10, 20], "y": [20, 40], "t": [40, 80]})
    r = calcular_indices(df, "x", "y", total_col="t")
    assert math.isclose(r.dissimilaridade, 0.0)


def test_segregacao_perfeita_tem_dissimilaridade_um():
    df = pd.DataFrame({"x": [50, 0], "y": [0, 50], "t": [50, 50]})
    r = calcular_indices(df, "x", "y", total_col="t")
    assert math.isclose(r.dissimilaridade, 1.0)
    assert math.isclose(r.isolamento_x, 1.0)
    assert math.isclose(r.isolamento_y, 1.0)
    assert math.isclose(r.exposicao_x_a_y, 0.0)
    assert math.isclose(r.exposicao_y_a_x, 0.0)
