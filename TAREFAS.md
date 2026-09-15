# Tarefas — COBECO: alinhamento da aplicação aos documentos v3.2

**Atualização:** 14/09/2026. Aplicação local de referência: `611beba`. Documentos remotos: `462a2fd`, baixados em `.remote-review/checkout` sem integrar o histórico remoto à aplicação local.

## Resultado da comparação inicial (antes da implementação)

**Na revisão inicial, os documentos batiam parcialmente com a aplicação.** FastAPI/MySQL, frontend JavaScript, catálogo próprio, listas públicas em rascunho, persistência autenticada, perfil, comparação por fornecedor e impressão já existiam. A versão v3.2 acrescenta funções e altera regras. A tabela abaixo registra a situação anterior ao primeiro incremento; o progresso de implementação está na seção seguinte. Os próprios documentos também misturam versões incompatíveis.

As caixas pendentes representam trabalho futuro; caixas concluídas têm evidências registradas abaixo. As tarefas concluídas da versão anterior permanecem no histórico ao final e não significam conformidade integral com v3.2.

### Fontes e evidências

- Base funcional: [REQUISITOS.md](.remote-review/checkout/REQUISITOS.md), [CASOSDEUSO.md](.remote-review/checkout/CASOSDEUSO.md) e [CAMADADEDADOS.md](.remote-review/checkout/CAMADADEDADOS.md).
- Complementos: [macro_report.md](.remote-review/checkout/macro_report.md), [análise de consistência](.remote-review/checkout/analise-UseCase-consistencia.md), [roadmap](.remote-review/checkout/board_roadmap.md) e [documento acadêmico](.remote-review/checkout/pre_DOCUMENTO.md).
- Divergências de versões: README remoto, `analise_REQ_CasosDeUso.md`, `diagrama_DER.md`, `relatorio_analitico_COBECO.md` e documentos históricos de `brain` na cópia baixada.
- Evidências da implementação: [contrato](COBECO/openapi/openapi.json), [schemas](COBECO/backend/adapters/schemas.py), [rotas](COBECO/backend/routers/api.py), [repositórios](COBECO/backend/adapters/repositories.py), [comparação](COBECO/backend/domain/comparison.py) e [frontend](COBECO/frontend/js/compare.js).
- Comparação detalhada por RF, tipos de dados e casos de uso: [relatório da revisão](.remote-review/RELATORIO.md). As fontes em `.remote-review` são cópias locais ainda não versionadas no repositório principal; a etapa 1 prevê consolidá-las em documentação versionada.

| Tema | Aplicação atual | Documentos baixados / pendência |
| --- | --- | --- |
| Arquitetura | FastAPI + MySQL + Vanilla JS | v3.2 coincide; README remoto ainda descreve React/NestJS/PostgreSQL e outros textos mantêm SQLite. |
| Conta e perfil | Cadastro, login, logout, perfil, JWT e revogação | Núcleo coincide; recuperação por código diverge da pergunta de segurança pedida nos textos. |
| Listas | Rascunho em sessionStorage; CRUD autenticado, paginação 20, propriedade e exclusão lógica | Falta validar categorias ao salvar; UC15 também pede valor estimado. |
| Categorias | Uma categoria opcional; disponibilidade exige lista com itens | v3.2 pede uma ou mais categorias obrigatórias antes da lista e fornecedores filtrados por elas. |
| Seed | 5 categorias, 10 fornecedores A–J, 50 produtos, 20 vínculos e 294 ofertas | v3.2 pede 11 categorias, fornecedores nomeados e outros vínculos de categoria. |
| Comparação | Ordenação por total; melhor oferta por maior cobertura e depois menor total | RF16 pede destaque do menor preço; faltam quantidade e motivo nos detalhes de ausentes. |
| Cache e timeout | Cache de 5 min e timeout HTTP de 10 s no frontend | Roadmap pede implementação no backend; delimitar o que deve ser garantido no servidor. |
| Exportação | CSV no navegador e impressão A4 | Falta PDF público gerado no servidor com ReportLab. |
| Banco e contrato | Nomes em inglês, oito tabelas de negócio mais recuperação/migrations; OpenAPI 3.1.0 | v3.2 pede PT-BR, tipos/tamanhos diferentes, outra collation e menciona OpenAPI 3.0. |

