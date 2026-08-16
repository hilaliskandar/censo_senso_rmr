"""Aquisição, cache e verificação de fontes externas do pipeline."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests


@dataclass(frozen=True)
class ArquivoFonte:
    url: str
    caminho: Path
    sha256: str
    bytes: int
    reutilizado: bool


def sha256_arquivo(caminho: str | Path, bloco: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(caminho).open("rb") as f:
        for pedaco in iter(lambda: f.read(bloco), b""):
            h.update(pedaco)
    return h.hexdigest()


def nome_por_url(url: str) -> str:
    nome = Path(urlparse(url).path).name
    if not nome:
        raise ValueError(f"URL sem nome de arquivo: {url}")
    return nome


def baixar_com_cache(
    url: str,
    pasta_cache: str | Path,
    *,
    sha256_esperado: str | None = None,
    timeout: int = 120,
    reprocessar: bool = False,
) -> ArquivoFonte:
    """Baixa uma fonte apenas quando necessário e registra seu checksum.

    Se ``sha256_esperado`` for fornecido, um arquivo de cache divergente não é
    reutilizado. O download é gravado primeiro em arquivo temporário e somente
    depois promovido ao nome final.
    """
    if not url:
        raise ValueError("URL da fonte não foi verificada/configurada.")

    pasta = Path(pasta_cache)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome_por_url(url)

    if destino.exists() and not reprocessar:
        digest = sha256_arquivo(destino)
        if sha256_esperado is None or digest == sha256_esperado:
            return ArquivoFonte(url, destino, digest, destino.stat().st_size, True)

    temporario = destino.with_suffix(destino.suffix + ".part")
    with requests.get(url, stream=True, timeout=timeout) as resposta:
        resposta.raise_for_status()
        with temporario.open("wb") as f:
            shutil.copyfileobj(resposta.raw, f)

    digest = sha256_arquivo(temporario)
    if sha256_esperado is not None and digest != sha256_esperado:
        temporario.unlink(missing_ok=True)
        raise ValueError(
            f"Checksum divergente para {url}: esperado {sha256_esperado}, obtido {digest}"
        )
    temporario.replace(destino)
    return ArquivoFonte(url, destino, digest, destino.stat().st_size, False)


def extrair_zip_seguro(
    arquivo_zip: str | Path,
    pasta_destino: str | Path,
) -> list[Path]:
    """Extrai ZIP impedindo path traversal."""
    origem = Path(arquivo_zip)
    destino = Path(pasta_destino)
    destino.mkdir(parents=True, exist_ok=True)
    raiz = destino.resolve()
    extraidos: list[Path] = []

    with zipfile.ZipFile(origem) as zf:
        for membro in zf.infolist():
            alvo = (destino / membro.filename).resolve()
            if raiz not in alvo.parents and alvo != raiz:
                raise ValueError(f"Caminho inseguro no ZIP: {membro.filename}")
            zf.extract(membro, destino)
            if not membro.is_dir():
                extraidos.append(alvo)
    return extraidos
