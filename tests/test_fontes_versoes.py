import pytest

from censo_rmr.fontes import validar_versoes_minimas


def _fontes_ok():
    return {
        "basico": {"url_csv_zip": "https://x/Agregados_por_setores_basico_BR_20260520.zip"},
        "caracteristicas_domicilio_2": {"url_csv_zip": "https://x/Agregados_por_setores_caracteristicas_domicilio2_BR_20250417.zip"},
        "caracteristicas_domicilio_3": {"url_csv_zip": "https://x/Agregados_por_setores_caracteristicas_domicilio3_BR_20250417.zip"},
    }


def test_versoes_minimas_aceitas():
    validar_versoes_minimas(_fontes_ok())


def test_versao_antiga_domicilio2_rejeitada():
    fontes = _fontes_ok()
    fontes["caracteristicas_domicilio_2"]["url_csv_zip"] = "https://x/Agregados_por_setores_caracteristicas_domicilio2_BR.zip"
    with pytest.raises(ValueError, match="versão mínima auditada"):
        validar_versoes_minimas(fontes)


def test_fonte_obrigatoria_ausente_rejeitada():
    fontes = _fontes_ok()
    del fontes["basico"]
    with pytest.raises(ValueError, match="Fonte obrigatória ausente"):
        validar_versoes_minimas(fontes)
