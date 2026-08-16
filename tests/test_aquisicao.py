import zipfile
from pathlib import Path

import pytest

from censo_rmr.aquisicao import extrair_zip_seguro, nome_por_url, sha256_arquivo


def test_nome_por_url():
    assert nome_por_url("https://exemplo.org/a/b/fonte.zip") == "fonte.zip"


def test_sha256_e_deterministico(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"abc")
    assert sha256_arquivo(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_extracao_zip_segura(tmp_path: Path):
    z = tmp_path / "ok.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("dados/a.csv", "x;y\n1;2\n")
    extraidos = extrair_zip_seguro(z, tmp_path / "out")
    assert len(extraidos) == 1
    assert extraidos[0].read_text() == "x;y\n1;2\n"


def test_zip_com_path_traversal_falha(tmp_path: Path):
    z = tmp_path / "ruim.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("../fora.txt", "nao")
    with pytest.raises(ValueError):
        extrair_zip_seguro(z, tmp_path / "out")
