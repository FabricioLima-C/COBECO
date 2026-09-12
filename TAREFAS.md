# Tarefas — COBECO v3.1 / MySQL + layout Figma

**Atualização:** 12/09/2026. Base anterior `d1f9e50`; pull posterior até `611d558` incorporado sem perder alterações locais. MySQL substitui SQLite por decisão do usuário. Modelo visual: `COBECO_figma_RF01_RF17_v2.html`, recebido na raiz do repositório.

## Implementação

- [x] **T01 — Contrato e decisões.** Contrato inicial escrito antes dos endpoints; OpenAPI JSON versionado com entradas, saídas, erros e autenticação. Decisões resolvidas no relatório consolidado.
- [x] **T02 — MySQL.** Schema versionado InnoDB, SQL parametrizado, transações e rollback; 8 tabelas de negócio + migrations. Categorias N:N, estoque, soft delete e seed idempotente 10 fornecedores/50 produtos/5 categorias.
- [x] **T03 — Conta.** Cadastro, login, access em memória, refresh rotativo/revogável, logout, bloqueios, recuperação por pergunta/token e perfil com senha atual.
- [x] **T04 — Compras.** Catálogo público, listas salvas com propriedade/paginação/busca, comparação flat sem persistência, cobertura por estoque e quantidade, desempate e invalidação de cache.
- [x] **T05 — Interface Figma.** Landing, criação, cadastro, login/estados, recuperação em três etapas, listas, fornecedores, resultados, perfil e modais conectados à API. CSV e A4; rascunho preservado durante login e erro.
- [x] **T06 — Qualidade e infraestrutura.** Testes Python e JavaScript, limite de cobertura, ruff, CI MySQL, Dockerfile/Compose e comandos de operação.
- [x] **T07 — Documentação.** README, decisões, requisitos, DER MySQL, UC, referência de legado, tarefas e AJUSTES atualizados. XML dos diagramas sincronizado com Markdown.

## Decisões de implementação

- Layout visual preservado do HTML recebido; lógica simulada de contas/senhas/listas em localStorage foi substituída pela API MySQL. O protótipo original permanece intacto.
- Home é a landing do modelo, com botão público de criar lista. Categoria é filtro transitório de fornecedores; produtos não possuem categoria.
- Rascunho em sessionStorage; seleção e access token em memória. Login promove lista apenas com confirmação.
- Itens distintos, quantidade 1–9999 e estoque suficiente para a quantidade completa. A melhor oferta é a de menor custo entre os fornecedores de maior cobertura; valores parciais e empates são informados.
- Uma sessão renovável por conta. `session_version` e hash de refresh em users permitem invalidar no servidor. Token de recuperação de uso único/15 min também fica em users.
- MySQL 8.4 no Compose/CI. Testes locais em MySQL 8.0.46 real, instância isolada na porta 33307 e banco `cobeco_test`. O serviço MySQL80 que o usuário iniciou foi confirmado como Running; não foram alteradas suas credenciais ou bases.
- O código e dados antigos não foram apagados. A imagem atual exclui apps/packages antigos. Importar contas/listas PostgreSQL exige tarefa específica de conversão; veja LEGADO.md.

## Validações executadas

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

## Limites e verificações de ambiente

- O daemon Docker estava indisponível nesta sessão; build e inicialização dos contêineres não foram executados localmente. O Compose foi validado e o CI foi configurado para build/testes com MySQL 8.4, sem alegação de execução remota.
- A cobertura mede domínio/casos de uso, não 97,61% de toda a interface ou repositório legado.
- Duas advertências de depreciação da integração Starlette/httpx apareceram nos testes, sem falhas.
- Rate limiting reside no processo: usar um worker; múltiplos workers exigem estado compartilhado. Recuperação por pergunta continua uma limitação do MVP acadêmico.
- Para usar o serviço MySQL já instalado em vez do ambiente isolado, configure as credenciais e banco próprios em `COBECO/.env`, seguindo README. Nenhuma senha existente foi presumida nem alterada.
