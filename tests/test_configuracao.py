from censo_rmr.configuracao import carregar_configuracao


def test_configuracao_rmr_tem_14_municipios():
    cfg = carregar_configuracao("config/config.yaml")
    assert len(cfg.municipios) == 14


def test_codigos_municipais_tem_sete_digitos():
    cfg = carregar_configuracao("config/config.yaml")
    assert all(len(codigo) == 7 and codigo.isdigit() for codigo in cfg.municipios)


def test_chave_setor_canonica():
    cfg = carregar_configuracao("config/config.yaml")
    assert cfg.chave_setor == "CD_SETOR"
