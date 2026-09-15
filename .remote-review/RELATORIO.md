# Verificação do remoto e compatibilidade da API

Data: 14/09/2026.

## Resultado

A API local atende ao fluxo básico de autenticação, listas e comparação, mas **não atende integralmente aos documentos v3.2 do remoto**. As principais diferenças são PDF no servidor, múltiplas categorias obrigatórias, dados do seed, modelo físico em português e critério de melhor oferta. Esta tarefa apenas baixou e analisou os arquivos; não implementou mudanças na aplicação.

## Git e preservação local

- Repositório: `https://github.com/FabricioLima-C/COBECO.git`.
- A `main` original permanece em `611beba` (Aprimoramento da seguranca).
- `git fetch origin` identificou atualização forçada de `origin/main` para `462a2fd` (Use Case Diagram).
- Os históricos divergem: 18 commits exclusivos locais e 9 exclusivos remotos.
- O estado remoto não contém `COBECO/`, os scripts locais, o CI e os documentos de segurança/monografia presentes no histórico local. Um pull com integração na árvore original exigiria resolver essa divergência e poderia afetar esses arquivos.
- Foi criada uma cópia independente em [checkout](checkout/README.md). Nela foi executado `git pull --ff-only origin main`, concluído com `Already up to date`.
- O pull **não foi integrado à main original**. O README de execução local foi preservado.
- Foram preservadas as alterações preexistentes: exclusão local de `Monografia e Demais Docs/COBECO_Monografia.docx`, arquivo não rastreado `COBECO_Monografia_new.docx` e `.claude/settings.local.json`.
- Os únicos novos artefatos desta revisão ficam em `.remote-review/`. Nenhum commit ou push foi realizado; não foram executados migrations, seed ou comandos de alteração do banco.

### Arquivos adicionados/modificados

Comparação entre os snapshots `611beba` e `462a2fd`: **7 adicionados e 10 modificados**, todos disponíveis no checkout isolado. A lista completa, incluindo ausências no remoto, está em [alteracoes-remotas.txt](alteracoes-remotas.txt). Os hashes dos 17 arquivos estão em [arquivos-baixados-sha256.json](arquivos-baixados-sha256.json).

| Estado | Arquivos |
| --- | --- |
| Adicionados | `CAMADADEDADOS.md`, `CASOSDEUSO.md`, `REQUISITOS.md`, `analise-UseCase-consistencia.md`, `board_roadmap.md`, `macro_report.md`, `pre_DOCUMENTO.md` |
| Modificados | `README.md`, `analise_REQ_CasosDeUso.md`, `diagrama_DER.md`, `relatorio_analitico_COBECO.md`, `der.drawio`, `uc.drawio`, `brain/_old-artifact/escopo.md`, `brain/_old-artifact/req_func.md`, `brain/_old-artifact/req_n-func.md`, `brain/_old-artifact/tech_stack.md` |

Os três últimos arquivos de requisitos/stack antigos estão vazios no remoto. Documentos antigos em `brain` não foram tratados como requisitos adicionais do MVP atual.

## Referência documental

Para a comparação funcional, foi priorizado o conjunto datado de 14/09/2026: [REQUISITOS.md](checkout/REQUISITOS.md), [CASOSDEUSO.md](checkout/CASOSDEUSO.md), [CAMADADEDADOS.md](checkout/CAMADADEDADOS.md) e [macro_report.md](checkout/macro_report.md). O [roadmap](checkout/board_roadmap.md) detalha tarefas e endpoint de PDF; [pre_DOCUMENTO.md](checkout/pre_DOCUMENTO.md) apresenta a versão acadêmica. Os demais textos foram considerados com suas divergências de versão, sem assumir que seus checklists de aprovação comprovem implementação.

## Matriz funcional

“Atende ao núcleo” significa que contrato e código dão suporte à função; não significa certificação de todos os cenários de interface e integração.