## Primeiro incremento implementado — 14/09/2026

- Regras consolidadas em [ESPECIFICACAO_V32.md](ESPECIFICACAO_V32.md): categorias transitórias obrigatórias, união de fornecedores, leitura de listas anteriores, limite de 100 itens e preservação da melhor oferta por cobertura/preço e recuperação segura.
- API e OpenAPI atualizados: `category_ids` obrigatório em disponibilidade, comparação e gravação; `POST /api/suppliers/search` permite consultar fornecedores antes de ter itens. Categorias são validadas na transação de salvamento e fornecedores fora da seleção são rejeitados na comparação.
- Nova tela de categorias com checkboxes; categorias dos fornecedores exibidas na seleção. Alterações limpam resultados e fornecedores selecionados. Login, promoção de rascunho e reabertura de listas continuam funcionando.
- Compatibilidade: o SQL e os registros existentes não foram migrados. Respostas de listas permanecem sem categorias; clientes antigos sem `category_ids` recebem 422. Reiniciar API e recarregar abas para usar o contrato novo. A consulta funciona com o seed atual de cinco categorias; expansão para onze continua pendente.
- **Validação:** 75 testes backend passaram com MySQL 8.0.46 em banco exclusivo `cobeco_v32_6263a547_test`, porta 33307; cobertura de domínio/casos de uso **97,69%**. Nove testes JavaScript passaram. Ruff e exportação do OpenAPI executados. A base de uso da aplicação não foi alterada.
- **Navegador:** Chromium 1440×1000, API de teste na porta 8002; categorias antes da lista, união sem duplicatas, comparação, invalidação ao trocar categorias, recarga com rascunho preservado, promoção após login e reabertura/atualização de lista passaram sem erro JavaScript. Script e capturas em `COBECO/.local-test/v32/` (artefatos locais ignorados).
- **Pendências:** consolidação integral dos documentos/diagramas, migration/seed v3.2, detalhes por item, PDF, cache no servidor e demais tarefas ainda abertas. As etapas 1 e 2 estão parcialmente concluídas; a parte de categorias da etapa 4 foi adiantada porque usa o schema existente e não depende da expansão do seed.

## Plano de execução por etapas

Prioridades deste plano: **P0** = necessário para fechar o fluxo v3.2; **P1** = ajustes de consistência e qualidade. Resolver uma divergência pode exigir corrigir a documentação, implementar uma função ou ambos. Regras contraditórias devem ser consolidadas antes de alterar o comportamento correspondente.

### Etapa 1 — Consolidar escopo e critérios de aceite (P0)

**Dependência:** nenhuma. **Referências:** todos os documentos baixados, README local e `seguranca_COBECO.md`.

- [ ] **V32-01 — Documentação de referência.** Consolidar os textos v3.2 em arquivos versionados, identificando os antigos como histórico. Corrigir referências a React/NestJS/PostgreSQL, SQLite/WAL, envio de email e PDF fora do escopo. Preservar as instruções operacionais da aplicação FastAPI/MySQL local.
- [ ] **V32-02 — Rastreabilidade.** Corrigir IDs duplicados de UC09 (cadastro/impressão) e UC16 (perfil/listas), revisar contagens e manter uma matriz única RF → UC → contrato → teste. Atualizar os diagramas `uc.drawio` e `der.drawio` conforme essa matriz.
- [x] **V32-03 — Regras que divergem.** Definir: melhor oferta por preço ou por cobertura/preço; tabela resumida por fornecedor ou matriz por produto; significado de subtotal/valor estimado antes de escolher fornecedor; limite de itens, inclusive cenários acima de 100 e PDF acima de 10 MB. Registrar exemplos de entrada/saída para cada decisão.
- [x] **V32-04 — Categorias transitórias.** Especificar seleção múltipla pela união das categorias, sem fornecedores duplicados, requisito de categoria ao salvar e comportamento ao reabrir listas antigas sem seleção. Resolver o campo `ativo` de categoria, citado nos UCs mas ausente do DER, e o momento de apresentar disponibilidade antes/depois de haver itens.
- [ ] **V32-05 — Segurança e compatibilidade técnica.** Incorporar recuperação por código e tabelas/campos de revogação à documentação atual. Preservar o modo seguro de produção. Definir se PT-BR se aplica ao SQL, ao JSON ou a ambos; resolver OpenAPI 3.0 versus 3.1 e a collation exigida. Documentar o mapeamento dos nomes atuais para os novos.

