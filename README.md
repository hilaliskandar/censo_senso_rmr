# Censo Senso RMR

Pipeline reprodutível para tratamento, integração, análise territorial e produção de tabelas e mapas a partir do Censo Demográfico 2022 e de camadas territoriais associadas à Região Metropolitana do Recife (RMR).

O projeto foi estruturado para separar claramente **código e método computacional** de **dados e produtos volumosos**, preservar os resultados históricos já produzidos e permitir reprocessamento controlado, regressão e auditoria antes de qualquer promoção de novos resultados.

## Objetivo

Reproduzir de forma auditável o fluxo:

```text
fontes oficiais
  -> cache versionado
  -> leitura e validação de esquema
  -> recorte RMR
  -> indicadores setoriais
  -> QA
  -> regressão contra produtos históricos
  -> base setorial integrada
  -> análises espaciais e multivariadas
  -> tabelas e mapas
  -> manifestos e logs
```

A interpretação substantiva dos resultados permanece separada do processamento automatizado.

## Arquitetura GitHub + Google Drive

### GitHub

O repositório concentra:

- código Python reutilizável;
- notebook mestre para Google Colab;
- configurações e parâmetros metodológicos;
- testes unitários e de regressão;
- manifestos de produtos;
- documentação de arquitetura e proveniência;
- scripts históricos preservados em `legacy/`, quando incorporados.

### Google Drive

O Drive concentra:

- fontes brutas e cache de arquivos oficiais;
- GeoPackages, Parquets, CSVs e planilhas analíticas;
- produtos históricos usados como referência de regressão;
- mapas, tabelas, gráficos e relatórios;
- logs e manifestos de execução.

A pasta principal de trabalho é `Censo_2022_Setores_RMR`. A área `00_Pipeline` foi criada para separar cache e reprocessamentos dos produtos históricos.

## Modos de execução

O notebook mestre foi desenhado com dois modos iniciais:

- `AUDITAR`: verifica contratos, fontes e produtos existentes sem recalcular nem sobrescrever resultados;
- `REPROCESSAR_EM_STAGING`: recalcula etapas habilitadas e grava somente em área de staging/regressão.

**Não existe, nesta versão, promoção automática para produtos oficiais.** A promoção deverá ser uma etapa posterior, condicionada à aprovação dos gates de qualidade e regressão.

## Estrutura do repositório

```text
.github/                 workflows de CI
config/                  fontes, caminhos, parâmetros, mapas e tabelas
  analise_multivariada.yaml
  analise_espacial.yaml
  habitacao_entorno.yaml
  mapas.yaml
  tabelas.yaml
docs/                    arquitetura, auditoria e proveniência
legacy/                  código histórico preservado
notebooks/               notebook mestre para Colab
src/censo_rmr/            pacote Python do pipeline
tests/                   testes unitários e de regressão
pyproject.toml
requirements.txt
README.md
```

## Módulos do pacote

Os módulos atualmente incorporados incluem:

- aquisição e leitura controlada das fontes oficiais;
- normalização de CSV e chaves territoriais;
- contratos de entrada e saída;
- demografia;
- composição doméstica;
- rendimento inicial;
- rendimento revisado 2026;
- cruzamentos setoriais;
- habitação e precariedade domiciliar;
- entorno urbano;
- PCA por domínio;
- tipologias territoriais e estabilidade;
- Moran global e LISA;
- LISA bivariado e sensibilidade de matriz espacial;
- segregação racial;
- cartografia municipal parametrizada;
- tabelas editoriais;
- regressão contra produtos históricos;
- geração de manifestos de execução.

## Estado de validação

### Módulos com regressão histórica já estruturada

Os primeiros blocos possuem código reconstruído/refatorado e casos-âncora extraídos dos produtos históricos:

- demografia;
- composição doméstica;
- rendimento;
- cruzamentos iniciais.

O pipeline preserva diferenças relevantes entre os produtos históricos e as revisões posteriores, especialmente no tratamento do rendimento.

### Rendimento revisado 2026

A divulgação atualizada é tratada em camada própria:

- `V06006`: mediana do rendimento nominal mensal das pessoas responsáveis com rendimento — medida principal de posição;
- `V06004`: média — medida auxiliar e critério de desempate quando necessário;
- classificação estrita abaixo de R$ 1.212 e quintil operacional são mantidos como procedimentos diferentes;
- a mediana setorial não é interpretada como renda domiciliar ou linha de pobreza.

### Habitação e entorno

Os indicadores de precariedade habitacional são mantidos por dimensão, sem criação automática de um índice único. A classificação do entorno reproduz a lógica histórica de limiares P80 da RMR e permite também receber limiares explícitos para testes de regressão.