| RF v3.2 | Situação | Evidência na aplicação local |
| --- | --- | --- |
| RF01 Cadastro | Parcial | `POST /api/auth/register` valida username, email, senha e confirmação. No modo padrão entrega código individual; pergunta não é obrigatória. Campos JSON estão em inglês. |
| RF02 Login | Atende ao núcleo | `POST /api/auth/login`, JWT access de 15 min, refresh de 7 dias, limitador por usuário/IP e exclusão de contas desativadas. Há diferenças finas no momento do HTTP 429 descritas abaixo. |
| RF03 Logout | Atende ao núcleo | `POST /api/auth/logout` invalida sessão no servidor e limpa cookie. |
| RF04 Recuperação | Divergente | Padrão e produção usam código individual. `question` e `log` são legados de desenvolvimento. A API não revela a pergunta cadastrada. |
| RF05 Perfil | Atende ao núcleo | `GET /api/profile` retorna id, username, nome, email e data de criação. |
| RF06 Editar perfil | Atende ao núcleo | `PATCH /api/profile` exige senha atual e impede repetir a senha atual na alteração. Email/nome/senha são atualizados em transação. |
| RF07 Lista efêmera | Atende ao núcleo | Estado no frontend; autocomplete em `GET /api/products?q=...`; quantidade inteira 1–9999 e produtos distintos. Limite adicional de 100 itens. |
| RF08 Salvar lista | Parcial | `POST /api/lists` exige autenticação, valida produtos e grava lista/itens em transação. Não recebe nem valida categorias selecionadas. |
| RF09 Minhas listas | Atende ao núcleo | `GET /api/lists` filtra proprietário e exclusões, busca por nome, 20 por página, data decrescente. Não retorna valor estimado pedido em UC15. |
| RF10 Editar lista | Atende ao núcleo | `PUT /api/lists/{list_id}` valida propriedade, nome, produtos e quantidades. |
| RF11 Excluir lista | Atende ao núcleo | `DELETE /api/lists/{list_id}` faz exclusão lógica; confirmação pelo nome está na interface, não no payload da API. |
| RF12 Categorias | Parcial | `GET /api/categories`; disponibilidade recebe somente `category_id` opcional. Não aceita seleção múltipla obrigatória. |
| RF13 Fornecedores | Parcial | Comparação valida 2–10 fornecedores ativos distintos. Não verifica pertencimento às categorias selecionadas, porque não as recebe. |
| RF14 Disponibilidade | Atende ao núcleo | API fornece `coverage`; frontend aplica slider e conserva apenas seleções visíveis válidas. |
| RF15 Orçamento | Parcial | Calcula totais, cobertura e ausentes, ordenando total crescente. Cache de 5 min e timeout de 10 s estão no frontend; não há cache de comparação no backend como pede o roadmap. |
| RF16 Resultados | Divergente | A ordenação é por total, mas a melhor oferta prioriza maior cobertura e depois menor custo. Documentos v3.2 pedem destaque pelo menor preço. Ausentes retornam apenas nomes. |
| RF17 PDF | Não atende | Não existe `POST /api/export/pdf`, nem dependência ReportLab no requirements da aplicação. CSV no navegador e impressão não equivalem ao PDF server-side exigido. |
| RF18 Impressão | Implementada no frontend | Impressão e CSS A4 disponíveis. Não requer endpoint próprio. Sem nova validação visual nesta revisão. |

### Evidências principais no código

- [Rotas](../COBECO/backend/routers/api.py), [schemas de entrada](../COBECO/backend/adapters/schemas.py) e [respostas](../COBECO/backend/adapters/responses.py).
- [Comparação](../COBECO/backend/domain/comparison.py), [casos de uso de compras](../COBECO/backend/usecases/shopping.py) e [repositórios](../COBECO/backend/adapters/repositories.py).
- [Autenticação](../COBECO/backend/usecases/auth.py) e [configuração](../COBECO/backend/config.py).
- [Cache e seleção no frontend](../COBECO/frontend/js/compare.js), [timeout HTTP](../COBECO/frontend/js/api.js) e [exportação](../COBECO/frontend/js/export.js).

## Informações que a API/modelo atual não comporta como especificado

1. **Múltiplas categorias e pré-filtro antes da lista:** `Availability` exige pelo menos um item e aceita somente um `category_id` opcional. O novo fluxo começa pelas categorias, antes da lista. Também faltam categorias/badges na resposta de fornecedores. `ShoppingList` e `Comparison` não recebem categorias; campos extras são rejeitados.
2. **Detalhes por produto:** `missing_items` e `available_items` são listas de nomes. Não há quantidade/motivo do item ausente nem matriz de preço por produto e fornecedor, necessária à representação descrita em `pre_DOCUMENTO.md`, seção 5.1. A listagem de listas não traz valor estimado.
3. **Melhor oferta:** exemplo já coberto no teste de domínio: fornecedor com 50% de cobertura e R$ 0,50 fica primeiro na ordenação; fornecedores com 100% e R$ 1,50 são marcados como melhores. Isso diverge da regra de destacar simplesmente o menor preço.
4. **Banco em português:** o modelo conceitual de oito tabelas de negócio e a relação N:N fornecedor/categoria existem. Porém tabelas e colunas físicas estão em inglês. `usuarios/nome_usuario` não são nomes aceitos diretamente no JSON ou no SQL atual. A aplicação também mantém `recovery_codes`, `schema_migrations` e campos de revogação/recuperação em `users`, ausentes do novo DER.
5. **Tamanhos/tipos:** documentos pedem produto de 200 caracteres (local 160), fornecedor de 150 (local 100), pergunta de 255 (local 200), descrição TEXT (local VARCHAR(255)), CNPJ formatado de 18 (local CHAR(14)), IDs INT (local BIGINT) e preço DECIMAL(10,2) (local DECIMAL(12,2)). Parte das diferenças amplia a capacidade local; outras impedem armazenar valores documentados. Não é apenas tradução de nomes.
6. **Seed:** local tem 5 categorias, 10 fornecedores fictícios A–J, 50 produtos, 20 vínculos de categoria e 294 ofertas. v3.2 especifica 11 categorias, fornecedores nomeados e aproximadamente 25 vínculos/~300 preços. A estrutura suporta expandir o catálogo, mas o seed entregue não é o descrito.
7. **Codificação:** conexão usa utf8mb4 e tabelas InnoDB. Compose configura `utf8mb4_0900_ai_ci`; RNF12 pede `utf8mb4_unicode_ci`. Não foi consultada a configuração do banco em execução.
8. **OpenAPI:** contrato local é 3.1.0; RNF02 menciona 3.0. Contrato e implementação local conferem entre si, mas ainda não incluem as funções novas.