**Concluída quando:** existir uma especificação versionada, sem regras conflitantes para esses pontos, com exemplos verificáveis e identificação clara do que já existe e do que falta.

### Etapa 2 — Definir o contrato das funções novas (P0)

**Dependência:** etapa 1. **Referências:** RF08, RF12–RF17; RNF02. **Arquivos:** `COBECO/openapi/`, schemas de entrada/saída e rotas.

- [x] **V32-06 — Contrato de categorias.** Definir coleção de IDs de categorias em disponibilidade, comparação e salvamento conforme a regra consolidada. Prever validação de categorias existentes, fornecedores pertencentes à união selecionada e limite de 2–10 fornecedores distintos. Definir consulta de fornecedores antes de existir lista, sem exigir disponibilidade calculada para lista vazia.
- [ ] **V32-07 — Contrato de resultados.** Definir detalhes por item (produto, quantidade solicitada, disponibilidade, motivo de ausência e preços quando aplicáveis), categorias dos fornecedores e valor estimado apenas após estabelecer sua regra de cálculo. Preservar uma estratégia de compatibilidade com o frontend atual.
- [ ] **V32-08 — Contrato de PDF.** Especificar `POST /api/export/pdf` público, payload de lista/comparação, validações, limites, erros, `application/pdf` e `Content-Disposition` com `lista_YYYYMMDD.pdf`. Definir quais dados o servidor recalcula para manter o PDF coerente com o catálogo e a comparação.

**Concluída quando:** contrato e exemplos cobrirem visitantes e autenticados, entradas inválidas e casos sem oferta; a implementação das próximas etapas tiver entradas e saídas definidas.

### Etapa 3 — Adequar banco e catálogo (P0)

**Dependência:** decisões de dados da etapa 1 e nomes definidos na etapa 2. **Referências:** CAMADADEDADOS, RNF03, RNF08 e RNF12.

- [ ] **V32-09 — Migração compatível.** Criar migrations incrementais para os nomes/tipos efetivamente adotados, sem reescrever migrations já aplicadas. Mapear diferenças: produto 160→200 caracteres, fornecedor 100→150, pergunta 200→255, email 254/255, descrição VARCHAR/TEXT, CNPJ sem/com máscara, BIGINT/INT, DECIMAL(12,2)/(10,2), precisão de datas e collation. Evitar truncamento e perda de IDs, relações, contas, listas ou dados de segurança; manter capacidades maiores quando essa for a decisão documentada.
- [ ] **V32-10 — Seed v3.2.** Implantar as 11 categorias e os 10 fornecedores descritos, com vínculos N:N coerentes, 50 produtos e ofertas determinísticas. Definir contagens exatas a partir dos dados finais; os documentos usam aproximações para vínculos/ofertas. Planejar a atualização dos IDs atuais sem trocar silenciosamente o significado de produtos já salvos em listas.
- [ ] **V32-11 — Validação da migração.** Em banco isolado, testar instalação vazia e atualização de uma cópia da estrutura anterior, repetição do seed, preservação de dados, FKs, índices, exclusões lógicas, rollback das operações de negócio e recuperação após falha de migration. Documentar procedimento de backup/restauração antes de aplicar em base de uso.

**Concluída quando:** schema, DER, repositórios e seed coincidirem e os testes de atualização preservarem as contas/listas anteriores.

### Etapa 4 — Implementar categorias e completar comparação/listas (P0)

**Dependência:** etapas 2 e 3. **Referências:** RF07–RF16. **Arquivos:** casos de uso, repositórios, domínio, `state.js`, `list.js`, `compare.js` e telas.

