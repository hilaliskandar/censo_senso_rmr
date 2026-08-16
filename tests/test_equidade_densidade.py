import math

import pandas as pd

from censo_rmr.densidade import calcular_densidade
from censo_rmr.equidade import calcular_equidade_alfabetizacao


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
