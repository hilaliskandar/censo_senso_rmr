# Código legado e rastreabilidade

Esta pasta é destinada a preservar, sem refatoração silenciosa, os scripts históricos que produziram etapas do diagnóstico da RMR.

## Scripts localizados no Drive

| Script | Drive | Estado |
|---|---|---|
| `read_parquet_min.py` | https://drive.google.com/file/d/1eKAvKiD_p0eoBmgiNSwdzzqouPEy6oTf/view | localizado; leitor Parquet/Snappy de baixo nível |
| `processa_composicao_domestica_rmr.py` | https://drive.google.com/file/d/1Y8gsw3j9RJr7ch4xIXAODDRfwidQr9-O/view | localizado; precisa parametrização |
| `processa_renda_rmr.py` | https://drive.google.com/file/d/1IL_EaW8CMN_zTj88q4lGbp6q9mAyy_j7/view | localizado; precisa parametrização |
| `cruza_renda_composicao_rmr.py` | https://drive.google.com/file/d/1tVHHv3YzfX-UE-BElg08SrRLCOFHNvQS/view | localizado; contém limiares hardcoded |

## Regra

O arquivo histórico, quando copiado para esta pasta, deve ser mantido como evidência e não alterado para fazê-lo parecer mais organizado ou atual. A versão refatorada deve ser implementada separadamente em `src/censo_rmr/`.

## Código ainda não localizado

Na auditoria de 2026-08-16 ainda não foram encontrados, como arquivos Python independentes indexados no Drive, os códigos responsáveis pela geração integral das fases avançadas de:

- FCU e sociodemografia consolidada;
- vulnerabilidade multidimensional;
- densidade ajustada;
- entorno;
- Moran/LISA e estabilidade local;
- segregação racial;
- PCA;
- k-means/Ward;
- estabilidade das tipologias.

Os respectivos produtos e relatórios existem. Eles deverão servir como referência para recuperação de código ou testes de regressão de uma reconstrução documentada.
