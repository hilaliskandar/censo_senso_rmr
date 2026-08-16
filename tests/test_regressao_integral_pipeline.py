import pandas as pd

from censo_rmr.csv_padrao import salvar_csv_rmr
from censo_rmr.pipeline import _regressao_integral


def _spec():
    return {
        "chave": "CD_SETOR",
        "colunas_centrais": ["VALOR", "CLASSE"],
        "tolerancia_abs": 1e-9,
        "tolerancia_rel": 1e-9,
        "referencia_historica_drive": {
            "csv_referencia_caminho": "00_Pipeline/02_Regressao/ref.csv",
            "csv_referencia_id": "drive123",
            "setores_referencia": 2,
        },
    }


def test_regressao_integral_compara_e_diagnostica(tmp_path):
    drive = tmp_path / "drive"
    ref = drive / "00_Pipeline/02_Regressao/ref.csv"
    novo = tmp_path / "novo.csv"
    salvar_csv_rmr(pd.DataFrame({"CD_SETOR": ["1", "2"], "VALOR": [10.0, 20.0], "CLASSE": ["A", "B"]}), ref)
    salvar_csv_rmr(pd.DataFrame({"CD_SETOR": ["1", "2"], "VALOR": [10.0, 21.0], "CLASSE": ["A", "C"]}), novo)

    out = _regressao_integral(drive, novo, _spec(), limite_amostras=5)
    assert out["status"] == "comparado"
    assert out["ok"] is False
    assert out["resultado"]["linhas_novo"] == 2
    assert out["resultado"]["linhas_referencia"] == 2
    assert out["divergencias_por_coluna"]["VALOR"] == 1
    assert out["divergencias_por_coluna"]["CLASSE"] == 1
    assert len(out["amostras_divergencias"]) == 2


def test_regressao_integral_reporta_referencia_ausente(tmp_path):
    novo = tmp_path / "novo.csv"
    salvar_csv_rmr(pd.DataFrame({"CD_SETOR": ["1"], "VALOR": [10.0], "CLASSE": ["A"]}), novo)
    out = _regressao_integral(tmp_path / "drive", novo, _spec())
    assert out["status"] == "referencia_nao_materializada_no_drive_montado"
    assert out["ok"] is False
    assert out["drive_file_id"] == "drive123"
