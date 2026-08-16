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

## 2. Núcleo operacional com cálculo codificado, regressão integral ainda pendente

- habitação;
- entorno;
- sexo/cor ou raça/alfabetização/FCU;
- densidade convencional e ajustada;
- PCA por domínio;
- tipologias territoriais e estabilidade;
- Moran global, LISA e LISA bivariado;
- segregação racial;
- cartografia;
- tabelas editoriais.

O fato de o cálculo estar codificado não equivale a validação integral. Para promoção metodológica, cada bloco deve ser confrontado com os produtos históricos completos ou com fonte oficial independente.

## 3. Fontes upstream verificadas

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

## 4. Equidade, alfabetização e FCU

O mapeamento `Vxxxxx -> conceito -> campo canônico` necessário ao núcleo atual foi registrado em `config/mapeamento_ibge.yaml` e incorporado a `equidade.py`.

O módulo agora pode receber diretamente as três tabelas temáticas brutas — demografia, cor ou raça e alfabetização — e recompõe os denominadores de alfabetização dentro do próprio agregado de alfabetização. Essa decisão evita misturar universos e impede que valores suprimidos (`X`) sejam convertidos em zero por soma parcial.

Foram incluídos testes para:

- recomposição de população 15+ e não alfabetizados 15+;
- taxas por sexo e cor ou raça;
- junção de `CD_FCU`/`NM_FCU`;
- preservação de supressões como ausência.

Ainda falta a regressão integral contra a planilha histórica de 7.208 setores.

## 5. FCU

A malha oficial confirma `CD_FCU` e `NM_FCU`. `SETOR_FCU` deriva da presença de `CD_FCU` e permanece classificação territorial transversal, não sinônimo automático de precariedade.

Falta incorporar ao pipeline de aquisição territorial a rotina explícita de leitura da malha, controle de unicidade por `CD_SETOR`, preservação dos atributos FCU e auditoria da cobertura da junção.

## 6. Densidade ajustada

A antiga hipótese de reconstruir `AREA_DOM` localmente foi abandonada. O IBGE publica oficialmente a tabela **Área territorial efetivamente domiciliada e densidade demográfica ajustada dos Setores Censitários**, acompanhada de leia-me metodológico.

O pipeline deverá usar essa publicação como fonte upstream para `AREA_DOM` e confrontar a densidade oficial com a recomposição:

- `DENS_ADJ = POP_TOTAL / AREA_DOM`;
- `DENS_CONV = POP_TOTAL / AREA_TOTAL`;
- `PCT_AREA_DOM = 100 * AREA_DOM / AREA_TOTAL`;
- `FATOR = DENS_ADJ / DENS_CONV`.

Densidade permanece variável de contexto territorial, sem sinal normativo de precariedade.

## 7. Habitação

O núcleo de variáveis domiciliares foi confrontado com o dicionário operacional histórico e com os intervalos oficiais dos três arquivos de características do domicílio. Os códigos usados para improvisados, cortiço, estrutura degradada, água, banheiro, esgoto e resíduos estão registrados em `config/mapeamento_ibge.yaml`.

A próxima validação é executar os indicadores diretamente sobre as versões oficiais corrigidas dos arquivos e comparar com a tabela histórica da RMR.

## 8. Entorno

A fonte oficial distingue três universos de 35 variáveis cada:

- domicílios: `V05000-V05034`;
- moradores: `V05200-V05234`;
- faces: `V05400-V05434`.

O estudo histórico usa moradores como universo preferencial. O mapeamento fino de cada indicador continua bloqueado até a conferência do pacote oficial `dicionarios_de_dados_entorno.zip`; referências secundárias não são promovidas a contrato executável.

## 9. Parâmetros históricos recuperados

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

## 10. Critério para promoção

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
