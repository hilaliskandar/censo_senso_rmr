"""Geração cartográfica declarativa para os produtos do diagnóstico RMR.

A geometria é sempre dissolvida por CD_SETOR antes de qualquer junção. Setores
sem informação temática permanecem sem dado e são contabilizados no metadado.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


@dataclass(frozen=True)
class AuditoriaMapa:
    id_mapa: str
    municipio: str
    codigo_municipio: str
    campo: str
    geometria_setores: int
    com_dado: int
    sem_dado: int
    crs: str | None
    arquivo: str


def slug(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "_", normal).strip("_").upper()


def preparar_geometria_municipal(
    malha: gpd.GeoDataFrame,
    codigo_municipio: str,
    *,
    chave: str = "CD_SETOR",
    coluna_municipio: str = "CD_MUN",
    crs: str = "EPSG:4674",
) -> gpd.GeoDataFrame:
    if chave not in malha.columns:
        raise ValueError(f"Malha sem chave {chave}.")
    g = malha.copy()
    g[chave] = g[chave].astype("string")
    if coluna_municipio in g.columns:
        g = g[g[coluna_municipio].astype("string").eq(str(codigo_municipio))].copy()
    else:
        g = g[g[chave].str.startswith(str(codigo_municipio), na=False)].copy()
    if g.empty:
        raise ValueError(f"Nenhuma geometria encontrada para município {codigo_municipio}.")
    g = g[[chave, "geometry"]].dissolve(by=chave, as_index=False)
    if g.crs is None:
        g = g.set_crs(crs)
    elif str(g.crs).upper() != crs.upper():
        g = g.to_crs(crs)
    if g[chave].duplicated().any():
        raise ValueError("Dissolve não produziu uma geometria única por CD_SETOR.")
    return g


def juntar_tema(
    geometria: gpd.GeoDataFrame,
    dados: pd.DataFrame,
    campos: list[str],
    *,
    chave: str = "CD_SETOR",
) -> gpd.GeoDataFrame:
    faltantes = [c for c in [chave, *campos] if c not in dados.columns]
    if faltantes:
        raise ValueError(f"Dados temáticos sem colunas: {faltantes}")
    d = dados[[chave, *campos]].copy()
    d[chave] = d[chave].astype("string")
    if d[chave].duplicated().any():
        raise ValueError("Dados temáticos possuem CD_SETOR duplicado; agregue antes da cartografia.")
    return geometria.merge(d, on=chave, how="left", validate="one_to_one")


def _nota(spec: Mapping, notas: Mapping[str, str]) -> str:
    return " ".join(notas[n] for n in spec.get("nota", []) if n in notas)


def _finalizar(ax, titulo: str, nota: str) -> None:
    ax.set_title(titulo, fontsize=12, pad=10)
    ax.set_axis_off()
    if nota:
        ax.text(0, -0.035, nota, transform=ax.transAxes, ha="left", va="top", fontsize=7, wrap=True)
    plt.tight_layout()


def renderizar_mapa(
    geometria: gpd.GeoDataFrame,
    dados: pd.DataFrame,
    spec: Mapping,
    *,
    municipio: str,
    codigo_municipio: str,
    pasta_saida: str | Path,
    notas: Mapping[str, str] | None = None,
    chave: str = "CD_SETOR",
    dpi: int = 220,
    figsize: tuple[float, float] = (8, 8),
) -> tuple[Path, AuditoriaMapa]:
    campo = spec["campo"]
    g = juntar_tema(geometria, dados, [campo], chave=chave)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = spec["arquivo"].format(slug=slug(municipio), municipio=municipio)
    caminho = pasta / nome
    titulo = spec["titulo"].format(municipio=municipio)
    tipo = spec["tipo"]
    fig, ax = plt.subplots(figsize=figsize)

    if tipo == "continuo":
        g[campo] = pd.to_numeric(g[campo], errors="coerce")
        g.plot(
            column=campo,
            ax=ax,
            legend=True,
            cmap=spec.get("cmap", "viridis"),
            edgecolor="white",
            linewidth=float(spec.get("linewidth", 0.1)),
            missing_kwds={"color": "lightgrey", "label": "Sem dado"},
            legend_kwds={"label": spec.get("legenda", campo), "shrink": 0.6},
        )
    elif tipo == "binario":
        serie = pd.to_numeric(g[campo], errors="coerce")
        rotulos_raw = spec.get("rotulos", {0: "0", 1: "1"})
        rotulos = {int(k): v for k, v in rotulos_raw.items()}
        categorias = [rotulos[k] for k in sorted(rotulos)]
        g["_categoria"] = serie.map(rotulos)
        prop_colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        handles = []
        for i, cat in enumerate(categorias):
            sub = g[g["_categoria"].eq(cat)]
            if len(sub):
                kwargs = {"edgecolor": "white", "linewidth": float(spec.get("linewidth", 0.1))}
                if prop_colors:
                    kwargs["color"] = prop_colors[i % len(prop_colors)]
                sub.plot(ax=ax, **kwargs)
                handles.append(Patch(facecolor=prop_colors[i % len(prop_colors)] if prop_colors else "none", label=cat))
        miss = g[g["_categoria"].isna()]
        if len(miss):
            miss.plot(ax=ax, color="lightgrey", edgecolor="white", linewidth=float(spec.get("linewidth", 0.1)))
            handles.append(Patch(facecolor="lightgrey", label="Sem dado"))
        if handles:
            ax.legend(handles=handles, loc="lower left", fontsize=8)
    elif tipo == "categorico":
        categorias = list(spec.get("categorias", []))
        prop_colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        handles = []
        for i, cat in enumerate(categorias):
            sub = g[g[campo].astype("string").eq(str(cat))]
            if len(sub):
                kwargs = {"edgecolor": "white", "linewidth": float(spec.get("linewidth", 0.1))}
                if prop_colors:
                    kwargs["color"] = prop_colors[i % len(prop_colors)]
                sub.plot(ax=ax, **kwargs)
                handles.append(Patch(facecolor=prop_colors[i % len(prop_colors)] if prop_colors else "none", label=str(cat)))
        conhecidos = set(str(x) for x in categorias)
        miss = g[g[campo].isna() | ~g[campo].astype("string").isin(conhecidos)]
        if len(miss):
            miss.plot(ax=ax, color="lightgrey", edgecolor="white", linewidth=float(spec.get("linewidth", 0.1)))
            handles.append(Patch(facecolor="lightgrey", label="Sem dado"))
        if handles:
            ax.legend(handles=handles, loc="lower left", fontsize=8)
    else:
        plt.close(fig)
        raise ValueError(f"Tipo cartográfico não suportado: {tipo}")

    _finalizar(ax, titulo, _nota(spec, notas or {}))
    fig.savefig(caminho, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    com_dado = int(g[campo].notna().sum())
    auditoria = AuditoriaMapa(
        id_mapa=str(spec.get("id", campo)),
        municipio=municipio,
        codigo_municipio=str(codigo_municipio),
        campo=campo,
        geometria_setores=len(g),
        com_dado=com_dado,
        sem_dado=len(g) - com_dado,
        crs=str(g.crs) if g.crs else None,
        arquivo=str(caminho),
    )
    caminho.with_suffix(".json").write_text(
        json.dumps(asdict(auditoria), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return caminho, auditoria


def gerar_nucleo_municipal(
    malha: gpd.GeoDataFrame,
    base_tematica: pd.DataFrame,
    specs: list[Mapping],
    *,
    municipio: str,
    codigo_municipio: str,
    pasta_saida: str | Path,
    notas: Mapping[str, str] | None = None,
    chave: str = "CD_SETOR",
) -> list[AuditoriaMapa]:
    geo = preparar_geometria_municipal(malha, codigo_municipio, chave=chave)
    auditorias = []
    for spec in specs:
        _, a = renderizar_mapa(
            geo,
            base_tematica,
            spec,
            municipio=municipio,
            codigo_municipio=codigo_municipio,
            pasta_saida=pasta_saida,
            notas=notas,
            chave=chave,
        )
        auditorias.append(a)
    return auditorias
