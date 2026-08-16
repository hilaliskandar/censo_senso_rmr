import math

import pandas as pd

from censo_rmr.composicao_domestica import calcular_indicadores
from censo_rmr.renda import LimiaresRenda, classificar_renda_relativa, preparar_renda_setorial


MUNICIPIOS = {"2600054": "Abreu e Lima"}


def test_renda_setor_260005405000001():
    bruto = pd.DataFrame([{
        "CD_SETOR": "260005405000001",
        "V06001": 220,
        "V06002": 627,
        "V06004": 1192.93,
    }])
    out = preparar_renda_setorial(bruto, MUNICIPIOS)
    out = classificar_renda_relativa(out, LimiaresRenda(p20=1300, p50=1800, p80=2500)).iloc[0]
    assert out["RESP_DPPO"] == 220
    assert out["MORADORES_DPPO"] == 627
    assert math.isclose(out["MORADORES_POR_RESP_DPPO"], 2.85)
    assert out["RENDA_MEDIA_RESP_COM_RENDA"] == 1192.93
    assert out["FAIXA_RELATIVA_RENDA_SETOR"] == "20% inferior RMR"


def test_composicao_setor_260005405000001():
    # Valores mínimos suficientes para reproduzir os indicadores históricos.
    bruto = pd.DataFrame([{
        "CD_SETOR": "260005405000001",
        "V01042": 220, "V01062": 75, "V01063": 145,
        "V01064": 0, "V01065": 0, "V01066": 0, "V01067": 164, "V01068": 56,
        "V01176": 101, "V01177": 0, "V01178": 0, "V01179": 119, "V01180": 0,
        "V01191": 171, "V01192": 0, "V01193": 0, "V01194": 49, "V01195": 0, "V01196": 0,
        "V01209": 44, "V01210": 122, "V01211": 54, "V01212": 0, "V01213": 0,
        "V01214": 18, "V01215": 26, "V01216": 0, "V01217": 0,
        "V01218": 15, "V01219": 39, "V01220": 0, "V01221": 0, "V01222": 0, "V01223": 0,
    }])
    out = calcular_indicadores(bruto).iloc[0]
    assert math.isclose(out["PCT_RESP_FEM"], 65.9090909090909)
    assert math.isclose(out["PCT_DOM_SEM_CONJUGE"], 54.09090909090909)
    assert math.isclose(out["PCT_RESP_SEM_CONJ_COM_FILHOS"], 22.272727272727277)
    assert math.isclose(out["PCT_DOM_UNIPESSOAL"], 20.0)
    assert math.isclose(out["PCT_DOM_ESTENDIDA"], 24.545454545454547)
    assert math.isclose(out["PCT_ESTENDIDA_RESP_FEM"], 72.22222222222223)
