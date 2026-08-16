import math

import pandas as pd

from censo_rmr.cruzamentos import (
    calcular_limiares_cruzamentos,
    cruzar_renda_composicao,
    resumir_cruzamentos_municipios,
)
from censo_rmr.renda import calcular_limiares_rmr, preparar_renda_setorial


MUNICIPIOS = {"2600054": "Abreu e Lima", "2611606": "Recife"}


def _renda():
    bruto = pd.DataFrame(
        [
            {"CD_SETOR": "260005405000001", "V06001": 25, "V06002": 60, "V06004": 1000},
            {"CD_SETOR": "260005405000002", "V06001": 25, "V06002": 60, "V06004": 2000},
            {"CD_SETOR": "261160605000001", "V06001": 25, "V06002": 60, "V06004": 3000},
            {"CD_SETOR": "261160605000002", "V06001": 25, "V06002": 60, "V06004": 4000},
        ]
    )
    return preparar_renda_setorial(bruto, MUNICIPIOS)


def _composicao():
    return pd.DataFrame(
        [
            {"CD_SETOR": "260005405000001", "POP_TOTAL": 200, "DOM_TIPO_DEN": 50, "PCT_RESP_SEM_CONJ_COM_FILHOS": 10, "PCT_DOM_UNIPESSOAL": 10, "PCT_DOM_ESTENDIDA": 10, "PCT_RESP_60_MAIS": 10, "PCT_0_14": 30, "PCT_60_MAIS": 10},
            {"CD_SETOR": "260005405000002", "POP_TOTAL": 200, "DOM_TIPO_DEN": 50, "PCT_RESP_SEM_CONJ_COM_FILHOS": 20, "PCT_DOM_UNIPESSOAL": 20, "PCT_DOM_ESTENDIDA": 20, "PCT_RESP_60_MAIS": 20, "PCT_0_14": 20, "PCT_60_MAIS": 20},
            {"CD_SETOR": "261160605000001", "POP_TOTAL": 200, "DOM_TIPO_DEN": 50, "PCT_RESP_SEM_CONJ_COM_FILHOS": 30, "PCT_DOM_UNIPESSOAL": 30, "PCT_DOM_ESTENDIDA": 30, "PCT_RESP_60_MAIS": 30, "PCT_0_14": 10, "PCT_60_MAIS": 30},
            {"CD_SETOR": "261160605000002", "POP_TOTAL": 200, "DOM_TIPO_DEN": 50, "PCT_RESP_SEM_CONJ_COM_FILHOS": 40, "PCT_DOM_UNIPESSOAL": 40, "PCT_DOM_ESTENDIDA": 40, "PCT_RESP_60_MAIS": 40, "PCT_0_14": 5, "PCT_60_MAIS": 40},
        ]
    )


def test_limiares_sao_derivados_dos_dados_e_nao_hardcoded():
    lim = calcular_limiares_cruzamentos(_composicao(), quantil=0.90)
    assert math.isclose(lim.monoparental_alta, 37.0)
    assert math.isclose(lim.unipessoal_alta, 37.0)
    assert math.isclose(lim.estendida_alta, 37.0)
    assert math.isclose(lim.jovem_alto, 27.0)
    assert math.isclose(lim.idoso_alto, 37.0)


def test_cruzamento_preserva_universo_de_setores_validos_de_renda():
    renda = _renda()
    lim_renda = calcular_limiares_rmr(renda)
    lim_cruza = calcular_limiares_cruzamentos(_composicao(), quantil=0.90)
    validos = cruzar_renda_composicao(renda, _composicao(), lim_renda, lim_cruza)
    resumo = resumir_cruzamentos_municipios(validos)
    assert len(validos) == 4
    assert set(resumo["MUNICIPIO"]) == {"Abreu e Lima", "Recife"}