- [x] **V32-12 — Pré-filtro completo.** Implementar seleção múltipla no backend e checkboxes no frontend, uma categoria mínima, união sem duplicatas, identificação das categorias de cada fornecedor e seleção transitória. Adaptar entrada do fluxo e retorno à lista mantendo o estilo visual atual.
- [x] **V32-13 — Persistência e seleção válidas.** Validar categorias no salvamento e fornecedores/categorias na comparação, também em chamadas diretas à API. Ao alterar categorias, itens ou slider, remover seleções inválidas e invalidar resultados/cache. Tratar promoção de rascunho após login e reabertura de listas sem categorias persistidas.
- [ ] **V32-14 — Resultados completos.** Aplicar a regra consolidada de melhor oferta/empate e apresentar detalhes de ausentes com quantidade e motivo. Tratar preço zero, estoque insuficiente, oferta inativa, nenhuma oferta e totais parciais. Implementar matriz por produto e estimativa de listas somente se mantidas no escopo da etapa 1.
- [ ] **V32-15 — Cache e timeout.** Implementar no servidor o cache de 5 minutos previsto pelo roadmap, com chave que considere itens/quantidades, categorias, fornecedores e versão do catálogo; limitar seu tamanho e invalidar na atualização dos dados. Definir e testar o prazo de processamento da comparação. O timeout atual de envio do corpo HTTP e o cancelamento no navegador não comprovam um limite total de execução do backend.

**Concluída quando:** visitante e usuário autenticado percorrerem categorias → lista → fornecedores → comparação, com validação equivalente na interface e API e salvamento/promoção funcionando.

### Etapa 5 — Implementar PDF e validar impressão (P0)

**Dependência:** contrato da etapa 2; dados e comparação das etapas 3–4 para exportar resultados. **Referências:** RF17, RF18 e RNF11.

- [ ] **V32-16 — Geração de PDF.** Adicionar ReportLab às dependências e implementar caso de uso/rota pública de PDF A4. Incluir lista e/ou comparação conforme contrato, fontes com suporte aos caracteres necessários, nomes longos, totais, ausentes e quebras de página. Tratar limites e falhas sem alterar o rascunho do usuário.
- [ ] **V32-17 — Download na interface.** Adicionar ação de exportar PDF para visitantes e autenticados, download com nome previsto, loading, bloqueio de duplo clique e mensagem de erro. Manter CSV já existente como opção adicional (RD09).
- [ ] **V32-18 — Impressão e casos extremos.** Validar A4, cabeçalhos repetidos, ocultação dos controles, legibilidade em preto e branco e cancelamento. Implementar suporte a mais de 100 itens/geração assíncrona apenas conforme o limite consolidado na etapa 1; corrigir os textos se esses cenários ficarem fora do MVP.

**Concluída quando:** download PDF gerado pelo backend funcionar sem login e com listas salvas, conteúdo corresponder à tela e geração de até 100 itens atender à meta de menos de 5 segundos.

### Etapa 6 — Alinhar detalhes de autenticação e casos de uso (P1)

**Dependência:** regras da etapa 1 e contrato da etapa 2. **Referências:** RF01–RF06, RF09–RF11 e seus UCs.

- [ ] **V32-19 — Recuperação.** Impedir nova senha igual à atual também no reset, regra hoje aplicada apenas na edição de perfil. Consolidar limites de solicitação (documento: 3/h; local: 6/15 min por IP), verificação/reset (3/15 min) e resposta HTTP na sexta falha de login. Preservar token/código de uso único e revogação de sessão; atualizar os critérios documentais do modo legado, incluindo tamanho mínimo da resposta, se ele continuar suportado.
- [ ] **V32-20 — Erros e paginação.** Alinhar documentação e contrato sobre 404 para lista de outro usuário (documentos pedem 403), página excessiva ajustada para a última (documentos pedem primeira), mensagens de erro e confirmação de exclusão na interface. Cobrir o comportamento final com testes, preservando a verificação de propriedade.
- [ ] **V32-21 — Abas e concorrência.** Validar refresh/login/logout entre abas, sessão expirada durante edição, recuperação após erro de rede, armazenamento indisponível/corrompido e lista excluída durante edição/comparação. Definir se comparação é de um snapshot do rascunho ou precisa verificar a existência da lista salva. Corrigir a expressão documental “última gravação vence (optimistic locking)” e testar a política escolhida.

**Concluída quando:** os cenários divergentes tiverem comportamento documentado e testado, mantendo isolamento entre usuários e as correções de segurança existentes.

### Etapa 7 — Validar entrega e sincronizar documentação (P0)

**Dependência:** etapas 1–6. **Referências:** RNF01–RNF12.

