import pytest

from censo_rmr.mapeamento import auditar_validacao_documental, exigir_mapeamento_promovivel


def test_staging_pode_identificar_pendencias_sem_bloquear_auditoria():
    dados = {
        "tema": {
            "campo": {"status": "operacional_conferido_validacao_xlsx_pendente"},
            "ok": {"status": "confirmado_portal_oficial"},
        }
    }
    aud = auditar_validacao_documental(dados)
    assert not aud.promovivel
    assert len(aud.pendencias) == 1


def test_promocao_recusa_mapeamento_pendente():
    dados = {"tema": {"campo": {"status": "validacao_documental_pendente"}}}
    with pytest.raises(ValueError, match="não pode ser promovido"):
        exigir_mapeamento_promovivel(dados)


def test_promocao_aceita_quando_status_estao_confirmados():
    dados = {"tema": {"campo": {"status": "confirmado_portal_oficial"}}}
    exigir_mapeamento_promovivel(dados)
