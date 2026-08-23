import pandas as pd

from censo_rmr.ancoras import carregar_ancoras, validar_ancoras


def test_ancoras_equidade_reconhecem_casos_historicos():
    cfg = carregar_ancoras("config/ancoras_regressao.yaml")
    casos = cfg["equidade_fcu"]["casos"]
    rows = []
    for setor, campos in casos.items():
        rows.append({"CD_SETOR": setor, **campos})
    out = validar_ancoras(pd.DataFrame(rows), cfg["equidade_fcu"], conjunto="equidade_fcu")
    assert out.ok
    assert out.campos_divergentes == 0


def test_ancoras_detectam_divergencia_e_setor_ausente():
    cfg = carregar_ancoras("config/ancoras_regressao.yaml")
    spec = {
        "chave": "CD_SETOR",
        "tolerancia_abs": 1e-9,
        "casos": {
            "1": {"X": 10.0},
            "2": {"X": 20.0},
        },
    }
    df = pd.DataFrame({"CD_SETOR": ["1"], "X": [10.1]})
    out = validar_ancoras(df, spec, conjunto="teste")
    assert not out.ok
    assert "2" in out.setores_ausentes
    assert out.campos_divergentes == 2


def test_ancoras_densidade_reconhecem_casos_historicos():
    cfg = carregar_ancoras("config/ancoras_regressao.yaml")
    casos = cfg["densidade_ajustada"]["casos"]
    rows = [{"CD_SETOR": setor, **campos} for setor, campos in casos.items()]
    out = validar_ancoras(pd.DataFrame(rows), cfg["densidade_ajustada"], conjunto="densidade_ajustada")
    assert out.ok
