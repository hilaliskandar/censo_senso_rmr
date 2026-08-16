from pathlib import Path

import pytest

from censo_rmr.contratos import exigir_produto, verificar_produto


def test_verificacao_identifica_arquivo_ausente(tmp_path: Path):
    manifesto = {
        "produtos": {
            "demo": {
                "etapa": "demografia",
                "pasta_drive": "03_Tabelas_Indicadores",
                "obrigatorios": ["a.csv", "b.json"],
            }
        }
    }
    pasta = tmp_path / "03_Tabelas_Indicadores"
    pasta.mkdir()
    (pasta / "a.csv").write_text("x", encoding="utf-8")

    v = verificar_produto(tmp_path, manifesto, "demo")
    assert not v.ok
    assert v.presentes == ("a.csv",)
    assert v.ausentes == ("b.json",)


def test_exigir_produto_falha_quando_contrato_nao_foi_atendido(tmp_path: Path):
    manifesto = {
        "produtos": {
            "demo": {
                "etapa": "demografia",
                "pasta_drive": "03_Tabelas_Indicadores",
                "obrigatorios": ["a.csv"],
            }
        }
    }
    (tmp_path / "03_Tabelas_Indicadores").mkdir()
    with pytest.raises(FileNotFoundError):
        exigir_produto(tmp_path, manifesto, "demo")
