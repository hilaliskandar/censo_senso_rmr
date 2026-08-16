"""Interface de linha de comando para o pipeline RMR."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import ModoPipeline, executar


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pipeline reproduzivel Censo 2022 - RMR")
    p.add_argument("--modo", choices=[m.value for m in ModoPipeline], required=True)
    p.add_argument("--repo", required=True, help="Raiz local do repositorio censo_senso_rmr")
    p.add_argument("--drive", required=True, help="Raiz montada da pasta Censo_2022_Setores_RMR")
    p.add_argument("--saida-json", help="Arquivo opcional para gravar o relatorio retornado")
    return p


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    resultado = executar(args.modo, Path(args.repo), Path(args.drive))
    texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
    print(texto)
    if args.saida_json:
        destino = Path(args.saida_json)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
