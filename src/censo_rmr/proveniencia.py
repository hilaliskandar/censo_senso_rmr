from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def sha256_arquivo(caminho: str | Path, bloco: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(caminho).open("rb") as f:
        for parte in iter(lambda: f.read(bloco), b""):
            h.update(parte)
    return h.hexdigest()


def commit_git() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def manifesto_execucao(
    *,
    configuracao: dict,
    fontes: Iterable[dict] = (),
    produtos: Iterable[dict] = (),
    avisos: Iterable[str] = (),
) -> dict:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit_git(),
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        "configuracao": configuracao,
        "fontes": list(fontes),
        "produtos": list(produtos),
        "avisos": list(avisos),
    }


def salvar_manifesto(manifesto: dict, caminho: str | Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return caminho
