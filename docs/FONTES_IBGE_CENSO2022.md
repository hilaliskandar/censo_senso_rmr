# Fontes oficiais do IBGE — Censo Demográfico 2022 — pipeline RMR

## 1. Regra de autoridade

A fonte primária do pipeline é o IBGE. Nomes de arquivos, intervalos de variáveis, universos e revisões devem ser registrados antes da execução. Produtos históricos do projeto servem como referência de regressão, não como substitutos dos dicionários oficiais.

Valores publicados como `X` ou outros valores não numéricos são ausentes/suprimidos e nunca são convertidos em zero.

## 2. Árvore principal — Agregados por Setores Censitários

Raiz:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/

Dicionário geral:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/dicionario_de_dados_agregados_por_setores_censitarios_20260520.xlsx

Nota metodológica n. 06:

https://biblioteca.ibge.gov.br/visualizacao/livros/liv102136.pdf

A Nota n. 06 organiza os arquivos temáticos nos seguintes intervalos relevantes ao pipeline:

| Tema | Intervalo |
|---|---|
| Características do domicílio — parte 1 | V00001–V00089 |
| Características do domicílio — parte 2 | V00090–V00495 |
| Características do domicílio — parte 3 | V00496–V00643 |
| Alfabetização | V00644–V01005 |
| Demografia | V01006–V01041 |
| Parentesco | V01042–V01223 |
| Cor ou raça | V01317–V01411 |

Arquivos CSV usados no núcleo atual:

- `Agregados_por_setores_basico_BR_20260520.zip`;
- `Agregados_por_setores_demografia_BR.zip`;
- `Agregados_por_setores_parentesco_BR.zip`;
- `Agregados_por_setores_alfabetizacao_BR.zip`;
- `Agregados_por_setores_cor_ou_raca_BR.zip`;
- `Agregados_por_setores_caracteristicas_domicilio1_BR.zip`;
- `Agregados_por_setores_caracteristicas_domicilio2_BR_20250417.zip`;
- `Agregados_por_setores_caracteristicas_domicilio3_BR_20250417.zip`.

## 3. Revisões que o pipeline deve impor

O IBGE informa que em 17/04/2025 foram corrigidas variáveis anteriormente zeradas nos arquivos de características do domicílio 2 e 3 e foram realizados ajustes no arquivo básico. Entre as variáveis corrigidas está `V00236`, utilizada diretamente no indicador de banheiro compartilhado do estudo RMR.

Por isso, o pipeline rejeita versões anteriores dos arquivos de características do domicílio 2 e 3 e exige os marcadores `20250417` nas URLs configuradas. Para o arquivo básico, a versão adotada é `20260520`. A função `validar_versoes_minimas` impede que arquivos substituídos sejam reutilizados silenciosamente.

## 4. Malha de Setores Censitários com atributos

Página oficial:

https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html

Malha de Pernambuco em GeoPackage:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/UF/PE/PE_setores_CD2022.gpkg

Dicionário da malha:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/Dicionario_de_dados_malha_agregados.xlsx

A página oficial confirma, entre outros, os campos:

- `CD_SETOR`: geocódigo do setor censitário;
- `AREA_KM2`: área do setor em km²;
- `CD_FCU`: código da Favela e Comunidade Urbana;
- `NM_FCU`: nome da Favela e Comunidade Urbana.

`SETOR_FCU` é uma derivação do projeto: 1 quando `CD_FCU` está preenchido e 0 quando não está. FCU é atributo territorial transversal e não um escore de precariedade.

## 5. Área territorial efetivamente domiciliada

A própria página oficial da Malha publica a tabela:

**Área territorial efetivamente domiciliada e densidade demográfica ajustada dos Setores Censitários** — formatos XLSX e ODS — e um leia-me metodológico específico.

Portanto, `AREA_DOM` não deve ser reconstruída por hipótese local quando essa publicação estiver disponível. O pipeline deve ingerir a tabela oficial, registrar o arquivo/checksum e comparar a densidade oficial com a recomposição a partir de população e área.

O link binário direto do XLSX ainda precisa ser materializado no ambiente Colab/portal; ele não será inferido por convenção de nome.

## 6. Entorno dos domicílios

O entorno possui árvore própria, fora da pasta principal:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_Caracteristicas_urbanisticas_do_entorno_dos_domicilios/

Dicionários:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_Caracteristicas_urbanisticas_do_entorno_dos_domicilios/dicionarios_de_dados_entorno.zip

A divulgação distingue três universos:

| Universo | Intervalo |
|---|---|
| Domicílios | V05000–V05034 |
| Moradores | V05200–V05234 |
| Faces | V05400–V05434 |

Esses universos não são intercambiáveis. O estudo histórico da RMR utiliza preferencialmente o arquivo de moradores; cada numerador e denominador deverá ser conferido no dicionário específico antes da execução automática.

## 7. Rendimento do responsável

Árvore própria:

https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/

Versão atual adotada: 08/05/2026.

Arquivos principais:

- `Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip`;
- `Agregados_por_setores_renda_responsavel_BR_20260508_xlsx.zip`;
- `dicionario_de_dados_renda_responsavel_20260508.xlsx`.

No pipeline:

- `V06004`: média do rendimento nominal mensal das pessoas responsáveis com rendimento;
- `V06005`: variância;
- `V06006`: mediana.

Essas medidas não representam renda domiciliar, renda familiar ou renda domiciliar per capita.

## 8. Estado do mapeamento fino

`config/mapeamento_ibge.yaml` contém o mapeamento operacional necessário aos blocos já reconstruídos.

Há três níveis distintos de maturidade:

1. **confirmado em página/documentação oficial** — por exemplo `CD_SETOR`, `AREA_KM2`, `CD_FCU`, `NM_FCU` e intervalos temáticos;
2. **operacionalmente conferido, validação binária do XLSX pendente** — códigos finos usados em alfabetização e cor ou raça neste ambiente;
3. **não executável até o dicionário oficial** — mapeamento fino do entorno.

Execução em staging pode trabalhar com o nível 2, desde que o status seja registrado. Promoção para produto oficial exige eliminação das pendências documentais.

## 9. Casos-âncora de regressão

`config/ancoras_regressao.yaml` registra setores reais já entregues nos produtos históricos de equidade/FCU e densidade ajustada. O módulo `censo_rmr.ancoras` compara a nova execução com esses valores usando tolerância explícita e falha quando:

- um setor-âncora desaparece;
- uma chave setorial aparece duplicada;
- um campo esperado não existe;
- um valor diverge além da tolerância configurada.

As âncoras são um gate de regressão rápido. Elas não substituem a comparação integral dos 7.208 setores de equidade/FCU e dos 7.004 setores da base histórica de densidade.

## 10. Política de revisão

O pipeline deve preservar:

- URL da fonte;
- nome e versão do arquivo;
- data de aquisição;
- tamanho;
- SHA-256;
- dicionário usado;
- revisão/correção relevante do IBGE;
- universo estatístico;
- chave territorial;
- tratamento das supressões.

Uma versão nova do IBGE não substitui silenciosamente a anterior. Mudança de esquema ou de valores exige nova regressão e novo manifesto de execução.
