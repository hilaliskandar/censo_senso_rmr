# Censo Senso RMR

Pipeline reprodutível para tratamento, integração, análise territorial e produção de tabelas e mapas a partir do Censo Demográfico 2022 e de camadas territoriais associadas à Região Metropolitana do Recife (RMR).

O projeto separa **código e método computacional** de **dados e produtos volumosos**, preserva os resultados históricos já produzidos e permite reprocessamento controlado, regressão e auditoria antes de qualquer promoção de novos resultados.

> **Estado atual:** desenvolvimento ativo na branch `agent/pipeline-rmr-v0`. O PR permanece em `draft`. O núcleo inicial possui regressão estruturada; módulos espaciais, multivariados e algumas entradas geoespaciais ainda aguardam regressão integral e CI verde.

## 1. Objetivo

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

## 2. Arquitetura GitHub + Google Drive

### GitHub

O repositório concentra:

- código Python reutilizável;
- notebook mestre para Google Colab;
- configurações e parâmetros metodológicos;
- testes unitários e de regressão;
- manifestos de produtos;
- documentação de arquitetura, status e proveniência;
- código histórico preservado em `legacy/`, quando incorporado.

### Google Drive

O Drive concentra:

- fontes brutas e cache de arquivos oficiais;
- GeoPackages, Parquets, CSVs e planilhas analíticas;
- produtos históricos usados como referência de regressão;
- mapas, tabelas, gráficos e relatórios;
- logs e manifestos de execução.

A pasta principal de trabalho é `Censo_2022_Setores_RMR`. A área `00_Pipeline` isola cache, regressão e logs dos produtos históricos.

```text
Censo_2022_Setores_RMR/
  00_Pipeline/
    01_Cache_IBGE/
    02_Regressao/
    03_Logs_Manifestos/
```

Nenhuma execução do pipeline deve sobrescrever produtos históricos diretamente.

## 3. Instalação

### Ambiente local

Requer Python 3.11+.

```bash
git clone https://github.com/hilaliskandar/censo_senso_rmr.git
cd censo_senso_rmr
git switch agent/pipeline-rmr-v0
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
pytest -q
```

No Windows, ative o ambiente virtual pelo comando apropriado ao shell utilizado.

### Google Colab

O notebook mestre está em:

```text
notebooks/RMR_CENSO2022_PIPELINE_MASTER.ipynb
```

A lógica analítica não deve ser duplicada no notebook. O Colab atua como orquestrador do pacote `censo_rmr` e das configurações YAML.

## 4. Modos de execução

O notebook mestre foi desenhado com dois modos iniciais:

- `AUDITAR`: verifica contratos, fontes e produtos existentes sem recalcular nem sobrescrever resultados;
- `REPROCESSAR_EM_STAGING`: recalcula etapas habilitadas e grava somente em área de staging/regressão.

**Não existe, nesta versão, promoção automática para produtos oficiais.** A promoção será implementada somente depois que os gates de qualidade, regressão e CI estiverem integralmente satisfeitos.

## 5. Estrutura do repositório

```text
.github/                 workflows de CI
config/                  fontes, caminhos, parâmetros e manifestos
  analise_multivariada.yaml
  analise_espacial.yaml
  habitacao_entorno.yaml
  mapas.yaml
  tabelas.yaml
docs/                    arquitetura, auditoria, status e proveniência
legacy/                  código histórico preservado
notebooks/               notebook mestre para Colab
src/censo_rmr/            pacote Python do pipeline
tests/                   testes unitários e de regressão
pyproject.toml
requirements.txt
README.md
```

## 6. Módulos

### Núcleo operacional com regressão estruturada

- aquisição e leitura controlada de CSV/ZIP;
- normalização de chaves territoriais;
- contratos de entrada e saída;
- demografia;
- composição doméstica;
- rendimento inicial;
- rendimento revisado 2026;
- cruzamentos iniciais;
- escrita em staging;
- comparação automática com produtos históricos.

### Cálculo codificado; regressão integral ainda pendente

- habitação;
- entorno urbano;
- sexo, cor ou raça, alfabetização e FCU;
- densidade convencional e ajustada;
- PCA por domínio;
- tipologias territoriais e estabilidade;
- Moran global e LISA;
- LISA bivariado e sensibilidade da matriz espacial;
- segregação racial;
- cartografia parametrizada;
- tabelas editoriais.

O status detalhado de cada bloco é mantido em [`docs/STATUS_VALIDACAO.md`](docs/STATUS_VALIDACAO.md).

## 7. Decisões metodológicas importantes

### Rendimento revisado 2026

A divulgação atualizada é tratada em camada própria:

- `V06006`: mediana do rendimento nominal mensal das pessoas responsáveis com rendimento — medida principal de posição;
- `V06004`: média — medida auxiliar e critério de desempate quando necessário;
- classificação estrita abaixo de R$ 1.212 e quintil operacional são procedimentos distintos;
- a mediana setorial não é interpretada como renda domiciliar ou linha de pobreza.