Valores suprimidos pelo IBGE (`X`) permanecem ausentes e nunca são convertidos silenciosamente em zero.

### PCA e tipologias

A arquitetura multivariada preserva a separação conceitual dos domínios. A PCA não atribui, por si só, peso normativo às variáveis.

A solução histórica de tipologias registra:

- `k = 4` como solução selecionada na Fase 7;
- comparação K-Means x Ward;
- testes de `k = 4..8`;
- z-score como padronização principal;
- percentis, leave-one-variable-out e leave-one-domain-out como testes de sensibilidade;
- bootstrap com 30 amostras de 80%;
- alinhamento de rótulos por algoritmo Húngaro;
- persistência estrutural como medida principal de robustez.

Parâmetros recuperados dos produtos históricos são mantidos em configuração, não escondidos no código.

### Análise espacial

A implementação distingue duas camadas:

1. **Fase exploratória histórica**: queen, 999 permutações, `p < 0,05`, sem correção por múltiplas comparações;
2. **camada consolidada**: queen como matriz principal, kNN simétrico com 6 vizinhos como sensibilidade e possibilidade de correção FDR de Benjamini-Hochberg.

A escolha de `kNN6` é tratada como parametrização operacional do estudo, não como constante universal da literatura.

### Segregação

São mantidos separadamente:

- composição racial;
- dissimilaridade;
- isolamento;
- exposição;
- autocorrelação espacial da composição.

A base setorial de rendimento atualmente disponível não é usada para declarar segregação econômica por grupos de renda, pois não contém a distribuição necessária para esse cálculo.

## Cartografia

Os scripts municipais históricos mostraram um padrão comum, agora abstraído em um gerador parametrizado. O núcleo cartográfico municipal é composto por:

1. população por setor;
2. precariedade material;
3. precariedade do entorno;
4. Favelas e Comunidades Urbanas (FCU);
5. não alfabetização de 15 anos ou mais;
6. rendimento mediano da pessoa responsável;
7. densidade ajustada.

Os mapas não recalculam indicadores: recebem a base analítica consolidada, validam as chaves e registram metadados/auditoria ao lado do produto.

## Tabelas

A camada editorial é independente da camada analítica. Ela seleciona, ordena e formata resultados já calculados, evitando que percentuais ou agregações sejam reconstruídos de forma diferente na etapa de publicação.

## Princípios de reprodutibilidade

1. nenhuma variável oficial é inferida silenciosamente;
2. toda transformação deve registrar fonte, universo, denominador, fórmula e ressalvas;
3. `CD_SETOR` é preservado como texto;
4. aliases históricos, como `CD_setor`, são normalizados explicitamente;
5. ausência não é zero;
6. parâmetros metodológicos ficam em configuração sempre que possível;
7. produtos analíticos só avançam depois de gates de QA;
8. resultados novos são comparados aos históricos antes de qualquer promoção;
9. cada execução registra versão do código, parâmetros, fontes e produtos;
10. mapas e tabelas devem ser regeneráveis a partir das bases canônicas;
11. decisões específicas da RMR são distinguidas de recomendações derivadas da literatura;
12. resultados exploratórios não são promovidos semanticamente a classificações normativas.

## Status do CI

O CI havia passado para a camada inicial do pipeline e para os primeiros testes de regressão. Após a incorporação dos módulos espaciais e multivariados, a execução mais recente apresentou falha.

O diagnóstico do log detalhado ainda está pendente porque o ambiente utilizado na última rodada não dispunha do GitHub CLI (`gh`), necessário para inspeção segura dos logs do GitHub Actions. Portanto, os módulos avançados permanecem **experimentais** até que essa falha seja diagnosticada e os testes voltem a ficar verdes.

## Próximas etapas

1. concluir os módulos upstream de FCU, sexo, cor ou raça e alfabetização;
2. concluir a reconstrução da densidade convencional e ajustada;
3. integrar esses blocos à base setorial canônica;
4. ampliar os testes de regressão contra os produtos históricos;
5. diagnosticar e corrigir o CI dos módulos avançados;
6. executar o pipeline integral em `REPROCESSAR_EM_STAGING` no Colab;
7. comparar integralmente novos produtos e produtos históricos;
8. somente então desenhar a etapa explícita de promoção para produtos oficiais.

## Situação da branch

O desenvolvimento atual ocorre em:

```text
agent/pipeline-rmr-v0
```

O pull request associado permanece em **draft** enquanto houver módulos avançados sem CI validado e etapas upstream ainda não reconstruídas integralmente.
