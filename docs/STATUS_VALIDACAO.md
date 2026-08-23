# Status de validação do pipeline

Este documento separa o que já pode ser tratado como núcleo operacional do que ainda permanece em reconstrução, regressão ou validação.

## 1. Núcleo operacional com regressão estruturada

- aquisição/leitura controlada de CSV e ZIP;
- cache com SHA-256 e reutilização controlada;
- validação mínima de versões oficiais;
- normalização de chaves territoriais;
- contratos de entrada/saída;
- demografia;
- composição doméstica;
- rendimento inicial;
- rendimento revisado 2026;
- cruzamentos iniciais;
- escrita de staging;
- comparação automática com produtos históricos dos blocos iniciais.

## 2. Integrado ao staging, regressão integral ainda pendente

### Equidade, alfabetização e FCU

O bloco está incorporado ao modo `REPROCESSAR_EM_STAGING` e executa:

1. aquisição dos agregados oficiais de demografia, cor ou raça e alfabetização;
2. leitura da malha oficial de Pernambuco;
3. recorte para os 14 municípios da RMR;
4. recomposição das contagens canônicas de alfabetização no próprio universo temático;
5. cálculo dos indicadores de sexo, cor ou raça e alfabetização;
6. incorporação de `CD_FCU`, `NM_FCU` e `SETOR_FCU`;
7. gravação do setorial em staging;
8. validação dos casos-âncora históricos;
9. registro de auditoria, cobertura e proveniência.

Ainda falta a regressão integral contra a planilha histórica de 7.208 setores e a validação binária do dicionário XLSX para os códigos finos atualmente classificados como operacionalmente conferidos.

### Densidade ajustada

A interface de staging está implementada. Quando a fonte estiver completamente configurada, ela:

1. lê `AREA_DOM` da publicação oficial do IBGE;
2. usa `AREA_KM2` da malha como `AREA_TOTAL`;
3. incorpora `POP_TOTAL` da demografia;
4. calcula `DENS_ADJ`, `DENS_CONV`, `PCT_AREA_DOM` e `FATOR`;
5. compara a densidade recomputada com `DENS_ADJ_OFICIAL`, quando esse campo existir;
6. executa os casos-âncora históricos;
7. registra cobertura da junção e divergências.

A execução real permanece `bloqueado_por_fonte` enquanto a URL binária e os nomes exatos das colunas da tabela oficial de área efetivamente domiciliada não estiverem confirmados em `config/fontes.yaml`. O pipeline não infere esses elementos por convenção.

## 3. Cálculo codificado, integração/regressão ainda pendente

- habitação;
- entorno;
- PCA por domínio;
- tipologias territoriais e estabilidade;
- Moran global, LISA e LISA bivariado;
- segregação racial;
- cartografia;
- tabelas editoriais.

O fato de o cálculo estar codificado não equivale a validação integral. Para promoção metodológica, cada bloco deve ser confrontado com os produtos históricos completos ou com fonte oficial independente.

## 4. Fontes upstream verificadas

As seguintes fontes oficiais estão registradas em `config/fontes.yaml`:

- dicionário geral dos Agregados por Setores Censitários;
- Nota metodológica n. 06 dos Agregados por Setores Censitários;
- agregados de demografia, parentesco, alfabetização e cor ou raça;
- três partes de características do domicílio, usando as versões corrigidas quando datadas;
- malha definitiva de setores de Pernambuco, com `AREA_KM2`, `CD_FCU` e `NM_FCU`;
- publicação oficial de área territorial efetivamente domiciliada e densidade demográfica ajustada;
- três universos do entorno: domicílios, moradores e faces, com dicionário próprio;
- rendimento do responsável e seu dicionário específico, atualização de 08/05/2026.

A Nota metodológica n. 06 confirma os intervalos de variáveis por tema: alfabetização `V00644-V01005`, demografia `V01006-V01041`, parentesco `V01042-V01223`, cor ou raça `V01317-V01411`, entorno-domicílios `V05000-V05034`, entorno-moradores `V05200-V05234` e entorno-faces `V05400-V05434`.

## 5. Controle de versões oficiais

O pipeline não aceita silenciosamente versões antigas: ele produz erro explícito quando uma fonte configurada não atende à revisão mínima auditada.

Atualmente são exigidos:

- `basico`: marcador `20260520`;
- `caracteristicas_domicilio_2`: marcador `20250417`;
- `caracteristicas_domicilio_3`: marcador `20250417`.

Esse controle é relevante porque o IBGE publicou correções materiais nos arquivos domiciliares, inclusive em variável usada diretamente no estudo.

## 6. Equidade, alfabetização e FCU

O mapeamento `Vxxxxx -> conceito -> campo canônico` necessário ao núcleo atual está em `config/mapeamento_ibge.yaml` e incorporado a `equidade.py`.

