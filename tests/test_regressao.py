import pandas as pd

from censo_rmr.regressao import comparar_dataframes


def test_regressao_identica_aprova():
    a = pd.DataFrame({"CD_SETOR": ["1", "2"], "x": [1.0, 2.0], "classe": ["a", "b"]})
    b = a.copy()
    r = comparar_dataframes(a, b)
    assert r.ok
    assert r.divergencias_numericas == 0
    assert r.divergencias_textuais == 0


def test_tolerancia_numerica_e_explicita():
    a = pd.DataFrame({"CD_SETOR": ["1"], "x": [1.00000001]})
    b = pd.DataFrame({"CD_SETOR": ["1"], "x": [1.0]})
    assert comparar_dataframes(a, b, atol=1e-6, rtol=0).ok
    assert not comparar_dataframes(a, b, atol=1e-12, rtol=0).ok


def test_detecta_universo_diferente():
    a = pd.DataFrame({"CD_SETOR": ["1", "2"], "x": [1, 2]})
    b = pd.DataFrame({"CD_SETOR": ["1", "3"], "x": [1, 2]})
    r = comparar_dataframes(a, b)
    assert not r.ok
    assert r.chaves_apenas_novo == 1
    assert r.chaves_apenas_referencia == 1


def test_detecta_divergencia_textual():
    a = pd.DataFrame({"CD_SETOR": ["1"], "classe": ["A"]})
    b = pd.DataFrame({"CD_SETOR": ["1"], "classe": ["B"]})
    r = comparar_dataframes(a, b)
    assert not r.ok
    assert r.divergencias_textuais == 1
