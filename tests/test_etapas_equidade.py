from pathlib import Path

import pandas as pd

from censo_rmr.csv_padrao import ler_csv_rmr
from censo_rmr.etapas_equidade import VARS_ALFA, executar_equidade_fcu


def _salvar(df: pd.DataFrame, caminho: Path) -> None:
    df.to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")


def test_executar_equidade_fcu_em_staging(tmp_path, monkeypatch):
    setor = "260005405000001"

    demo = pd.DataFrame({"CD_SETOR": [setor], "V01006": [100], "V01008": [55]})
    raca = pd.DataFrame(
        {
            "CD_SETOR": [setor],
            "V01317": [30], "V01318": [20], "V01319": [0],
            "V01320": [50], "V01321": [0],
        }
    )
    alfa_vals = {c: 0 for c in VARS_ALFA}
    # POP_15_MAIS = 80; NAO_ALF_15_MAIS = 8.
    alfa_vals.update({"V00852": 72, "V00853": 8})
    alfa = pd.DataFrame({"CD_SETOR": [setor], **{k: [v] for k, v in alfa_vals.items()}})

    p_demo = tmp_path / "demo.csv"
    p_raca = tmp_path / "raca.csv"
    p_alfa = tmp_path / "alfa.csv"
    _salvar(demo, p_demo)
    _salvar(raca, p_raca)
    _salvar(alfa, p_alfa)

    malha = pd.DataFrame(
        {"CD_SETOR": [setor], "AREA_KM2": [0.2], "CD_FCU": ["123"], "NM_FCU": ["Teste"]}
    )
    monkeypatch.setattr("censo_rmr.etapas_equidade.gpd.read_file", lambda _: malha)

    res = executar_equidade_fcu(
        p_demo,
        p_raca,
        p_alfa,
        tmp_path / "malha.gpkg",
        tmp_path / "staging",
        {"2600054": "Abreu e Lima"},
    )

    out = ler_csv_rmr(res["setorial"])
    assert len(out) == 1
    assert out.loc[0, "PCT_FEMININO"] == 55.0
    assert out.loc[0, "PCT_PRETA_PARDA"] == 70.0
    assert out.loc[0, "TAXA_NAO_ALF_15_MAIS"] == 10.0
    assert out.loc[0, "SETOR_FCU"] == 1
    assert res["resultado"]["promocao_permitida"] is False
