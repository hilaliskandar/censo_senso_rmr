import pandas as pd

from censo_rmr.qa import qa_chave_unica, qa_intervalo, qa_nao_nulo


def test_chave_unica_aprovada():
    df = pd.DataFrame({"CD_SETOR": ["1", "2", "3"]})
    assert qa_chave_unica(df, "CD_SETOR").passou


def test_chave_unica_reprovada():
    df = pd.DataFrame({"CD_SETOR": ["1", "1"]})
    assert not qa_chave_unica(df, "CD_SETOR").passou


def test_percentual_no_intervalo():
    df = pd.DataFrame({"pct": [0, 25, 100, None]})
    assert qa_intervalo(df, "pct", 0, 100).passou


def test_nulo_detectado():
    df = pd.DataFrame({"x": [1, None]})
    assert not qa_nao_nulo(df, "x").passou
