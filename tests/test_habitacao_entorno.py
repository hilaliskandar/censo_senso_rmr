import math

import pandas as pd

from censo_rmr.entorno import classificar_entorno
from censo_rmr.habitacao import calcular_indicadores_habitacao


def test_indicadores_habitacao_preservam_denominadores():
    bruto = pd.DataFrame([{
        "V00001": 100, "V00002": 10, "V00005": 300,
        "V00022": 2, "V00023": 3, "V00024": 4, "V00025": 5, "V00026": 6,
        "V00050": 5, "V00052": 4, "V00464": 20, "V00200": 7, "V00201": 3,
        "V00236": 2, "V00237": 1, "V00238": 4,
        "V00312": 5, "V00313": 2, "V00314": 3, "V00315": 1, "V00316": 4,
        "V00399": 2, "V00400": 1, "V00401": 3, "V00402": 4,
    }])
    out = calcular_indicadores_habitacao(bruto).iloc[0]
    assert math.isclose(out["PCT_IMPROVISADOS"], 100 * 10 / 110)
    assert out["MORADORES_POR_DPPO"] == 3
    assert out["PCT_DPPO_6MAIS"] == 20
    assert out["PCT_ESGOTO_PRECARIO"] == 15
    assert out["PCT_LIXO_INADEQUADO"] == 10


def test_x_habitacional_permanece_ausente():
    linha = {c: 1 for c in [
        "V00001", "V00002", "V00005", "V00022", "V00023", "V00024", "V00025", "V00026",
        "V00050", "V00052", "V00464", "V00200", "V00201", "V00236", "V00237", "V00238",
        "V00312", "V00313", "V00314", "V00315", "V00316", "V00399", "V00400", "V00401", "V00402",
    ]}
    linha["V00052"] = "X"
    out = calcular_indicadores_habitacao(pd.DataFrame([linha])).iloc[0]
    assert pd.isna(out["PCT_ESTRUTURA_DEGRADADA"])


def test_entorno_reproduz_primeiros_setores_com_limiares_historicos():
    limiares = {
        "pct_sem_pavimentacao": 54.55908639523341,
        "pct_sem_bueiro": 92.14655296178255,
        "pct_sem_iluminacao": 2.005683104081274,
        "pct_sem_calcada": 79.36625410910925,
        "pct_calcada_com_obstaculo": 100.0,
        "pct_sem_arvores": 93.0201131363922,
    }
    df = pd.DataFrame([
        {"pct_sem_pavimentacao": 0, "pct_sem_bueiro": 21.85007974481659, "pct_sem_iluminacao": 0, "pct_sem_calcada": 49.76076555023923, "pct_calcada_com_obstaculo": 98.0952380952381, "pct_sem_arvores": 99.36204146730462},
        {"pct_sem_pavimentacao": 0, "pct_sem_bueiro": 67.40576496674058, "pct_sem_iluminacao": 0, "pct_sem_calcada": 17.1840354767184, "pct_calcada_com_obstaculo": 100, "pct_sem_arvores": 100},
    ])
    out, meta = classificar_entorno(df, limiares=limiares)
    assert list(out["n_carencias_entorno_altas"].astype(int)) == [1, 2]
    assert list(out["precariedade_entorno"]) == ["Baixa ou não identificada", "Moderada"]
    assert meta.origem_limiares == "explicitos"


def test_entorno_missing_nao_vira_carencia():
    df = pd.DataFrame({
        "pct_sem_pavimentacao": [None, 100],
        "pct_sem_bueiro": [None, 100],
        "pct_sem_iluminacao": [None, 100],
        "pct_sem_calcada": [None, 100],
        "pct_calcada_com_obstaculo": [None, 100],
        "pct_sem_arvores": [None, 100],
    })
    out, _ = classificar_entorno(df, limiares={c: 50 for c in df.columns})
    assert pd.isna(out.iloc[0]["precariedade_entorno"])
    assert out.iloc[0]["n_dimensoes_entorno_validas"] == 0
    assert out.iloc[1]["n_carencias_entorno_altas"] == 6
