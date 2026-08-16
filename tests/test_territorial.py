import pandas as pd
import pytest

from censo_rmr.territorial import (
    integrar_area_e_malha,
    normalizar_area_domiciliada_oficial,
    preparar_atributos_malha,
)


def test_preparar_atributos_malha_preserva_fcu_e_area():
    df = pd.DataFrame(
        {
            "CD_SETOR": ["1", "2"],
            "AREA_KM2": [0.2, 0.3],
            "CD_FCU": ["26001", ""],
            "NM_FCU": ["Teste", ""],
        }
    )
    out, aud = preparar_atributos_malha(df)
    assert list(out["SETOR_FCU"]) == [1, 0]
    assert aud.registros == 2
    assert aud.com_fcu == 1
    assert out.loc[0, "AREA_KM2"] == 0.2


def test_preparar_atributos_malha_recusa_duplicidade():
    df = pd.DataFrame(
        {
            "CD_SETOR": ["1", "1"],
            "AREA_KM2": [0.2, 0.2],
            "CD_FCU": ["", ""],
        }
    )
    with pytest.raises(ValueError, match="duplicidade"):
        preparar_atributos_malha(df)


def test_area_domiciliada_exige_mapeamento_explicito():
    bruto = pd.DataFrame({"setor": ["1"], "area_efetiva": [0.1], "dens": [10000]})
    out = normalizar_area_domiciliada_oficial(
        bruto,
        mapa_colunas={
            "CD_SETOR": "setor",
            "AREA_DOM": "area_efetiva",
            "DENS_ADJ_OFICIAL": "dens",
        },
    )
    assert out.loc[0, "CD_SETOR"] == "1"
    assert out.loc[0, "AREA_DOM"] == 0.1
    assert out.loc[0, "DENS_ADJ_OFICIAL"] == 10000


def test_integrar_area_e_malha_registra_falta_de_cobertura():
    malha = pd.DataFrame(
        {
            "CD_SETOR": ["1", "2"],
            "AREA_KM2": [0.2, 0.3],
            "CD_FCU": ["", ""],
            "SETOR_FCU": [0, 0],
        }
    )
    area = pd.DataFrame({"CD_SETOR": ["1"], "AREA_DOM": [0.1]})
    out = integrar_area_e_malha(malha, area)
    assert out.loc[0, "_join_area_dom"] == "both"
    assert out.loc[1, "_join_area_dom"] == "left_only"