- [ ] **V32-22 — Testes e contrato.** Executar testes de domínio, segurança, integração MySQL em banco `_test` e frontend; verificar cobertura mínima de 80% nas regras de negócio, ruff e OpenAPI versionado. Incluir categorias múltiplas, migração de listas antigas, PDF público, propriedade, rollback e regras finais de comparação.
- [ ] **V32-23 — Fluxo visual.** Validar desktop a partir de 1024 px, feedback visual, navegação, promoção de rascunho, categorias sem fornecedores, indisponibilidade total, exportação e impressão. Conferir que a adaptação das telas preserva a identidade visual do modelo Figma.
- [ ] **V32-24 — Infraestrutura e desempenho.** Executar build e subida do Compose, validar CI, medir seed (<10 s), geração de PDF (<5 s para até 100 itens), comparação com 100 itens/10 fornecedores e API p95 (<500 ms). Registrar ambiente, amostra e concorrência; conferir meta de pipeline <5 min e limites de um worker enquanto o limitador for em memória.
- [ ] **V32-25 — Documentação final.** Sincronizar README, requisitos, casos de uso, DER, diagramas, contrato, relatório analítico, segurança, roadmap e documento acadêmico com o código validado. Registrar resultados efetivamente executados e atualizar este checklist somente após cada aceite.

**Concluída quando:** evidências atuais comprovarem o fluxo v3.2, documentos refletirem a aplicação e comandos de instalação/atualização forem reproduzíveis.

## Fora deste plano de adequação ao MVP

Histórico persistente de comparações, importação CSV, alertas de preço, compartilhamento, mobile/PWA, integração com fornecedores reais, IA e idiomas adicionais continuam como backlog RD01–RD08. O código legado não comprova implementação dessas funções na aplicação FastAPI atual. CSV (RD09) já existe e deve ser preservado.

## Validação da revisão inicial (antes da implementação)

A revisão documental inicial de 14/09/2026 passou em **17 testes de domínio**, **8 testes JavaScript** e conferência do OpenAPI, sem integração MySQL, cobertura completa, benchmarks, build Docker ou navegador. A validação posterior do código implementado está na seção “Primeiro incremento implementado”. Os números históricos abaixo não certificam as funcionalidades v3.2 ainda pendentes.

## Histórico — entrega v3.1 / MySQL + layout Figma

As seções abaixo preservam o registro de 12/09/2026. A recuperação por pergunta mencionada nesse histórico foi posteriormente substituída por código como padrão e único modo de produção; consulte [README.md](README.md) e [seguranca_COBECO.md](seguranca_COBECO.md).

**Atualização:** 12/09/2026. Base anterior `d1f9e50`; pull posterior até `611d558` incorporado sem perder alterações locais. MySQL substitui SQLite por decisão do usuário. Modelo visual: `COBECO_figma_RF01_RF17_v2.html`, recebido na raiz do repositório.

### Implementação histórica

- [x] **T01 — Contrato e decisões.** Contrato inicial escrito antes dos endpoints; OpenAPI JSON versionado com entradas, saídas, erros e autenticação. Decisões resolvidas no relatório consolidado.
- [x] **T02 — MySQL.** Schema versionado InnoDB, SQL parametrizado, transações e rollback; 8 tabelas de negócio + migrations. Categorias N:N, estoque, soft delete e seed idempotente 10 fornecedores/50 produtos/5 categorias.
- [x] **T03 — Conta.** Cadastro, login, access em memória, refresh rotativo/revogável, logout, bloqueios, recuperação por pergunta/token e perfil com senha atual.
- [x] **T04 — Compras.** Catálogo público, listas salvas com propriedade/paginação/busca, comparação flat sem persistência, cobertura por estoque e quantidade, desempate e invalidação de cache.
- [x] **T05 — Interface Figma.** Landing, criação, cadastro, login/estados, recuperação em três etapas, listas, fornecedores, resultados, perfil e modais conectados à API. CSV e A4; rascunho preservado durante login e erro.
- [x] **T06 — Qualidade e infraestrutura.** Testes Python e JavaScript, limite de cobertura, ruff, CI MySQL, Dockerfile/Compose e comandos de operação.
- [x] **T07 — Documentação.** README, decisões, requisitos, DER MySQL, UC, referência de legado, tarefas e AJUSTES atualizados. XML dos diagramas sincronizado com Markdown.