O módulo recompõe os denominadores de alfabetização dentro do próprio agregado de alfabetização. Essa decisão evita misturar universos e impede que valores suprimidos (`X`) sejam convertidos em zero por soma parcial.

A malha pode conter repetição de `CD_SETOR` por estrutura geométrica. Para a junção tabular, repetições são consolidadas apenas quando `AREA_KM2`, `CD_FCU` e `NM_FCU` são idênticos, inclusive quanto a ausência/presença. Conflito de atributo interrompe a etapa. A dissolução geométrica permanece procedimento cartográfico separado.

`SETOR_FCU` deriva da presença de `CD_FCU` e permanece classificação territorial transversal, não sinônimo automático de precariedade.

## 7. Densidade ajustada

A antiga hipótese de reconstruir `AREA_DOM` localmente foi abandonada. O IBGE publica oficialmente a tabela **Área territorial efetivamente domiciliada e densidade demográfica ajustada dos Setores Censitários**, acompanhada de leia-me metodológico.

O pipeline usa a seguinte estrutura:

- `DENS_ADJ = POP_TOTAL / AREA_DOM`;
- `DENS_CONV = POP_TOTAL / AREA_TOTAL`;
- `PCT_AREA_DOM = 100 * AREA_DOM / AREA_TOTAL`;
- `FATOR = DENS_ADJ / DENS_CONV`.

Densidade permanece variável de contexto territorial, sem sinal normativo de precariedade. Quando a publicação fornecer densidade ajustada pronta, o pipeline preserva esse campo como autoridade externa e compara-o com a recomposição local.

## 8. Habitação

O núcleo de variáveis domiciliares foi confrontado com o dicionário operacional histórico e com os intervalos oficiais dos três arquivos de características do domicílio. Os códigos usados para improvisados, cortiço, estrutura degradada, água, banheiro, esgoto e resíduos estão registrados em `config/mapeamento_ibge.yaml`.

A próxima validação é executar os indicadores diretamente sobre as versões oficiais corrigidas dos arquivos e comparar com a tabela histórica da RMR.

## 9. Entorno

A fonte oficial distingue três universos de 35 variáveis cada:

- domicílios: `V05000-V05034`;
- moradores: `V05200-V05234`;
- faces: `V05400-V05434`.

O estudo histórico usa moradores como universo preferencial. O mapeamento fino de cada indicador continua bloqueado até a conferência do pacote oficial `dicionarios_de_dados_entorno.zip`; referências secundárias não são promovidas a contrato executável.

## 10. Casos-âncora

`config/ancoras_regressao.yaml` contém setores reais dos produtos históricos de equidade/FCU e densidade. O gate falha quando:

- setor esperado desaparece;
- `CD_SETOR` fica duplicado;
- campo esperado não é produzido;
- valor diverge além da tolerância explícita.

As âncoras são um teste rápido e não substituem a regressão integral dos universos históricos.

## 11. CI

Após a integração dos executores de equidade/FCU e densidade, dois testes novos falharam inicialmente porque releram CSVs com `pandas.read_csv` sem o contrato regional de vírgula decimal. Os cálculos não divergiram. Os testes foram corrigidos para usar `ler_csv_rmr`, o mesmo leitor canônico empregado pelo pipeline.

A execução subsequente do GitHub Actions concluiu com sucesso em `pytest -q`: **75 testes passaram**. Isso valida o estado unitário e de integração do código corrente, mas não substitui a regressão integral com os arquivos oficiais materializados no staging.

## 12. Parâmetros históricos recuperados

### Rendimento revisado 2026

- mediana `V06006` como medida principal;
- média `V06004` como apoio/desempate;
- variância `V06005` para heterogeneidade relativa;
- classificação estrita abaixo de R$ 1.212 separada do quintil operacional.

### Tipologias

- solução histórica `k=4`;
- K-Means com `n_init=50`;
- comparação com Ward;
- avaliação de `k=4..8`;
- bootstrap: 30 amostras de 80%;
- alinhamento Húngaro;
- persistência estrutural como medida principal de robustez.

### Análise espacial

- queen como matriz principal;
- 999 permutações;
- kNN simétrico com 6 vizinhos como sensibilidade;
- FDR como camada consolidada, sem apagar a saída exploratória histórica sem correção.

## 13. Execução operacional

O pacote expõe o comando `censo-rmr`:

```bash
censo-rmr --modo AUDITAR --repo <repo> --drive <Censo_2022_Setores_RMR>
```

ou:

```bash
censo-rmr --modo REPROCESSAR_EM_STAGING --repo <repo> --drive <Censo_2022_Setores_RMR>
```

A execução de staging grava em `00_Pipeline/02_Regressao/v1_upstream` e não promove arquivos para as pastas oficiais.

## 14. Critério para promoção

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

Enquanto qualquer um desses gates estiver pendente, `promocao_permitida` permanece `false`.
