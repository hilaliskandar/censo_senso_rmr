import pandas as pd

from censo_rmr.regressao import diagnosticar_regressao


def test_diagnostico_expoe_chaves_e_divergencias_por_coluna():
    novo = pd.DataFrame(
        {
            "CD_SETOR": ["1", "2", "3"],
            "VALOR": [10.0, 21.0, 30.0],
            "CLASSE": ["A", "B", "C"],
        }
    )
    ref = pd.DataFrame(
        {
            "CD_SETOR": ["1", "2", "4"],
            "VALOR": [10.0, 20.0, 40.0],
            "CLASSE": ["A", "X", "D"],
        }
    )

    d = diagnosticar_regressao(novo, ref, colunas=["VALOR", "CLASSE"], max_amostras=5)

    assert d["resumo"]["ok"] is False
    assert d["amostra_chaves_apenas_novo"] == ["3"]
    assert d["amostra_chaves_apenas_referencia"] == ["4"]
    assert d["divergencias_por_coluna"]["VALOR"]["divergencias"] == 1
    assert d["divergencias_por_coluna"]["VALOR"]["amostras"][0]["CD_SETOR"] == "2"
    assert d["divergencias_por_coluna"]["CLASSE"]["divergencias"] == 1


def test_diagnostico_respeita_tolerancia_numerica():
    novo = pd.DataFrame({"CD_SETOR": ["1"], "VALOR": [10.000000001]})
    ref = pd.DataFrame({"CD_SETOR": ["1"], "VALOR": [10.0]})

    d = diagnosticar_regressao(novo, ref, colunas=["VALOR"], atol=1e-8, rtol=0.0)

    assert d["resumo"]["ok"] is True
    assert d["divergencias_por_coluna"] == {}
