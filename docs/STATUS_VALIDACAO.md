# Status de validação do pipeline

Este documento separa o que já pode ser tratado como núcleo operacional do que ainda permanece em reconstrução, regressão ou validação.

## 1. Núcleo operacional com regressão estruturada

- aquisição/leitura controlada de CSV e ZIP;
- normalização de chaves territoriais;
- contratos de entrada/saída;
- demografia;
- composição doméstica;
- rendimento inicial;
- rendimento revisado 2026;
- cruzamentos iniciais;
- escrita de staging;
- comparação automática com produtos históricos.

Esses blocos já possuem testes unitários e/ou casos-âncora extraídos de produtos históricos.

## 2. Núcleo operacional com cálculo codificado, regressão integral ainda pendente

- habitação;
- entorno;
- sexo/cor ou raça/alfabetização/FCU;
- densidade convencional e ajustada;
- PCA por domínio;
- tipologias territoriais;
- estabilidade das tipologias;
- Moran global e LISA;
- LISA bivariado;
- segregação racial;
- cartografia;
- tabelas editoriais.

O fato de o cálculo estar codificado não equivale a validação integral. Para promoção metodológica, cada bloco deve ser confrontado com os produtos históricos completos ou com fonte oficial independente.

## 3. Fontes upstream verificadas

As seguintes fontes oficiais já foram verificadas e registradas em `config/fontes.yaml`:

- dicionário geral dos Agregados por Setores Censitários, atualização de 20/05/2026;
- agregados de demografia;
- agregados de parentesco/composição doméstica;
- agregados de alfabetização;
- agregados de cor ou raça;
- malha de setores de Pernambuco em GeoPackage, com atributos territoriais e `CD_FCU`;
- agregados de rendimento do responsável, atualização de 08/05/2026;
- dicionário específico de rendimento do responsável, atualização de 08/05/2026.

A presença de uma fonte verificada no manifesto não significa que todos os seus campos já foram mapeados e regressados.

## 4. Dependências upstream ainda não resolvidas

### Equidade e alfabetização

As fontes oficiais e os produtos históricos estão identificados. O produto histórico registra claramente as fórmulas substantivas e os resultados, mas o mapeamento completo das variáveis brutas IBGE `Vxxxxx` para todos os numeradores e denominadores padronizados ainda precisa ser extraído do dicionário oficial de 20/05/2026.

Por essa razão, `equidade.py` recebe contagens padronizadas e **não tenta inferir códigos brutos**.

A regra de trabalho é: somente depois do mapeamento documental `Vxxxxx -> conceito -> universo -> campo padronizado` a camada de aquisição poderá alimentar automaticamente esse módulo.

### FCU

`SETOR_FCU` deriva da presença de `CD_FCU` na malha oficial de setores censitários do IBGE. A fonte geoespacial de Pernambuco e a regra substantiva já estão verificadas.

Ainda falta incorporar ao pipeline de aquisição territorial a rotina explícita de:

1. leitura da malha canônica;
2. dissolução/controle de duplicatas por `CD_SETOR` quando necessário;
3. preservação de `CD_FCU`/`NM_FCU`;
4. derivação de `SETOR_FCU`;
5. auditoria da cobertura da junção com a base temática.

FCU permanece classificação territorial transversal, não sinônimo automático de precariedade.

### Densidade ajustada

O cálculo está definido:

- `DENS_ADJ = POP_TOTAL / AREA_DOM`;
- `DENS_CONV = POP_TOTAL / AREA_TOTAL`;
- `PCT_AREA_DOM = 100 * AREA_DOM / AREA_TOTAL`;
- `FATOR = DENS_ADJ / DENS_CONV`.

A reconstrução da camada `AREA_DOM` — área efetivamente domiciliada — ainda deve ser ligada à fonte geoespacial canônica usada no estudo histórico. O módulo de cálculo não deve inventar `AREA_DOM` a partir da área total do setor.

## 5. Parâmetros históricos recuperados

### Rendimento revisado 2026

- mediana `V06006` como medida principal;
- média `V06004` como apoio/desempate;
- variância `V06005` para heterogeneidade relativa;
- classificação estrita abaixo de R$ 1.212 separada do quintil operacional;
- ausência de interpretação como renda domiciliar ou linha de pobreza.

### Entorno

- seis dimensões centrais;
- P80 regional por dimensão;
- 0-1 dimensões altas: baixa ou não identificada;
- 2: moderada;
- 3 ou mais: alta.

### Tipologias

- solução histórica `k=4`;
- K-Means com `n_init=50`;
- comparação com Ward;
- avaliação de `k=4..8`;
- bootstrap: 30 amostras de 80%;
- alinhamento Húngaro;
- robusta: persistência estrutural >= 0,80;
- intermediária: >= 0,60 e < 0,80;
- instável: < 0,60.

### Análise espacial

- queen como matriz principal;
- 999 permutações;
- kNN simétrico com 6 vizinhos como sensibilidade;
- FDR como camada consolidada, sem apagar a saída exploratória histórica sem correção.

## 6. CI

O GitHub Actions confirma que:

- checkout passa;
- setup do Python passa;
- instalação `pip install -e . pytest` passa;
- a falha observada ocorre no passo `pytest -q`.

O traceback detalhado ainda precisa ser inspecionado antes de qualquer correção. Nenhuma causa será presumida apenas a partir do nome do teste ou do último módulo alterado.

A branch permanece em desenvolvimento e o PR permanece em `draft` enquanto o CI não voltar a ficar verde.

## 7. Critério para promoção

Um módulo só deve ser considerado promovível quando cumprir simultaneamente:

1. fonte e universo documentados;
2. fórmula e denominador explícitos;
3. tratamento de ausências/supressões definido;
4. teste unitário;
5. regressão histórica ou validação independente;
6. contrato de entrada e saída;
7. execução em staging sem sobrescrita;
8. CI verde;
9. manifesto de execução gerado;
10. revisão metodológica humana concluída.
