# Arquitetura do pipeline

## 1. Separação de responsabilidades

### GitHub

Contém apenas artefatos versionáveis e necessários à reprodução lógica:

- código Python;
- notebook mestre;
- arquivos YAML de configuração;
- testes;
- documentação;
- manifestos de estrutura e exemplos pequenos.

### Google Drive

Contém artefatos de dados e execução:

- fontes brutas e cacheadas;
- Parquets e GeoPackages;
- CSV/XLSX derivados;
- mapas e gráficos;
- relatórios;
- logs e manifestos de cada execução.

## 2. Camadas do pipeline

### Camada A — fontes

Responsável por aquisição, cache, checksum e metadados das fontes do IBGE e demais fontes públicas.

### Camada B — validação estrutural

Confere dicionários, esquema, chaves territoriais, cobertura e compatibilidade com a configuração esperada.

### Camada C — base territorial canônica

Mantém `CD_SETOR` como chave canônica. Toda junção deve declarar cardinalidade esperada e produzir relatório de cobertura.

### Camada D — indicadores descritivos

Produz indicadores diretamente derivados das fontes, em três níveis sempre que aplicável:

- setor censitário;
- município;
- RMR.

### Camada E — análise espacial e multivariada

Inclui módulos independentes para:

- Moran global;
- LISA;
- correção FDR;
- sensibilidade da matriz espacial;
- dissimilaridade, isolamento e exposição;
- PCA;
- clustering e estabilidade de tipologias.

### Camada F — publicação

Gera tabelas, mapas e gráficos a partir de manifestos declarativos. O produto publicado nunca deve depender de edição manual de uma planilha intermediária.

### Camada G — proveniência

Cada execução registra:

- commit Git;
- configuração;
- versões do ambiente;
- fontes e checksums;
- parâmetros;
- etapas executadas;
- avisos e erros;
- lista de produtos.

## 3. Gates de qualidade

A execução deve interromper etapas dependentes quando houver falha crítica, incluindo:

- duplicidade de `CD_SETOR`;
- ausência de chaves obrigatórias;
- perda de cobertura acima da tolerância declarada;
- percentuais fora do intervalo válido;
- geometria inválida não tratada;
- incompatibilidade de esquema da fonte;
- denominadores impossíveis ou negativos.

## 4. Parâmetros metodológicos

Três classes devem ser explicitamente diferenciadas:

1. **definição proveniente da fonte**: conceito e variável do IBGE;
2. **procedimento fundamentado na literatura**: método ou estatística;
3. **parametrização operacional da pesquisa**: por exemplo, `k=6` em kNN ou limiar mínimo de casos.

Nenhuma parametrização operacional deve ser apresentada como regra universal da literatura.

## 5. Regra de promoção do legado

Scripts históricos são preservados como evidência de como os resultados foram obtidos. A refatoração para o núcleo ocorre apenas quando houver equivalência verificável ou diferença metodologicamente justificada.
