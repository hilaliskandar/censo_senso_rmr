"""Indicadores descritivos de sexo, cor ou raca, alfabetizacao e FCU.

O modulo separa duas operacoes:
1. padronizacao das variaveis brutas publicadas pelo IBGE;
2. calculo dos indicadores canonicos utilizados no estudo da RMR.

Os codigos Vxxxxx usados aqui estao documentados em config/mapeamento_ibge.yaml.
Valores nao numericos, inclusive supressoes publicadas como X, tornam-se ausentes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _pct(num: pd.Series, den: pd.Series) -> pd.Series:
    num = pd.to_numeric(num, errors="coerce")
    den = pd.to_numeric(den, errors="coerce")
    out = pd.Series(np.nan, index=num.index, dtype="float64")
    ok = num.notna() & den.notna() & den.gt(0)
    out.loc[ok] = 100.0 * num.loc[ok] / den.loc[ok]
    return out


def _soma_completa(df: pd.DataFrame, colunas: list[str]) -> pd.Series:
    """Soma somente quando todas as parcelas estao observadas.

    Esta regra evita transformar supressoes do IBGE em zero por efeito colateral
    de uma soma com skipna=True.
    """
    faltantes = [c for c in colunas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas IBGE obrigatorias ausentes: {faltantes}")
    valores = df[colunas].apply(pd.to_numeric, errors="coerce")
    return valores.sum(axis=1, min_count=len(colunas))


def padronizar_equidade_ibge(
    demografia: pd.DataFrame,
    cor_ou_raca: pd.DataFrame,
    alfabetizacao: pd.DataFrame,
    malha: pd.DataFrame | None = None,
    *,
    chave: str = "CD_SETOR",
) -> pd.DataFrame:
    """Converte tabelas tematicas brutas do IBGE em contagens canonicas.

    Cada tabela mantem seu proprio universo. As tabelas sao unidas apenas por
    CD_SETOR e os denominadores de alfabetizacao sao recompostos no proprio
    agregado de alfabetizacao.
    """
    bases = []
    for nome, df in (
        ("demografia", demografia),
        ("cor_ou_raca", cor_ou_raca),
        ("alfabetizacao", alfabetizacao),
    ):
        if chave not in df.columns:
            raise ValueError(f"{nome}: chave {chave} ausente")
        x = df.copy()
        x[chave] = x[chave].astype("string")
        if x[chave].isna().any() or x[chave].duplicated().any():
            raise ValueError(f"{nome}: {chave} deve ser nao nulo e unico")
        bases.append(x)

    demo, raca, alfa = bases
    out = pd.DataFrame({chave: demo[chave]})
    out["POP_TOTAL"] = pd.to_numeric(demo["V01006"], errors="coerce")
    out["POP_FEMININO"] = pd.to_numeric(demo["V01008"], errors="coerce")

    raca_sel = raca[[chave, "V01317", "V01318", "V01319", "V01320", "V01321"]].copy()
    raca_sel = raca_sel.rename(
        columns={
            "V01317": "POP_BRANCA",
            "V01318": "POP_PRETA",
            "V01319": "POP_AMARELA",
            "V01320": "POP_PARDA",
            "V01321": "POP_INDIGENA",
        }
    )
    out = out.merge(raca_sel, on=chave, how="left", validate="one_to_one")

    a = alfabetizacao.copy()
    contagens = {
        "POP_15_MAIS": ["V00852", "V00853", "V00854", "V00855", "V00856", "V00857"],
        "NAO_ALF_15_MAIS": ["V00853", "V00855", "V00857"],
        "POP_MASC_15_MAIS": ["V00858", "V00859", "V00860", "V00861", "V00862", "V00863"],
        "NAO_ALF_MASC_15_MAIS": ["V00859", "V00861", "V00863"],
        "POP_FEM_15_MAIS": ["V00864", "V00865", "V00866", "V00867", "V00868", "V00869"],
        "NAO_ALF_FEM_15_MAIS": ["V00865", "V00867", "V00869"],
        "POP_BRANCA_15_MAIS": ["V00870", "V00871", "V00880", "V00881", "V00890", "V00891"],
        "NAO_ALF_BRANCA_15_MAIS": ["V00871", "V00881", "V00891"],
        "POP_PRETA_15_MAIS": ["V00872", "V00873", "V00882", "V00883", "V00892", "V00893"],
        "NAO_ALF_PRETA_15_MAIS": ["V00873", "V00883", "V00893"],
        "POP_PARDA_15_MAIS": ["V00876", "V00877", "V00886", "V00887", "V00896", "V00897"],
        "NAO_ALF_PARDA_15_MAIS": ["V00877", "V00887", "V00897"],
    }
    alfa_pad = pd.DataFrame({chave: a[chave]})
    for campo, vars_ in contagens.items():
        alfa_pad[campo] = _soma_completa(a, vars_)
    out = out.merge(alfa_pad, on=chave, how="left", validate="one_to_one")

    if malha is not None:
        if chave not in malha.columns or "CD_FCU" not in malha.columns:
            raise ValueError("malha: CD_SETOR e CD_FCU sao obrigatorios")
        m = malha.copy()
        m[chave] = m[chave].astype("string")
        if m[chave].duplicated().any():
            raise ValueError("malha: CD_SETOR deve ser unico antes da juncao FCU")
        campos = [chave, "CD_FCU"]
        if "NM_FCU" in m.columns:
            campos.append("NM_FCU")
        out = out.merge(m[campos], on=chave, how="left", validate="one_to_one")

    return out


def calcular_equidade_alfabetizacao(df: pd.DataFrame) -> pd.DataFrame:
    obrigatorias = [
        "POP_TOTAL", "POP_FEMININO", "POP_BRANCA", "POP_PRETA", "POP_PARDA",
        "POP_AMARELA", "POP_INDIGENA", "POP_15_MAIS", "NAO_ALF_15_MAIS",
    ]
    faltantes = [c for c in obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatorias ausentes: {faltantes}")

    out = df.copy()
    for c in obrigatorias:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["PCT_FEMININO"] = _pct(out["POP_FEMININO"], out["POP_TOTAL"])
    out["PCT_BRANCA"] = _pct(out["POP_BRANCA"], out["POP_TOTAL"])
    out["PCT_PRETA"] = _pct(out["POP_PRETA"], out["POP_TOTAL"])
    out["PCT_PARDA"] = _pct(out["POP_PARDA"], out["POP_TOTAL"])
    out["PCT_PRETA_PARDA"] = _pct(out["POP_PRETA"] + out["POP_PARDA"], out["POP_TOTAL"])
    out["PCT_AMARELA"] = _pct(out["POP_AMARELA"], out["POP_TOTAL"])
    out["PCT_INDIGENA"] = _pct(out["POP_INDIGENA"], out["POP_TOTAL"])
    out["TAXA_NAO_ALF_15_MAIS"] = _pct(out["NAO_ALF_15_MAIS"], out["POP_15_MAIS"])

    pares = {
        "MASC": ("NAO_ALF_MASC_15_MAIS", "POP_MASC_15_MAIS"),
        "FEM": ("NAO_ALF_FEM_15_MAIS", "POP_FEM_15_MAIS"),
        "BRANCA": ("NAO_ALF_BRANCA_15_MAIS", "POP_BRANCA_15_MAIS"),
        "PRETA": ("NAO_ALF_PRETA_15_MAIS", "POP_PRETA_15_MAIS"),
        "PARDA": ("NAO_ALF_PARDA_15_MAIS", "POP_PARDA_15_MAIS"),
    }
    for sufixo, (num, den) in pares.items():
        if num in out.columns and den in out.columns:
            out[f"TAXA_NAO_ALF_{sufixo}"] = _pct(out[num], out[den])

    if {"TAXA_NAO_ALF_FEM", "TAXA_NAO_ALF_MASC"}.issubset(out.columns):
        out["GAP_NAO_ALF_FEM_MASC"] = out["TAXA_NAO_ALF_FEM"] - out["TAXA_NAO_ALF_MASC"]

    if {"NAO_ALF_PRETA_15_MAIS", "NAO_ALF_PARDA_15_MAIS", "POP_PRETA_15_MAIS", "POP_PARDA_15_MAIS"}.issubset(out.columns):
        out["TAXA_NAO_ALF_PRETA_PARDA"] = _pct(
            out["NAO_ALF_PRETA_15_MAIS"] + out["NAO_ALF_PARDA_15_MAIS"],
            out["POP_PRETA_15_MAIS"] + out["POP_PARDA_15_MAIS"],
        )

    if {"TAXA_NAO_ALF_PRETA_PARDA", "TAXA_NAO_ALF_BRANCA"}.issubset(out.columns):
        out["GAP_NAO_ALF_PPI_BRANCA"] = out["TAXA_NAO_ALF_PRETA_PARDA"] - out["TAXA_NAO_ALF_BRANCA"]

    if "CD_FCU" in out.columns:
        cd = out["CD_FCU"].astype("string")
        out["SETOR_FCU"] = (cd.notna() & cd.str.strip().ne("")).astype("Int64")

    return out
