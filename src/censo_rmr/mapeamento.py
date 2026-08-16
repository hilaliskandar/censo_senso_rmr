"""Validação de maturidade documental dos mapeamentos de variáveis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class AuditoriaMapeamento:
    pendencias: tuple[str, ...]

    @property
    def promovivel(self) -> bool:
        return not self.pendencias


def carregar_mapeamento(caminho: str | Path) -> dict:
    with Path(caminho).open("r", encoding="utf-8") as f:
        dados = yaml.safe_load(f) or {}
    if not isinstance(dados, dict):
        raise ValueError("Mapeamento IBGE deve ser um objeto YAML.")
    return dados


def auditar_validacao_documental(mapeamento: dict) -> AuditoriaMapeamento:
    """Localiza status que ainda declaram validacao documental pendente.

    A auditoria e deliberadamente conservadora: qualquer string de status com
    `pendente` impede promocao, embora nao impeca execucao em staging.
    """
    pendencias: list[str] = []

    def visitar(obj: object, caminho: str) -> None:
        if isinstance(obj, dict):
            for chave, valor in obj.items():
                prox = f"{caminho}.{chave}" if caminho else str(chave)
                if chave == "status" and isinstance(valor, str) and "pendente" in valor.lower():
                    pendencias.append(f"{prox}: {valor}")
                elif chave.startswith("status_") and isinstance(valor, str) and "pendente" in valor.lower():
                    pendencias.append(f"{prox}: {valor}")
                else:
                    visitar(valor, prox)
        elif isinstance(obj, list):
            for i, valor in enumerate(obj):
                visitar(valor, f"{caminho}[{i}]")

    visitar(mapeamento, "")
    return AuditoriaMapeamento(tuple(sorted(set(pendencias))))


def exigir_mapeamento_promovivel(mapeamento: dict) -> None:
    auditoria = auditar_validacao_documental(mapeamento)
    if not auditoria.promovivel:
        detalhes = "\n- ".join(auditoria.pendencias)
        raise ValueError(
            "Mapeamento ainda possui validações documentais pendentes e não pode ser promovido.\n- "
            + detalhes
        )
