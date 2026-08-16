import math

import pandas as pd

from censo_rmr.renda_2026 import classificar_mediana_1sm, preparar_renda_2026, quintil_operacional_mediana_media


MUNICIPIOS = {"2600054": "Abreu e Lima"}


def test_indicadores_setor_historico_abreu():
    bruto = pd.DataFrame([{
        "CD_SETOR": "260005405000001",
        "V06001": 220,
        "V06002": 627,
        "V06004": 1192.93,
        "V06005": 711106.42,
        "V06006": 1200,
    }])
    out = preparar_renda_2026(bruto, MUNICIPIOS).iloc[0]
    assert out["RENDA_MEDIANA_NOVA"] == 1200
    assert math.isclose(out["RAZAO_MEDIA_MEDIANA"], 0.9941083333333334)
    assert math.isclose(out["DIF_MEDIA_MEDIANA"], -7.07, abs_tol=1e-9)


def test_mediana_igual_1212_nao_entra_na_classificacao_estrita():
    df = pd.DataFrame({"RENDA_MEDIANA_NOVA": [1200.0, 1212.0, 1300.0]})
    out = classificar_mediana_1sm(df, referencia=1212.0)
    assert list(out["BAIXO_REND_MEDIANA_REL"]) == [True, False, False]
    assert out.iloc[1]["FAIXA_MEDIANA_1SM"] == "Igual a R$ 1.212"


def test_quintil_operacional_desempata_pela_media_e_cria_grupos_quase_iguais():
    df = pd.DataFrame({
        "CD_SETOR": [str(i) for i in range(10)],
        "RENDA_MEDIANA_NOVA": [1212] * 6 + [1300, 1400, 1500, 1600],
        "RENDA_MEDIA_NOVA": [1500, 1200, 1300, 1400, 1100, 1600, 1700, 1800, 1900, 2000],
    })
    out = quintil_operacional_mediana_media(df)
    assert out["QUINTIL_OPER_MEDIANA_MEDIA"].notna().all()
    assert (out["QUINTIL_OPER_MEDIANA_MEDIA"] == 1).sum() == 2
    # Entre medianas empatadas, menor média recebe maior desvantagem.
    a = out.loc[out["RENDA_MEDIA_NOVA"] == 1100, "DESV_RENDA_RANK"].iloc[0]
    b = out.loc[out["RENDA_MEDIA_NOVA"] == 1600, "DESV_RENDA_RANK"].iloc[0]
    assert a > b