### Habitação e entorno

Os indicadores de precariedade habitacional permanecem por dimensão, sem criação automática de um índice único. A classificação do entorno reproduz a lógica histórica de limiares P80 da RMR e pode também receber limiares explícitos para regressão.

Valores suprimidos pelo IBGE (`X`) permanecem ausentes e nunca são convertidos silenciosamente em zero.

### PCA e tipologias

A arquitetura multivariada preserva a separação conceitual dos domínios. A PCA não atribui, por si só, peso normativo às variáveis.

Parâmetros históricos atualmente registrados:

- `k = 4` como solução selecionada;
- comparação K-Means x Ward;
- avaliação de `k = 4..8`;
- z-score como padronização principal;
- percentis, leave-one-variable-out e leave-one-domain-out como sensibilidade;
- 30 bootstraps de 80%;
- alinhamento de rótulos por algoritmo Húngaro;
- persistência estrutural como medida principal de robustez.

### Análise espacial

São mantidas duas camadas distintas:

1. **Fase exploratória histórica**: queen, 999 permutações, `p < 0,05`, sem correção por múltiplas comparações;
2. **camada consolidada**: queen principal, kNN simétrico com 6 vizinhos como sensibilidade e possibilidade de FDR de Benjamini-Hochberg.

`kNN6` é uma parametrização operacional do estudo, não uma constante universal derivada da literatura.

### Segregação

São mantidos separadamente:

- composição racial;
- dissimilaridade;
- isolamento;
- exposição;
- autocorrelação espacial da composição.

A base setorial de rendimento atualmente disponível não é usada para declarar segregação econômica por grupos de renda, pois não contém distribuição de renda suficiente para esse cálculo.

## 8. Cartografia

Os scripts municipais históricos revelaram um padrão comum, abstraído em um gerador parametrizado. O núcleo cartográfico municipal é composto por:

1. população por setor;
2. precariedade material;
3. precariedade do entorno;
4. Favelas e Comunidades Urbanas (FCU);
5. não alfabetização de 15 anos ou mais;
6. rendimento mediano da pessoa responsável;
7. densidade ajustada.

Os mapas recebem a base analítica consolidada, validam chaves e registram auditoria/metadados. Eles não recalculam indicadores.

## 9. Tabelas

A camada editorial é independente da camada analítica. Ela seleciona, ordena e formata resultados já calculados, evitando reconstruir percentuais ou agregações com regras diferentes na publicação.

## 10. Convenções de dados

1. `CD_SETOR` é sempre preservado como texto;
2. aliases históricos, como `CD_setor`, são normalizados explicitamente;
3. ausência não é zero;
4. valores `X` do IBGE permanecem ausentes;
5. percentuais só podem ser agregados novamente a partir de numerador e denominador quando esses componentes estiverem disponíveis;
6. variáveis de equidade (sexo, raça/cor) não entram automaticamente em escores de privação;
7. FCU é condição territorial transversal, não sinônimo automático de precariedade;
8. densidade é contexto territorial, não medida de vulnerabilidade;
9. decisões específicas da RMR devem ser distinguidas de recomendações derivadas da literatura.

## 11. Reprodutibilidade e QA

Cada etapa deve registrar, conforme aplicável:

- fonte oficial;
- versão/data da fonte;
- universo;
- fórmula;
- numerador e denominador;
- tratamento de ausência e sigilo;
- parâmetros metodológicos;
- chave espacial;
- produto gerado;
- versão do código;
- resultado dos testes de regressão.

Um módulo só é promovível quando cumprir simultaneamente:

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

## 12. Status do CI

O checkout, a configuração do Python e a instalação do pacote estão funcionando no GitHub Actions. A execução mais recente falhou especificamente no passo `pytest -q` depois da incorporação dos módulos espaciais e multivariados.

O traceback detalhado ainda precisa ser inspecionado antes de qualquer correção. Portanto, nenhuma causa foi presumida e os módulos avançados permanecem experimentais.

## 13. Próximas etapas

1. recuperar completamente o mapeamento das variáveis brutas IBGE para sexo, cor ou raça e alfabetização;
2. incorporar a junção oficial de FCU à malha canônica;
3. recuperar e integrar a camada de área efetivamente domiciliada usada na densidade ajustada;
4. ampliar regressões dos blocos temáticos contra produtos históricos completos;
5. diagnosticar e corrigir o `pytest` no Actions;
6. executar o pipeline integral em `REPROCESSAR_EM_STAGING` no Colab;
7. comparar novos produtos e produtos históricos;
8. desenhar somente então a etapa explícita de promoção para produtos oficiais.

## 14. Branch de desenvolvimento

```text
agent/pipeline-rmr-v0
```

PR associado: `#1`, mantido em **draft** até que os módulos avançados tenham regressão suficiente e o CI volte a ficar verde.
