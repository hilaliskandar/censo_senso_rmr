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

## 3. Dependências upstream ainda não resolvidas

### Equidade e alfabetização

O produto histórico registra claramente as fórmulas substantivas e os resultados, mas o mapeamento completo das variáveis brutas IBGE `Vxxxxx` para os numeradores e denominadores padronizados ainda precisa ser recuperado de dicionário/script-fonte.

Por essa razão, `equidade.py` recebe contagens padronizadas e não tenta inferir códigos brutos.

### FCU

`SETOR_FCU` deriva da presença de `CD_FCU` na malha/classificação oficial do IBGE. A rotina de junção da camada FCU à malha canônica ainda deve ser incorporada ao pipeline de aquisição territorial.

### Densidade ajustada

O cálculo está definido:

- `DENS_ADJ = POP_TOTAL / AREA_DOM`;
- `DENS_CONV = POP_TOTAL / AREA_TOTAL`;
- `PCT_AREA_DOM = 100 * AREA_DOM / AREA_TOTAL`;
- `FATOR = DENS_ADJ / DENS_CONV`.

A reconstrução da camada `AREA_DOM` — área efetivamente domiciliada — ainda deve ser ligada à fonte geoespacial canônica usada no estudo histórico.

## 4. Parâmetros históricos recuperados

### Rendimento revisado 2026

- mediana `V06006` como medida principal;
- média `V06004` como apoio/desempate;
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

## 5. CI

O CI passou para a camada inicial e para os primeiros testes de regressão. Após a incorporação de módulos espaciais/multivariados, a execução mais recente falhou.

O diagnóstico detalhado depende de acesso aos logs do GitHub Actions por `gh`; como esse recurso não estava disponível no ambiente da rodada anterior, nenhuma causa foi presumida e os módulos avançados permanecem experimentais.

## 6. Critério para promoção

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
