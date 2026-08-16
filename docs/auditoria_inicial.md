# Auditoria inicial do pipeline RMR

Data da auditoria: 2026-08-16.

## Escopo

Auditoria preliminar das pastas `01_Inspecao_Dicionarios` a `07_Analise_Espacial` do Google Drive, com foco em rastrear entradas, scripts e produtos já existentes e identificar lacunas para reprodução integral.

## Estrutura observada no Drive

- `01_Inspecao_Dicionarios`: scripts Python, metadados JSON e arquivos de missingness dos primeiros blocos.
- `02_Recortes_RMR`: bases setoriais CSV e sucessivas bases GeoPackage consolidadas.
- `03_Tabelas_Indicadores`: tabelas, planilhas analíticas e produtos de Moran/LISA.
- `04_Mapas`: mapas e gráficos de demografia, renda, FCU, equidade, vulnerabilidade, densidade e entorno.
- `05_Relatorios`: relatórios por bloco, fichamentos metodológicos e metodologia consolidada.
- `06_Revisoes_Metodologicas`: revisão específica de rendimento em 2026.
- `07_Analise_Espacial`: produtos de segregação, PCA, tipologias e estabilidade, com bases espaciais derivadas e relatórios.

## Scripts explicitamente localizados

### `read_parquet_min.py`

Função: leitor mínimo de Parquet/Snappy usado nos protótipos iniciais.

Risco de manutenção: implementação de baixo nível dependente de `libsnappy.so.1` e de `parse_thrift`; deve ser substituída, quando possível, por `pyarrow`/`pandas` no ambiente Colab, mantendo o código histórico em `legacy/`.

### `processa_composicao_domestica_rmr.py`

Entrada principal:

- `Agregados_por_setores_parentesco_BR.parquet.bin`.

Dependência:

- `RMR_CENSO2022_DEMOGRAFIA_SETOR.csv`.

Saídas comprovadas:

- `RMR_CENSO2022_COMPOSICAO_DOMESTICA_SETOR.csv`;
- `RMR_CENSO2022_COMPOSICAO_DOMESTICA_MUNICIPIOS.csv`;
- `RMR_CENSO2022_COMPOSICAO_DOMESTICA_MISSING.csv`;
- `RMR_CENSO2022_COMPOSICAO_DOMESTICA_HETEROGENEIDADE.csv`;
- `RMR_CENSO2022_COMPOSICAO_DOMESTICA_EXTREMOS.csv`;
- `METADADOS_BLOCO2_COMPOSICAO_DOMESTICA.json`.

Problemas a refatorar:

- caminhos absolutos `/mnt/data/...`;
- municípios embutidos no script;
- limiares de cruzamentos demográficos embutidos numericamente;
- execução e gravação misturadas à lógica analítica.

### `processa_renda_rmr.py`

Saídas comprovadas:

- `RMR_CENSO2022_RENDA_RESPONSAVEL_SETOR.csv`;
- `RMR_CENSO2022_RENDA_RESPONSAVEL_MUNICIPIOS.csv`;
- `RMR_CENSO2022_RENDA_RESPONSAVEL_MISSING.csv`;
- `RMR_CENSO2022_RENDA_RESPONSAVEL_EXTREMOS.csv`;
- `METADADOS_BLOCO3_RENDA.json`.

Cautela metodológica já registrada no próprio script: a variável de rendimento médio de responsáveis com rendimento não é renda domiciliar per capita e não deve ser agregada diretamente ao município sem denominador compatível.

### `cruza_renda_composicao_rmr.py`

Dependências:

- renda setorial;
- composição doméstica setorial.

Saída comprovada:

- `RMR_CENSO2022_RENDA_CRUZAMENTOS_HABITACIONAIS.csv`.

Problema crítico de reprodutibilidade: vários limiares são números hardcoded provenientes de etapas anteriores. Esses valores devem passar a ser calculados ou lidos de um manifesto de parâmetros da mesma execução.

## Bases consolidadas observadas

Em `02_Recortes_RMR` há uma sequência evolutiva:

1. `RMR_CENSO2022_SETORES_CONSOLIDADO.gpkg`;
2. `..._COM_FCU.gpkg`;
3. `..._SOCIODEMOGRAFIA_FCU.gpkg`;
4. `..._VULNERABILIDADE.gpkg`;
5. `..._DENSIDADE_AJUSTADA.gpkg`;
6. `..._ENTORNO.gpkg`.

A sequência indica dependências incrementais. A versão refatorada deve evitar múltiplas bases canônicas concorrentes: cada etapa deve produzir uma camada derivada versionada, mas existir uma definição explícita da base canônica utilizada por cada produto.

## Produtos avançados observados

Em `07_Analise_Espacial/Produtos` foram localizados produtos de:

- entorno + Moran/LISA bivariado;
- segregação racial: dissimilaridade, isolamento e exposição;
- auditoria de redundância e PCA exploratória;
- tipologias territoriais por k-means e Ward;
- estabilidade e sensibilidade das tipologias.

Há também GeoPackages das fases 7 e 8.

## Lacuna atual

Na auditoria preliminar, os scripts correspondentes às etapas avançadas não foram localizados nas pastas consultadas. Portanto, esses produtos são tratados como **resultados existentes com código de geração ainda não auditado**, não como etapas plenamente reproduzíveis.

Antes de declarar o pipeline completo, é necessário recuperar esses códigos de outras pastas/logs ou reconstruí-los a partir da metodologia e dos produtos, com testes de regressão contra os resultados existentes.

## Grafo parcial comprovado

```text
IBGE / agregados setoriais
        |
        +--> demografia setorial
        |        |
        |        +--> composição doméstica
        |        |         |
        |        |         +--> cruzamentos com renda
        |        |
        |        +--> mapas demográficos
        |
        +--> renda de responsáveis
                 |
                 +--> tabelas municipais / missing / extremos
                 +--> cruzamentos habitacionais

bases setoriais + malha
        |
        +--> base consolidada
                 |
                 +--> FCU
                 +--> sociodemografia
                 +--> vulnerabilidade
                 +--> densidade ajustada
                 +--> entorno
                         |
                         +--> Moran/LISA
                         +--> PCA
                         +--> tipologias
                         +--> segregação
```

As setas da parte avançada indicam encadeamento inferido pela sucessão dos produtos e devem ser confirmadas na auditoria dos códigos.

## Critério de promoção para o núcleo do pipeline

Um módulo só deve sair de `legacy/` e entrar em `src/censo_rmr/` quando:

1. entradas e saídas forem explícitas;
2. caminhos forem configuráveis;
3. parâmetros estiverem fora do código;
4. houver validações de esquema e denominadores;
5. houver teste mínimo de regressão;
6. o produto for compatível com o resultado histórico ou a diferença estiver metodologicamente justificada.
