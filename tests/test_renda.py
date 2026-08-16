import math

import pandas as pd

from censo_rmr.renda import (
    calcular_limiares_rmr,
    preparar_renda_setorial,
    resumir_renda_municipios,
)


MUNICIPIOS = {"2600054": "Abreu e Lima", "2611606": "Recife"}


def _base():
    return pd.DataFrame(
        [
            {"CD_SETOR": "260005405000001", "V06001": 25, "V06002": 70, "V06004": "1000,0"},
            {"CD_SETOR": "260005405000002", "V06001": 30, "V06002": 90, "V06004": "2000,0"},
            {"CD_SETOR": "261160605000001", "V06001": 40, "V06002": 80, "V06004": "3000,0"},
            {"CD_SETOR": "261160605000002", "V06001": 10, "V06002": 20, "V06004": "500,0"},
        ]
    )


def test_limiar_renda_usa_apenas_setores_com_minimo_de_responsaveis():
    df = preparar_renda_setorial(_base(), MUNICIPIOS)
    lim = calcular_limiares_rmr(df, responsaveis_minimos=20)
    # O setor de renda 500 tem apenas 10 responsáveis e fica fora da distribuição.
    assert math.isclose(lim.p20, 1400.0)
    assert math.isclose(lim.p50, 2000.0)
    assert math.isclose(lim.p80, 2600.0)


def test_resumo_municipal_descreve_distribuicao_setorial():
    df = preparar_renda_setorial(_base(), MUNICIPIOS)
    lim = calcular_limiares_rmr(df, responsaveis_minimos=20)
    resumo = resumir_renda_municipios(df, lim, responsaveis_minimos=20)
    abreu = resumo[resumo["COD_MUN"] == "2600054"].iloc[0]
    assert abreu["SETORES_RENDA_VALIDOS"] == 2
    assert math.isclose(abreu["MEDIANA_SETOR_RENDA_MEDIA_RESP"], 1500.0)
    assert math.isclose(abreu["PCT_SET_NO_20_INF_RMR"], 50.0)


def test_decimal_com_virgula_e_convertido_sem_alterar_semantica():
    df = preparar_renda_setorial(_base().iloc[[0]], MUNICIPIOS)
    assert df.iloc[0]["RENDA_MEDIA_RESP_COM_RENDA"] == 1000.0
