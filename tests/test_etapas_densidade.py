import pandas as pd

from censo_rmr.etapas_densidade import executar_densidade_oficial


def test_executar_densidade_oficial_compara_recomposicao(tmp_path, monkeypatch):
    setor = "260005405000001"
    pop = pd.DataFrame({"CD_SETOR": [setor], "POP_TOTAL": [1000]})
    malha = pd.DataFrame(
        {"CD_SETOR": [setor], "AREA_KM2": [0.2], "CD_FCU": [""], "NM_FCU": [""]}
    )
    monkeypatch.setattr("censo_rmr.etapas_densidade.gpd.read_file", lambda _: malha)

    area = pd.DataFrame({"setor": [setor], "area_dom": [0.1], "dens_oficial": [10000.0]})
    caminho_area = tmp_path / "area.xlsx"
    area.to_excel(caminho_area, index=False)

    res = executar_densidade_oficial(
        pop,
        tmp_path / "malha.gpkg",
        caminho_area,
        {"CD_SETOR": "setor", "AREA_DOM": "area_dom", "DENS_ADJ_OFICIAL": "dens_oficial"},
        tmp_path / "staging",
        {"2600054": "Abreu e Lima"},
        limiar_alta=15000.0,
    )

    out = pd.read_csv(res["setorial"], sep=";", dtype={"CD_SETOR": "string"})
    assert out.loc[0, "DENS_ADJ"] == 10000.0
    assert out.loc[0, "DENS_CONV"] == 5000.0
    assert out.loc[0, "PCT_AREA_DOM"] == 50.0
    assert out.loc[0, "FATOR"] == 2.0
    assert res["resultado"]["comparacao_densidade_oficial"]["ok"] is True
    assert res["resultado"]["promocao_permitida"] is False
