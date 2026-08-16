from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ConfiguracaoPipeline:
    dados: dict[str, Any]
    arquivo: Path

    @property
    def municipios(self) -> dict[str, str]:
        return self.dados["territorio"]["municipios_rmr"]

    @property
    def chave_setor(self) -> str:
        return self.dados["territorio"]["chave_setor"]

    @property
    def chave_municipio(self) -> str:
        return self.dados["territorio"]["chave_municipio"]

    def parametro(self, nome: str, padrao: Any = None) -> Any:
        return self.dados.get("parametros_operacionais", {}).get(nome, padrao)


def carregar_configuracao(caminho: str | Path) -> ConfiguracaoPipeline:
    caminho = Path(caminho)
    with caminho.open("r", encoding="utf-8") as f:
        dados = yaml.safe_load(f)
    validar_configuracao(dados)
    return ConfiguracaoPipeline(dados=dados, arquivo=caminho)


def validar_configuracao(dados: dict[str, Any]) -> None:
    obrigatorios = ["projeto", "drive", "territorio", "execucao"]
    ausentes = [k for k in obrigatorios if k not in dados]
    if ausentes:
        raise ValueError(f"Secoes obrigatorias ausentes: {ausentes}")

    municipios = dados["territorio"].get("municipios_rmr", {})
    if len(municipios) != 14:
        raise ValueError(
            "A configuracao atual da RMR deve conter 14 municipios; "
            f"foram encontrados {len(municipios)}."
        )

    codigos_invalidos = [c for c in municipios if len(str(c)) != 7 or not str(c).isdigit()]
    if codigos_invalidos:
        raise ValueError(f"Codigos municipais invalidos: {codigos_invalidos}")
