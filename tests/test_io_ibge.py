import zipfile
from pathlib import Path

import pandas as pd
import pytest

from censo_rmr.io_ibge import extrair_csv_principal_zip, ler_csv_ibge


def test_ler_csv_normaliza_cd_setor_e_preserva_texto(tmp_path: Path):
    p = tmp_path / "demo.csv"
    p.write_text("CD_setor;V01006;V01007\n260005405000001;627;298\n", encoding="utf-8")
    df = ler_csv_ibge(p, colunas=["CD_SETOR", "V01006"])
    assert list(df.columns) == ["CD_SETOR", "V01006"]
    assert df.iloc[0]["CD_SETOR"] == "260005405000001"
    assert df.iloc[0]["V01006"] == 627


def test_coluna_solicitada_ausente_falha(tmp_path: Path):
    p = tmp_path / "demo.csv"
    p.write_text("CD_SETOR;A\n1;2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ler_csv_ibge(p, colunas=["CD_SETOR", "B"])


def test_extrai_csv_unico_do_zip(tmp_path: Path):
    z = tmp_path / "fonte.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("pasta/dados.csv", "CD_SETOR;A\n1;2\n")
    p = extrair_csv_principal_zip(z, tmp_path / "out")
    assert p.name == "dados.csv"
    assert pd.read_csv(p, sep=";").iloc[0]["A"] == 2


def test_zip_com_multiplos_csvs_exige_preferencia(tmp_path: Path):
    z = tmp_path / "fonte.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("a.csv", "x\n1\n")
        f.writestr("b.csv", "x\n2\n")
    with pytest.raises(ValueError):
        extrair_csv_principal_zip(z, tmp_path / "out")