Fontes: [migration inicial](../COBECO/backend/migrations/001_initial.sql), [migration de recuperação](../COBECO/backend/migrations/002_recovery_codes.sql), [seed](../COBECO/backend/seed.py), [conexão/transações](../COBECO/backend/adapters/database.py), [Compose](../COBECO/docker-compose.yml), [OpenAPI](../COBECO/openapi/openapi.json).

### Diferenças adicionais de casos de uso

- UC12 pede impedir senha igual à anterior no reset; esse bloqueio existe em editar perfil, mas não em `Auth.reset`.
- UC12 pede no máximo 3 solicitações/hora; local limita solicitações a 6/15 min por IP e tentativas de verificação/reset a 3/15 min por usuário/IP.
- UC10 descreve HTTP 429 na sexta falha. O código registra a sexta falha e bloqueia as tentativas seguintes; o teste existente confirma o início da janela na sexta falha.
- Cadastro legado aceita resposta de 2 caracteres; UC09 pede rejeitar respostas menores que 3.
- UC13 pede 403 para lista de outro usuário; local usa 404, assim como para lista inexistente.
- UC15 pede voltar à página 1 em página excessiva; local ajusta para a última página disponível.
- Documentos descrevem listas/PDF com mais de 100 itens; o contrato local limita listas a 100 itens.
- Os detalhes de abas, eventos de storage, feedback visual e impressão precisam de validação específica de navegador antes de se afirmar conformidade integral.

## Inconsistências dos próprios documentos

- README remoto descreve React/NestJS/PostgreSQL, recuperação por email e PDF fora do escopo. v3.2 descreve Vanilla JS/FastAPI/MySQL, sem email e PDF obrigatório.
- `relatorio_analitico_COBECO.md` e `diagrama_DER.md` ainda contêm SQLite/WAL, CSV e cinco categorias. `analise_REQ_CasosDeUso.md` mantém referências v3.1/17 RFs/26 UCs.
- `CASOSDEUSO.md` usa **UC09** tanto para cadastro quanto para impressão. Outros textos reutilizam UC16 para perfil e listas; as contagens declaradas não resolvem essas colisões.
- UC03 menciona categoria inativa (`ativo=false`), mas `CAMADADEDADOS.md` não define esse campo em categorias.
- O DER novo omite os dados usados para revogar sessões e consumir tokens/códigos, embora os casos de uso exijam esses comportamentos.
- Há textos que descrevem limite de 100 itens e cenários acima de 100; filtro opcional e categorias obrigatórias; tabela por fornecedor e matriz por produto. Precisam de critérios de aceite consolidados.

As diferenças de recuperação são deliberadas na implementação local e estão explicadas no [relatório de segurança preservado](../seguranca_COBECO.md). A documentação deve incorporar essas decisões antes de qualquer mudança nesse fluxo.

## Verificação executada

Executados em `COBECO/`, sem banco e sem iniciar/reiniciar a aplicação:

| Comando | Resultado |
| --- | --- |
| `.venv/Scripts/python.exe -B -m pytest backend/tests/test_domain.py -q -o addopts= -p no:cacheprovider` | 17 testes passaram; 2 avisos de depreciação das bibliotecas de teste. |
| `.venv/Scripts/python.exe -B -m backend.export_openapi --check` | Passou; contrato versionado corresponde à aplicação. |
| `node --test frontend/tests/*.test.mjs` | 8 testes passaram. |

Não foram executados integração MySQL, cobertura completa, benchmarks, geração PDF, build Docker ou navegação visual. Portanto, esta revisão não comprova as metas de p95, tempo de seed/PDF, pipeline ou cobertura mínima v3.2. Os testes aprovados verificam a implementação existente, não substituem testes das funções ausentes.

## Próximos ajustes identificados (não executados)

1. Consolidar os documentos v3.2, numeração de UCs, regra de melhor oferta, limites e decisões de segurança.
2. Definir contrato para múltiplas categorias, validação no salvamento/comparação e detalhamento dos itens ausentes.
3. Adicionar exportação pública de PDF e alinhar responsabilidades de cache/timeout.
4. Planejar migration compatível com dados existentes se PT-BR físico/tamanhos forem obrigatórios; atualizar seed e documentar tabelas técnicas.
5. Validar as mudanças futuras com banco isolado, testes de contrato e fluxo de navegador.
