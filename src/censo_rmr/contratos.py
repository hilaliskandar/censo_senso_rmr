"""Contratos de entrada e saída do pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class VerificacaoProduto:
    etapa: str
    pasta: Path
    obrigatorios: tuple[str, ...]
    presentes: tuple[str, ...]
    ausentes: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.ausentes


def carregar_produtos(caminho: str | Path) -> dict:
    with Path(caminho).open("r", encoding="utf-8") as f:
        dados = yaml.safe_load(f)
    if not isinstance(dados, dict) or "produtos" not in dados:
        raise ValueError("Manifesto de produtos inválido: chave 'produtos' ausente.")
    return dados


def verificar_produto(
    raiz_drive: str | Path,
    manifesto: dict,
    nome_produto: str,
) -> VerificacaoProduto:
    produtos = manifesto["produtos"]
    if nome_produto not in produtos:
        raise KeyError(f"Produto não declarado: {nome_produto}")
    spec = produtos[nome_produto]
    obrigatorios = tuple(spec.get("obrigatorios", []))
    pasta = Path(raiz_drive) / spec["pasta_drive"]
    presentes = tuple(nome for nome in obrigatorios if (pasta / nome).exists())
    ausentes = tuple(nome for nome in obrigatorios if not (pasta / nome).exists())
    return VerificacaoProduto(
        etapa=spec.get("etapa", nome_produto),
        pasta=pasta,
        obrigatorios=obrigatorios,
        presentes=presentes,
        ausentes=ausentes,
    )


def exigir_produto(
    raiz_drive: str | Path,
    manifesto: dict,
    nome_produto: str,
) -> VerificacaoProduto:
    verificacao = verificar_produto(raiz_drive, manifesto, nome_produto)
    if not verificacao.ok:
        faltam = ", ".join(verificacao.ausentes)
        raise FileNotFoundError(
            f"Contrato da etapa '{verificacao.etapa}' não atendido. Ausentes: {faltam}"
        )
    return verificacao
