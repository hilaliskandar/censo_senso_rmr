"""Ingestao e auditoria de fontes territoriais oficiais do IBGE."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .io_ibge import normalizar_chave_setor


@dataclass(frozen=True)
class AuditoriaTerritorial:
    registros: int
    setores_unicos: int
    duplicados: int
    com_fcu: int
    sem_fcu: int


def consolidar_atributos_por_setor(df: pd.DataFrame) -> pd.DataFrame:
    """Consolida repeticoes tabulares de CD_SETOR somente quando os atributos concordam.

    A malha pode conter mais de uma feicao para um mesmo setor. Para a juncao
    analitica de atributos, isso nao exige dissolver a geometria: exige apenas
    provar que os atributos usados pelo pipeline sao univocos. Qualquer conflito
    em AREA_KM2, CD_FCU ou NM_FCU interrompe a etapa.
    """
    out = normalizar_chave_setor(df)
    campos = [c for c in ("AREA_KM2", "CD_FCU", "NM_FCU") if c in out.columns]
    if not out["CD_SETOR"].duplicated().any():
        return out.copy()

    conflitos: list[str] = []
    for setor, grupo in out.groupby("CD_SETOR", dropna=False, sort=False):
        if len(grupo) <= 1:
            continue
        for campo in campos:
            vals = grupo[campo].astype("string").str.strip().replace({"": pd.NA}).dropna().unique()
            if len(vals) > 1:
                conflitos.append(f"{setor}/{campo}: {vals.tolist()}")
    if conflitos:
        amostra = "; ".join(conflitos[:10])
        raise ValueError(f"Atributos territoriais conflitantes em CD_SETOR duplicado: {amostra}")

    return out.drop_duplicates(subset=["CD_SETOR"], keep="first").copy()


def preparar_atributos_malha(df: pd.DataFrame) -> tuple[pd.DataFrame, AuditoriaTerritorial]:
    """Seleciona os atributos territoriais necessarios sem alterar a geometria.

    Repeticoes de CD_SETOR sao consolidadas apenas quando os atributos analiticos
    sao consistentes. A dissolucao geometrica permanece uma etapa espacial separada.
    """
    bruto = normalizar_chave_setor(df)
    obrigatorias = ["CD_SETOR", "AREA_KM2", "CD_FCU"]
    faltantes = [c for c in obrigatorias if c not in bruto.columns]
    if faltantes:
        raise ValueError(f"Atributos obrigatorios da malha ausentes: {faltantes}")

    duplicados = int(bruto["CD_SETOR"].duplicated(keep=False).sum())
    out = consolidar_atributos_por_setor(bruto)

    campos = ["CD_SETOR", "AREA_KM2", "CD_FCU"]
    if "NM_FCU" in out.columns:
        campos.append("NM_FCU")
    tab = out[campos].copy()
    tab["AREA_KM2"] = pd.to_numeric(tab["AREA_KM2"], errors="coerce")
    cd = tab["CD_FCU"].astype("string")
    tab["SETOR_FCU"] = (cd.notna() & cd.str.strip().ne("")).astype("Int64")

    auditoria = AuditoriaTerritorial(
        registros=len(bruto),
        setores_unicos=int(tab["CD_SETOR"].nunique(dropna=True)),
        duplicados=duplicados,
        com_fcu=int(tab["SETOR_FCU"].fillna(0).sum()),
        sem_fcu=int((tab["SETOR_FCU"] == 0).sum()),
    )
    return tab, auditoria


def normalizar_area_domiciliada_oficial(
    df: pd.DataFrame,
    *,
    mapa_colunas: dict[str, str],
) -> pd.DataFrame:
    """Normaliza a tabela oficial de area efetivamente domiciliada.

    Nao sao adivinhados nomes de colunas. `mapa_colunas` deve informar os nomes
    presentes na publicacao oficial para os campos canonicos abaixo:

    - CD_SETOR
    - AREA_DOM
    - opcionalmente DENS_ADJ_OFICIAL

    AREA_TOTAL e obtida preferencialmente da malha oficial (`AREA_KM2`) em etapa
    de juncao posterior, evitando duplicacao de autoridades para a area do setor.
    """
    obrigatorios = {"CD_SETOR", "AREA_DOM"}
    ausentes_mapa = obrigatorios - set(mapa_colunas)
    if ausentes_mapa:
        raise ValueError(f"Mapeamento incompleto da tabela de area domiciliada: {sorted(ausentes_mapa)}")

    faltantes_fonte = [orig for orig in mapa_colunas.values() if orig not in df.columns]
    if faltantes_fonte:
        raise ValueError(f"Colunas declaradas nao encontradas na fonte oficial: {faltantes_fonte}")

    renomear = {orig: canon for canon, orig in mapa_colunas.items()}
    out = df[list(renomear)].rename(columns=renomear).copy()
    out = normalizar_chave_setor(out)
    if out["CD_SETOR"].isna().any() or out["CD_SETOR"].duplicated().any():
        raise ValueError("Tabela oficial de area domiciliada deve ter CD_SETOR nao nulo e unico")

    out["AREA_DOM"] = pd.to_numeric(out["AREA_DOM"], errors="coerce")
    if "DENS_ADJ_OFICIAL" in out.columns:
        out["DENS_ADJ_OFICIAL"] = pd.to_numeric(out["DENS_ADJ_OFICIAL"], errors="coerce")
    return out


def integrar_area_e_malha(
    atributos_malha: pd.DataFrame,
    area_domiciliada: pd.DataFrame,
) -> pd.DataFrame:
    """Une as duas autoridades territoriais por CD_SETOR com validacao 1:1."""
    m = normalizar_chave_setor(atributos_malha)
    a = normalizar_chave_setor(area_domiciliada)
    if m["CD_SETOR"].duplicated().any() or a["CD_SETOR"].duplicated().any():
        raise ValueError("CD_SETOR deve ser unico nas duas fontes territoriais")
    return m.merge(a, on="CD_SETOR", how="left", validate="one_to_one", indicator="_join_area_dom")
