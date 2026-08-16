import math

import pandas as pd

from censo_rmr.densidade import calcular_densidade
from censo_rmr.equidade import calcular_equidade_alfabetizacao, padronizar_equidade_ibge


def test_padronizar_equidade_ibge_recompoe_universos_sem_misturar_fontes():
    demo = pd.DataFrame({"CD_SETOR": ["1"], "V01006": [100], "V01008": [55]})
    raca = pd.DataFrame(
        {
            "CD_SETOR": ["1"],
            "V01317": [30], "V01318": [20], "V01319": [0], "V01320": [50], "V01321": [0],
        }
    )
    alfa = pd.DataFrame({"CD_SETOR": ["1"]})
    valores = {
        "V00852": 25, "V00853": 3, "V00854": 30, "V00855": 3, "V00856": 20, "V00857": 2,
        "V00858": 12, "V00859": 2, "V00860": 14, "V00861": 1, "V00862": 10, "V00863": 1,
        "V00864": 13, "V00865": 1, "V00866": 16, "V00867": 2, "V00868": 10, "V00869": 1,
        "V00870": 8, "V00871": 1, "V00880": 10, "V00881": 1, "V00890": 8, "V00891": 1,
        "V00872": 4, "V00873": 1, "V00882": 5, "V00883": 1, "V00892": 4, "V00893": 1,
        "V00876": 10, "V00877": 1, "V00886": 12, "V00887": 1, "V00896": 10, "V00897": 1,
    }
    for col, valor in valores.items():
        alfa[col] = [valor]

    malha = pd.DataFrame({"CD_SETOR": ["1"], "CD_FCU": ["2600001"], "NM_FCU": ["Teste"]})
    base = padronizar_equidade_ibge(demo, raca, alfa, malha)
    out = calcular_equidade_alfabetizacao(base)

    assert base.loc[0, "POP_15_MAIS"] == 83
    assert base.loc[0, "NAO_ALF_15_MAIS"] == 8
    assert base.loc[0, "POP_BRANCA"] == 30
    assert out.loc[0, "PCT_PRETA_PARDA"] == 70.0
    assert out.loc[0, "SETOR_FCU"] == 1
    assert out.loc[0, "TAXA_NAO_ALF_15_MAIS"] == 100 * 8 / 83


def test_padronizar_equidade_ibge_nao_converte_supressao_em_zero():
    demo = pd.DataFrame({"CD_SETOR": ["1"], "V01006": [100], "V01008": [50]})
    raca = pd.DataFrame(
        {"CD_SETOR": ["1"], "V01317": [30], "V01318": [20], "V01319": [0], "V01320": [50], "V01321": [0]}
    )
    alfa = pd.DataFrame({"CD_SETOR": ["1"]})
    cols = [
        "V00852", "V00853", "V00854", "V00855", "V00856", "V00857",
        "V00858", "V00859", "V00860", "V00861", "V00862", "V00863",
        "V00864", "V00865", "V00866", "V00867", "V00868", "V00869",
        "V00870", "V00871", "V00880", "V00881", "V00890", "V00891",
        "V00872", "V00873", "V00882", "V00883", "V00892", "V00893",
        "V00876", "V00877", "V00886", "V00887", "V00896", "V00897",
    ]
    for c in cols:
        alfa[c] = [1]
    alfa["V00855"] = ["X"]

    base = padronizar_equidade_ibge(demo, raca, alfa)
    assert math.isnan(base.loc[0, "POP_15_MAIS"])
    assert math.isnan(base.loc[0, "NAO_ALF_15_MAIS"])


def test_equidade_basica_preserva_ausencias_e_calcula_percentuais():
    df = pd.DataFrame(
        {
            "POP_TOTAL": [100, 0],
            "POP_FEMININO": [55, 0],
            "POP_BRANCA": [30, 0],
            "POP_PRETA": [20, 0],
            "POP_PARDA": [50, 0],
            "POP_AMARELA": [0, 0],
            "POP_INDIGENA": [0, 0],
            "POP_15_MAIS": [80, 0],
            "NAO_ALF_15_MAIS": [8, 0],
            "CD_FCU": ["123", ""],
        }
    )
    out = calcular_equidade_alfabetizacao(df)
    assert out.loc[0, "PCT_FEMININO"] == 55.0
    assert out.loc[0, "PCT_PRETA_PARDA"] == 70.0
    assert out.loc[0, "TAXA_NAO_ALF_15_MAIS"] == 10.0
    assert out.loc[0, "SETOR_FCU"] == 1
    assert out.loc[1, "SETOR_FCU"] == 0
    assert math.isnan(out.loc[1, "PCT_FEMININO"])


def test_equidade_gaps_por_sexo_e_raca():
    df = pd.DataFrame(
        {
            "POP_TOTAL": [100],
            "POP_FEMININO": [52],
            "POP_BRANCA": [40],
            "POP_PRETA": [20],
            "POP_PARDA": [40],
            "POP_AMARELA": [0],
            "POP_INDIGENA": [0],
            "POP_15_MAIS": [80],
            "NAO_ALF_15_MAIS": [8],
            "POP_MASC_15_MAIS": [38],
            "NAO_ALF_MASC_15_MAIS": [4],
            "POP_FEM_15_MAIS": [42],
            "NAO_ALF_FEM_15_MAIS": [4],
            "POP_BRANCA_15_MAIS": [32],
            "NAO_ALF_BRANCA_15_MAIS": [2],
            "POP_PRETA_15_MAIS": [16],
            "NAO_ALF_PRETA_15_MAIS": [2],
            "POP_PARDA_15_MAIS": [32],
            "NAO_ALF_PARDA_15_MAIS": [4],
        }
    )
    out = calcular_equidade_alfabetizacao(df)
    assert "GAP_NAO_ALF_FEM_MASC" in out.columns
    assert "TAXA_NAO_ALF_PRETA_PARDA" in out.columns
    assert "GAP_NAO_ALF_PPI_BRANCA" in out.columns


def test_densidade_formulas_e_limiar_explicito():
    df = pd.DataFrame(
        {
            "POP_TOTAL": [1000, 1000],
            "AREA_DOM": [0.10, 0.05],
            "AREA_TOTAL": [0.20, 0.20],
        }
    )
    out, meta = calcular_densidade(df, limiar_alta=15000.0)
    assert out.loc[0, "DENS_ADJ"] == 10000.0
    assert out.loc[0, "DENS_CONV"] == 5000.0
    assert out.loc[0, "PCT_AREA_DOM"] == 50.0
    assert out.loc[0, "FATOR"] == 2.0
    assert bool(out.loc[0, "ALTA_DENS_ADJ"]) is False
    assert bool(out.loc[1, "ALTA_DENS_ADJ"]) is True
    assert meta.limiar_alta_densidade == 15000.0
