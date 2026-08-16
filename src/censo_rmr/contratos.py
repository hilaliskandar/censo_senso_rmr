"""Contratos de entrada e saída do pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class VerificacaoProduto:
    etapa: str
    raiz: Path
    obrigatorios: tuple[str, ...]
    presentes: tuple[str, ...]
    ausentes: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.ausentes

    @property
    def pasta(self) -> Path:
        """Alias legado: a auditoria atual trabalha com a raiz do projeto."""
        return self.raiz


def carregar_produtos(caminho: str | Path) -> dict:
    with Path(caminho).open("r", encoding="utf-8") as f:
        dados = yaml.safe_load(f)
    if not isinstance(dados, dict) or "produtos" not in dados:
        raise ValueError("Manifesto de produtos inválido: chave 'produtos' ausente.")
    return dados


def _caminhos_obrigatorios(spec: dict) -> tuple[str, ...]:
    if "arquivos_obrigatorios" in spec:
        return tuple(spec.get("arquivos_obrigatorios", []))
    pasta = spec.get("pasta_drive")
    nomes = spec.get("obrigatorios", [])
    if pasta:
        return tuple(str(Path(pasta) / nome) for nome in nomes)
    return tuple(nomes)


def verificar_produto(raiz_drive: str | Path, manifesto: dict, nome_produto: str) -> VerificacaoProduto:
    produtos = manifesto["produtos"]
    if nome_produto not in produtos:
        raise KeyError(f"Produto não declarado: {nome_produto}")
    spec = produtos[nome_produto]
    raiz = Path(raiz_drive)
    obrigatorios = _caminhos_obrigatorios(spec)
    presentes = tuple(rel for rel in obrigatorios if (raiz / rel).exists())
    ausentes = tuple(rel for rel in obrigatorios if not (raiz / rel).exists())
    return VerificacaoProduto(
        etapa=spec.get("etapa", nome_produto),
        raiz=raiz,
        obrigatorios=obrigatorios,
        presentes=presentes,
        ausentes=ausentes,
    )


def exigir_produto(raiz_drive: str | Path, manifesto: dict, nome_produto: str) -> VerificacaoProduto:
    verificacao = verificar_produto(raiz_drive, manifesto, nome_produto)
    if not verificacao.ok:
        faltam = ", ".join(verificacao.ausentes)
        raise FileNotFoundError(f"Contrato da etapa '{verificacao.etapa}' não atendido. Ausentes: {faltam}")
    return verificacao
