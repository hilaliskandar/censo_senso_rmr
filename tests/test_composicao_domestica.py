import pandas as pd

from censo_rmr.composicao_domestica import calcular_indicadores


def linha_base():
    return {
        "CD_SETOR": "260005400000001",
        "V01042": 10,
        "V01062": 4,
        "V01063": 6,
        "V01064": 0,
        "V01065": 0,
        "V01066": 0,
        "V01067": 0,
        "V01068": 2,
        "V01176": 1,
        "V01177": 2,
        "V01178": 1,
        "V01179": 6,
        "V01180": 90,
        "V01191": 2,
        "V01192": 2,
        "V01193": 1,
        "V01194": 3,
        "V01195": 2,
        "V01196": 90,
        "V01209": 2,
        "V01210": 4,
        "V01211": 3,
        "V01212": 1,
        "V01213": 90,
        "V01214": 1,
        "V01215": 1,
        "V01216": 2,
        "V01217": 2,
        "V01218": 1,
        "V01219": 2,
        "V01220": 1,
        "V01221": 0,
        "V01222": 0,
        "V01223": 0,
    }


def test_exclui_coletivos_dos_denominadores():
    out = calcular_indicadores(pd.DataFrame([linha_base()])).iloc[0]
    assert out["DOM_CONJ_DEN"] == 10
    assert out["DOM_COMP_DEN"] == 10
    assert out["DOM_TIPO_DEN"] == 10


def test_percentuais_principais():
    out = calcular_indicadores(pd.DataFrame([linha_base()])).iloc[0]
    assert out["PCT_RESP_FEM"] == 60
    assert out["PCT_RESP_60_MAIS"] == 20
    assert out["PCT_DOM_SEM_CONJUGE"] == 60
    assert out["PCT_RESP_SEM_CONJ_COM_FILHOS"] == 30
    assert out["PCT_DOM_UNIPESSOAL"] == 20
