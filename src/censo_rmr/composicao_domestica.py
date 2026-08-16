from __future__ import annotations

import pandas as pd


VARIAVEIS_FONTE = [
    "CD_SETOR", "V01042", "V01062", "V01063", "V01064", "V01065", "V01066", "V01067", "V01068",
    "V01176", "V01177", "V01178", "V01179", "V01180",
    "V01191", "V01192", "V01193", "V01194", "V01195", "V01196",
    "V01209", "V01210", "V01211", "V01212", "V01213",
    "V01214", "V01215", "V01216", "V01217", "V01218", "V01219", "V01220", "V01221", "V01222", "V01223",
]


def percentual(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
    den = denominador.where(denominador != 0)
    return 100.0 * numerador / den


def validar_colunas_fonte(df: pd.DataFrame) -> None:
    ausentes = [c for c in VARIAVEIS_FONTE if c not in df.columns]
    if ausentes:
        raise ValueError(f"Variaveis obrigatorias ausentes em composicao domestica: {ausentes}")


def calcular_indicadores(df_fonte: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores setoriais preservando as regras do prototipo historico.

    A funcao nao le nem grava arquivos. A interpretacao das variaveis deve permanecer
    vinculada ao dicionario oficial do IBGE usado na execucao.
    """
    validar_colunas_fonte(df_fonte)
    df = df_fonte.copy()

    for c in VARIAVEIS_FONTE[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["RESP_TOTAL"] = df["V01042"]
    df["RESP_HOMENS"] = df["V01062"]
    df["RESP_MULHERES"] = df["V01063"]
    df["RESP_SEXO_DEN"] = df[["V01062", "V01063"]].sum(axis=1, min_count=1)
    df["PCT_RESP_FEM"] = percentual(df["RESP_MULHERES"], df["RESP_SEXO_DEN"])
    df["RESP_60_MAIS"] = df["V01068"]
    df["PCT_RESP_60_MAIS"] = percentual(df["RESP_60_MAIS"], df["RESP_TOTAL"])

    # Situacao conjugal: exclui unidade coletiva V01180 do denominador.
    df["DOM_COM_CONJ_DIF"] = df["V01176"]
    df["DOM_COM_CONJ_MESMO"] = df["V01177"]
    df["DOM_COM_CONJ_AMBOS"] = df["V01178"]
    df["DOM_SEM_CONJUGE"] = df["V01179"]
    df["DOM_COLETIVO_CONJ"] = df["V01180"]
    df["DOM_CONJ_DEN"] = df[["V01176", "V01177", "V01178", "V01179"]].sum(axis=1, min_count=1)
    df["PCT_DOM_SEM_CONJUGE"] = percentual(df["DOM_SEM_CONJUGE"], df["DOM_CONJ_DEN"])

    # Composicao domiciliar: exclui unidade coletiva V01196.
    df["DOM_RESP_CONJ_SEM_FILHOS"] = df["V01191"]
    df["DOM_RESP_CONJ_FILHOS_AMBOS"] = df["V01192"]
    df["DOM_RESP_CONJ_FAMILIA_RECONSTITUIDA"] = df["V01193"]
    df["DOM_RESP_SEM_CONJ_COM_FILHOS"] = df["V01194"]
    df["DOM_OUTRAS_COMPOSICOES"] = df["V01195"]
    df["DOM_COLETIVO_COMP"] = df["V01196"]
    df["DOM_COMP_DEN"] = df[["V01191", "V01192", "V01193", "V01194", "V01195"]].sum(axis=1, min_count=1)
    df["PCT_RESP_SEM_CONJ_COM_FILHOS"] = percentual(df["DOM_RESP_SEM_CONJ_COM_FILHOS"], df["DOM_COMP_DEN"])

    # Tipo de unidade domestica: exclui coletivo V01213.
    tipos = {
        "UNIPESSOAL": "V01209",
        "NUCLEAR": "V01210",
        "ESTENDIDA": "V01211",
        "COMPOSTA": "V01212",
    }
    for nome, origem in tipos.items():
        df[f"DOM_{nome}"] = df[origem]
    df["DOM_COLETIVO_TIPO"] = df["V01213"]
    df["DOM_TIPO_DEN"] = df[list(tipos.values())].sum(axis=1, min_count=1)
    for nome in tipos:
        df[f"PCT_DOM_{nome}"] = percentual(df[f"DOM_{nome}"], df["DOM_TIPO_DEN"])

    df["DOM_UNIPESSOAL_RESP_H"] = df["V01214"]
    df["DOM_UNIPESSOAL_RESP_M"] = df["V01215"]
    df["DOM_ESTENDIDA_RESP_H"] = df["V01218"]
    df["DOM_ESTENDIDA_RESP_M"] = df["V01219"]
    df["PCT_UNIPESSOAL_RESP_FEM"] = percentual(
        df["DOM_UNIPESSOAL_RESP_M"],
        df[["V01214", "V01215"]].sum(axis=1, min_count=1),
    )
    df["PCT_ESTENDIDA_RESP_FEM"] = percentual(
        df["DOM_ESTENDIDA_RESP_M"],
        df[["V01218", "V01219"]].sum(axis=1, min_count=1),
    )
    return df


def resumo_municipal(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega contagens antes de calcular percentuais; nao calcula media de percentuais setoriais."""
    obrigatorias = {"COD_MUN", "MUNICIPIO", "CD_SETOR", "RESP_TOTAL", "RESP_HOMENS", "RESP_MULHERES", "RESP_60_MAIS", "DOM_CONJ_DEN", "DOM_SEM_CONJUGE", "DOM_COMP_DEN", "DOM_RESP_SEM_CONJ_COM_FILHOS", "DOM_TIPO_DEN", "DOM_UNIPESSOAL", "DOM_NUCLEAR", "DOM_ESTENDIDA", "DOM_COMPOSTA", "DOM_UNIPESSOAL_RESP_H", "DOM_UNIPESSOAL_RESP_M"}
    ausentes = sorted(obrigatorias - set(df.columns))
    if ausentes:
        raise ValueError(f"Colunas ausentes para resumo municipal: {ausentes}")

    agg = df.groupby(["COD_MUN", "MUNICIPIO"], as_index=False).agg(
        SETORES=("CD_SETOR", "count"),
        RESP_TOTAL=("RESP_TOTAL", "sum"),
        RESP_HOMENS=("RESP_HOMENS", "sum"),
        RESP_MULHERES=("RESP_MULHERES", "sum"),
        RESP_60_MAIS=("RESP_60_MAIS", "sum"),
        DOM_CONJ_DEN=("DOM_CONJ_DEN", "sum"),
        DOM_SEM_CONJUGE=("DOM_SEM_CONJUGE", "sum"),
        DOM_COMP_DEN=("DOM_COMP_DEN", "sum"),
        DOM_RESP_SEM_CONJ_COM_FILHOS=("DOM_RESP_SEM_CONJ_COM_FILHOS", "sum"),
        DOM_TIPO_DEN=("DOM_TIPO_DEN", "sum"),
        DOM_UNIPESSOAL=("DOM_UNIPESSOAL", "sum"),
        DOM_NUCLEAR=("DOM_NUCLEAR", "sum"),
        DOM_ESTENDIDA=("DOM_ESTENDIDA", "sum"),
        DOM_COMPOSTA=("DOM_COMPOSTA", "sum"),
        DOM_UNIPESSOAL_RESP_H=("DOM_UNIPESSOAL_RESP_H", "sum"),
        DOM_UNIPESSOAL_RESP_M=("DOM_UNIPESSOAL_RESP_M", "sum"),
    )
    agg["PCT_RESP_FEM"] = percentual(agg["RESP_MULHERES"], agg["RESP_HOMENS"] + agg["RESP_MULHERES"])
    agg["PCT_RESP_60_MAIS"] = percentual(agg["RESP_60_MAIS"], agg["RESP_TOTAL"])
    agg["PCT_DOM_SEM_CONJUGE"] = percentual(agg["DOM_SEM_CONJUGE"], agg["DOM_CONJ_DEN"])
    agg["PCT_RESP_SEM_CONJ_COM_FILHOS"] = percentual(agg["DOM_RESP_SEM_CONJ_COM_FILHOS"], agg["DOM_COMP_DEN"])
    for nome in ["UNIPESSOAL", "NUCLEAR", "ESTENDIDA", "COMPOSTA"]:
        agg[f"PCT_DOM_{nome}"] = percentual(agg[f"DOM_{nome}"], agg["DOM_TIPO_DEN"])
    agg["PCT_UNIPESSOAL_RESP_FEM"] = percentual(
        agg["DOM_UNIPESSOAL_RESP_M"], agg["DOM_UNIPESSOAL_RESP_H"] + agg["DOM_UNIPESSOAL_RESP_M"]
    )
    return agg