### Decisões de implementação históricas

- Layout visual preservado do HTML recebido; lógica simulada de contas/senhas/listas em localStorage foi substituída pela API MySQL. O protótipo original permanece intacto.
- Home é a landing do modelo, com botão público de criar lista. Categoria é filtro transitório de fornecedores; produtos não possuem categoria.
- Rascunho em sessionStorage; seleção e access token em memória. Login promove lista apenas com confirmação.
- Itens distintos, quantidade 1–9999 e estoque suficiente para a quantidade completa. A melhor oferta é a de menor custo entre os fornecedores de maior cobertura; valores parciais e empates são informados.
- Uma sessão renovável por conta. `session_version` e hash de refresh em users permitem invalidar no servidor. Token de recuperação de uso único/15 min também fica em users.
- MySQL 8.4 no Compose/CI. Testes locais em MySQL 8.0.46 real, instância isolada na porta 33307 e banco `cobeco_test`. O serviço MySQL80 que o usuário iniciou foi confirmado como Running; não foram alteradas suas credenciais ou bases.
- O código e dados antigos não foram apagados. A imagem atual exclui apps/packages antigos. Importar contas/listas PostgreSQL exige tarefa específica de conversão; veja LEGADO.md.

### Validações executadas em 12/09/2026

| Verificação | Resultado |
|---|---|
| pytest com MySQL real | **31 testes passaram**, 39,42 s na execução após integração do layout |
| Cobertura de domínio + casos de uso | **97,61%**, incluindo branches; meta 80% |
| JavaScript (Node test runner) | **7 testes passaram**, incluindo contrato visual e exclusão da lógica simulada do protótipo |
| Ruff check e format | Passaram |
| OpenAPI versionado vs aplicação | Conferência passou |
| Compose | `docker compose config --quiet` passou |
| Navegador Chromium 1440×1000 | Fluxo completo passou sem erro JavaScript: landing → lista → fornecedores → comparação → CSV → modal → cadastro → login → promoção → listas → perfil → refresh → logout → recuperação em 3 etapas |
| Fidelidade visual | Screenshot da landing **idêntico pixel a pixel** ao HTML de referência em 1440×1000. Card, campos e botão de login com posições e dimensões idênticas à referência |
| Impressão A4 | PDFs de lista e comparação gerados no Chromium após integração Figma; conteúdo e visibilidade de impressão verificados |
| CSV | Nome lista_YYYYMMDD.csv no download; BOM, aspas, acentos, delimitador e fórmula verificados |
| Transações | Falha simulada após gravação e antes do commit não deixou lista/itens; FKs e CHECKs MySQL exercitados |
| Performance HTTP local | 30 amostras por endpoint, concorrência 1: catálogo p95 **124,83 ms**, comparação p95 **118,45 ms**; catálogo teve uma chamada inicial de 2185,58 ms. Medição pequena, não prova desempenho sob carga |
| Seed idempotente | 0,064 s no banco local já inicializado; repetição sem duplicatas |

Capturas e artefatos temporários da validação estão em `COBECO/.local-test/` (ignorados pelo Git). Scripts reproduzíveis: `scripts/sync_figma_layout.py`, `scripts/sync_mysql_diagrams.py`, `python -m backend.export_openapi` e `python -m backend.benchmark`.

### Limites e verificações de ambiente registrados em 12/09/2026

- O daemon Docker estava indisponível nesta sessão; build e inicialização dos contêineres não foram executados localmente. O Compose foi validado e o CI foi configurado para build/testes com MySQL 8.4, sem alegação de execução remota.
- A cobertura mede domínio/casos de uso, não 97,61% de toda a interface ou repositório legado.
- Duas advertências de depreciação da integração Starlette/httpx apareceram nos testes, sem falhas.
- Rate limiting reside no processo: usar um worker; múltiplos workers exigem estado compartilhado. Recuperação por pergunta continua uma limitação do MVP acadêmico.
- Para usar o serviço MySQL já instalado em vez do ambiente isolado, configure as credenciais e banco próprios em `COBECO/.env`, seguindo README. Nenhuma senha existente foi presumida nem alterada.
