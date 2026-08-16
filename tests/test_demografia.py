import math

import pandas as pd

from censo_rmr.demografia import preparar_demografia_setorial


MUNICIPIOS = {"2600054": "Abreu e Lima"}


def test_regressao_primeiro_setor_historico():
    # Linha 260005405000001 do CSV histórico do Bloco 1.
    valores = {
        "CD_SETOR": "260005405000001",
        "V01006": 627,
        "V01007": 298,
        "V01008": 329,
        "V01009": 25,
        "V01010": 26,
        "V01011": 20,
        "V01012": 28,
        "V01013": 24,
        "V01014": 19,
        "V01015": 38,
        "V01016": 39,
        "V01017": 42,
        "V01018": 23,
        "V01019": 14,
        "V01020": 17,
        "V01021": 14,
        "V01022": 22,
        "V01023": 21,
        "V01024": 19,
        "V01025": 19,
        "V01026": 58,
        "V01027": 52,
        "V01028": 53,
        "V01029": 27,
        "V01030": 27,
        "V01031": 42,
        "V01032": 40,
        "V01033": 42,
        "V01034": 49,
        "V01035": 43,
        "V01036": 38,
        "V01037": 96,
        "V01038": 91,
        "V01039": 95,
        "V01040": 50,
        "V01041": 41,
    }
    out = preparar_demografia_setorial(pd.DataFrame([valores]), MUNICIPIOS).iloc[0]

    assert out["POP_TOTAL"] == 627
    assert out["POP_0_14"] == 124
    assert out["POP_15_29"] == 130
    assert out["POP_30_59"] == 282
    assert out["POP_60_MAIS"] == 91
    assert out["POP_15_59"] == 412
    assert math.isclose(out["PCT_0_14"], 19.776714513556616)
    assert math.isclose(out["PCT_60_MAIS"], 14.513556618819775)
    assert math.isclose(out["RAZAO_DEPENDENCIA"], 52.18446601941748)
    assert math.isclose(out["INDICE_ENVELHECIMENTO"], 73.38709677419355)
    assert math.isclose(out["RAZAO_SEXO_H_100M"], 90.5775075987842)


def test_x_e_tratado_como_ausente_e_nao_zero():
    valores = {"CD_SETOR": "260005405000999"}
    for i in range(6, 42):
        valores[f"V010{i:02d}"] = "X"
    out = preparar_demografia_setorial(pd.DataFrame([valores]), MUNICIPIOS).iloc[0]
    assert pd.isna(out["POP_TOTAL"])
    assert pd.isna(out["V01031"])
