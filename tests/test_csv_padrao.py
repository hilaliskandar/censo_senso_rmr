from pathlib import Path

import pandas as pd

from censo_rmr.csv_padrao import ler_csv_rmr, salvar_csv_rmr
from censo_rmr.regressao import comparar_csvs


def test_roundtrip_csv_rmr_preserva_decimal_e_chave(tmp_path: Path):
    df = pd.DataFrame({
        "CD_SETOR": pd.Series(["260005405000001"], dtype="string"),
        "COD_MUN": pd.Series(["2600054"], dtype="string"),
        "VALOR": [19.776714513556616],
        "CLASSE": ["Faixa intermediária"],
    })
    p = tmp_path / "a.csv"
    salvar_csv_rmr(df, p)
    texto = p.read_text(encoding="utf-8-sig")
    assert ";" in texto
    assert "19,776714513556616" in texto
    lido = ler_csv_rmr(p)
    assert lido.iloc[0]["CD_SETOR"] == "260005405000001"
    assert abs(lido.iloc[0]["VALOR"] - 19.776714513556616) < 1e-12


def test_comparador_aceita_csv_historico_e_csv_padrao(tmp_path: Path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    df = pd.DataFrame({"CD_SETOR": ["1"], "X": [2.5]})
    salvar_csv_rmr(df, a)
    salvar_csv_rmr(df, b)
    assert comparar_csvs(a, b).ok
