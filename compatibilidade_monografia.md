# Compatibilidade entre a monografia e o projeto COBECO

Verificação realizada em 13/09/2026 sobre [COBECO_Monografia.docx](Monografia%20e%20Demais%20Docs/COBECO_Monografia.docx), incluindo o texto e as três imagens incorporadas, e a implementação atual em `COBECO/backend` e `COBECO/frontend`.

**Parecer: o projeto é substancialmente compatível com o MVP descrito, mas não integralmente.** A arquitetura, o catálogo, as listas, a comparação por cobertura/custo e os resultados dos testes estão alinhados. Há uma divergência funcional na recuperação de senha, inconsistências nos protótipos e afirmações documentais que precisam de ajuste ou evidência adicional. Esta revisão não alterou o código nem a monografia.

## Divergências e ajustes recomendados

### 1. RF04: a API permite recuperação sem o token obrigatório descrito

A monografia exige recuperação em três etapas com token de uso único válido por 15 minutos. A interface implementa esse percurso em [auth.js](COBECO/frontend/js/auth.js): identificação, validação da resposta com emissão de token e redefinição.

Entretanto, `Auth.reset` aceita `answer` quando não há `token`, no modo `question`, e redefine a senha diretamente. O schema `Reset` também torna ambos os campos opcionais. Assim, um cliente da API pode pular a emissão e a validação temporal do token, desde que conheça a resposta correta. Isso não significa redefinição sem verificação da resposta: a divergência é a ausência da obrigatoriedade das três etapas.

Evidências: [usecases/auth.py](COBECO/backend/usecases/auth.py), condição `self.settings.recovery_mode == "question" and not data.get("token")`; [adapters/schemas.py](COBECO/backend/adapters/schemas.py), classe `Reset`; [test_api.py](COBECO/backend/tests/test_api.py), teste `test_question_reset_revokes_session`, que passou nesta revisão e usa a resposta diretamente. O teste `test_three_stage_recovery_token_is_single_use` também passou, confirmando que o percurso com token funciona.

**Recomendação:** exigir token em `/api/auth/reset`, concentrar a verificação da resposta em `/api/auth/recovery/verify` e ajustar contrato e testes. Alternativamente, documentar explicitamente a modalidade direta se sua manutenção for uma decisão do projeto.

### 2. Figura 3: o protótipo de baixa fidelidade representa decisões anteriores

A imagem incorporada à seção 6 contém diferenças que vão além de cores e posicionamento:

| Figura 3 | Implementação atual |
|---|---|
| Login por “Email ou Username” | Login por username, conforme RF02 |
| Recuperação por e-mail, botão “Enviar link” e máximo de 3 solicitações/hora | Pergunta de segurança em três etapas na interface; sem envio de e-mail; solicitação limitada a 6 por 15 minutos por IP e validação limitada a 3 falhas por 15 minutos |
| Botão “Excluir Conta” no perfil | Não existe rota nem ação de exclusão de conta no MVP |
| Confirmação digitando “EXCLUIR” | Exclusão da lista exige digitar o nome da própria lista na interface |
| Login/cadastro identificados como UC01–02; fornecedores como UC25–26 | Quadro 11 identifica login/cadastro como UC10/UC09 e seleção/filtro como UC03/UC04 |

A figura apresenta nove quadros, mas eles incluem modal e impressão e não correspondem às nove telas principais enumeradas no texto da seção 6: a página inicial não aparece e login/cadastro estão agrupados.

Evidências de implementação: [auth.js](COBECO/frontend/js/auth.js), [list.js](COBECO/frontend/js/list.js), [ui.js](COBECO/frontend/js/ui.js), [routers/api.py](COBECO/backend/routers/api.py) e [usecases/auth.py](COBECO/backend/usecases/auth.py).

**Recomendação:** atualizar a figura e seus códigos UC ou identificá-la expressamente como protótipo inicial superado, explicando quais decisões mudaram. A ausência de exclusão de conta não é descumprimento dos RF atuais; é uma inconsistência entre a imagem e esses requisitos.

### 3. Figura 4: falta a imagem de alta fidelidade

A seção 7 mantém literalmente `[INSERIR IMAGEM — inserir captura da interface]`. O DOCX contém somente três imagens, correspondentes às figuras anteriores. A interface e o modelo HTML existem no projeto, mas a figura anunciada ainda não foi inserida na monografia.

**Recomendação:** inserir uma captura atual da aplicação, coerente com a resolução e a tela mencionadas no texto. Existem capturas locais em `COBECO/.local-test`, mas sua inserção não foi realizada nesta auditoria.

### 4. Quadro 15: controles implementados não comprovam ausência de vulnerabilidades críticas

O critério de segurança declara “Ausência de vulnerabilidades críticas”, mas o resultado apresentado lista bcrypt, tokens, cookies, limitação de tentativas e revogação. Esses controles estão presentes, porém sua existência e a aprovação dos testes funcionais não demonstram aquela ausência. O CI examinado executa lint, testes, contrato e build, sem uma etapa explícita de auditoria de vulnerabilidades.

**Recomendação:** descrever o resultado como implementação e teste dos controles previstos ou anexar avaliação de segurança com método, escopo, data e resultados. Esta revisão não fez auditoria de dependências nem teste de invasão, e não afirma a existência ou ausência de vulnerabilidades críticas.

O percurso em menos de cinco minutos e a igualdade visual pixel a pixel também são resultados históricos relatados no documento. Há registros e capturas anteriores em `TAREFAS.md` e `.local-test`, mas esta revisão não refez um estudo de usabilidade nem uma comparação pixel a pixel.

### 5. Ajustes de precisão no texto

- **Autenticação:** a premissa “exigida apenas para persistir listas” é restritiva demais. Consultar listas salvas e visualizar/alterar perfil também exigem autenticação. Sugestão: “A montagem e a comparação são públicas; o acesso às listas pessoais e ao perfil exige autenticação.” Evidência: dependência `User` nas rotas de listas e perfil e proteção das telas em [ui.js](COBECO/frontend/js/ui.js).
- **Casos de uso:** a seção 4 afirma genericamente que validação, hash e emissão de sessão são sempre executados por cadastro, autenticação, recuperação e alteração de perfil. No código, cadastro não emite sessão; login verifica o hash; alteração de nome/e-mail não gera novo hash de senha; recuperação revoga a sessão. A tabela UC21 → RF02 é mais precisa do que essa frase. Ajustar a explicação das relações sem atribuir as três operações indistintamente a todos esses fluxos.
- **Exclusão de usuários:** `users.deleted_at` existe no schema e é considerado nas consultas, mas não há caso de uso de exclusão de conta. Na seção 5, distinguir o suporte do modelo à exclusão lógica de usuários da funcionalidade de exclusão de listas efetivamente oferecida.
- **Referência OpenAPI:** a bibliografia cita a especificação 3.0.3, enquanto [openapi.json](COBECO/openapi/openapi.json) declara `3.1.0`. RNF02 não fixa uma versão, portanto o requisito está atendido; convém alinhar a referência técnica à versão utilizada.

## Conferência dos requisitos

“Compatível” indica evidência no código e, quando aplicável, nos testes abaixo; não equivale a certificação de todos os cenários possíveis.

| Requisitos | Resultado | Evidência principal |
|---|---|---|
| RF01–RF03 | Compatíveis: cadastro, login por username, bloqueio após seis falhas, logout e preservação do rascunho | `adapters/schemas.py`, `usecases/auth.py`, `usecases/limiter.py`, `frontend/js/state.js`, testes de API |
| RF04 | Parcial: interface com três etapas; API também aceita resposta sem token | Achado 1 |
| RF05–RF06 | Compatíveis: perfil próprio, username somente leitura, alterações com senha atual | `routers/api.py`, `usecases/auth.py`, `frontend/index.html`, testes de perfil |
| RF07–RF08 | Compatíveis: lista pública com catálogo e quantidades 1–9999; salvamento autenticado com rascunho preservado | `frontend/js/list.js`, `state.js`, schemas e rotas |
| RF09–RF10 | Compatíveis: busca, criação em ordem decrescente, 20 registros por página e edição por proprietário | `adapters/repositories.py`, teste de listas |
| RF11 | Compatível no fluxo de interface: confirmação pelo nome e exclusão lógica por proprietário | `frontend/js/list.js`, `ui.js`, `adapters/repositories.py` |
| RF12–RF13 | Compatíveis no catálogo do MVP: seleção de 2–10 fornecedores distintos ativos, categoria e disponibilidade mínima | `Comparison` no schema, `Shopping.comparison`, `frontend/js/compare.js` |
| RF14–RF15 | Compatíveis: preço × quantidade, estoque integral, cobertura, ausências, parciais, ordenação, empates e melhor oferta | `domain/comparison.py`, testes de domínio/API e percurso no navegador |
| RF16–RF17 | Compatíveis: CSV público e impressão A4 sem navegação | `frontend/js/export.js`, estilos de impressão, testes JavaScript e verificação no navegador |
| RNF01–RNF03 | Compatíveis: camadas, composição em `main.py`, OpenAPI versionado e persistência MySQL transacional | Código, verificação do contrato, migrations e testes de integração |
| RNF04–RNF05 | Implementação compatível: desktop, modelo visual, estados e suporte a teclado; avaliação completa de acessibilidade não refeita | `layout.test.mjs`, `frontend/js/ui.js`, CSS e verificação em 1440 × 1000 |
| RNF06 | Compatível e revalidado: cobertura mínima de 80% | 31 testes e 97,61% de cobertura de domínio/casos de uso |
| RNF07 | Configuração compatível; build e execução Docker não revalidados | Dockerfile, Compose, volume `mysql_data` e `.github/workflows/ci.yml` |
| RNF08 | Compatível e revalidado | Teste idempotente: 5 categorias, 10 fornecedores, 50 produtos, 20 vínculos e 294 ofertas |
| RNF09 | Meta atendida na amostra local; não representa teste sob carga | Novas medições abaixo |
| RNF10 | Controles descritos presentes; ressalva de RF04 e do critério de segurança do Quadro 15 | `adapters/security.py`, `usecases/auth.py`, middleware, cookies e estado em memória |
| RD01–RD08 | Evoluções futuras, não obrigações do MVP | Sua ausência na implementação atual não caracteriza incompatibilidade |

A confirmação pelo nome de RF11 ocorre no navegador; a API DELETE verifica a propriedade e aplica exclusão lógica, mas não recebe o nome de confirmação. O limite superior de dez fornecedores é validado pela API e por “Selecionar todos”; a marcação manual não limita a seleção no frontend caso o catálogo venha a exceder os dez fornecedores do seed.

## Modelo de dados

O schema e as contagens da instância de auditoria confirmam oito tabelas de negócio mais `schema_migrations`, sete chaves estrangeiras, cinco restrições UNIQUE além das PKs e seis CHECKs. O SQL define duas PKs compostas, relações N:N fornecedor/categoria e fornecedor/produto, moeda em DECIMAL(12,2), conexões em utf8mb4 e timestamps em UTC.

Categorias não são persistidas na lista; não há tabelas de comparações ou histórico na implementação atual. A Figura 2 está alinhada às entidades e aos campos do schema. A Figura 1 mantém rótulos como “API Mock”, que merecem atualização para “catálogo interno/MySQL” para evitar ambiguidade, embora o texto já explique que se trata de recursos internos.

## Validação executada nesta revisão

| Verificação | Resultado |
|---|---|
| Backend com MySQL real | **31 testes passaram**, 18,80 s; MySQL 8.0.46 na porta 33307 |
| Cobertura de domínio e casos de uso, incluindo branches | **97,61%**, confirmando o número da monografia |
| Frontend | **7 testes passaram** |
| Ruff lint e formatação | Aprovados; 25 arquivos formatados |
| Contrato OpenAPI | `python -m backend.export_openapi --check` aprovado |
| Compose | `docker compose config --quiet` aprovado com variáveis temporárias de validação |
| Chromium, 1440 × 1000 | Lista de visitante, CSV, comparação com 10 fornecedores, invalidação após edição e ausência de melhor oferta com estoque insuficiente; nenhum erro JavaScript |
| Impressão | Navegação invisível em mídia de impressão; A4 definido no CSS. Não foi produzida impressão física |
| Desempenho local | 30 amostras por endpoint, concorrência 1: catálogo p95 **116,14 ms**; comparação p95 **105,91 ms** |

O backend foi testado no banco separado `cobeco_monografia_20260913_test`, criado para esta revisão na instância local de testes. Os testes da aplicação geraram somente dados de auditoria nessa base. O percurso no navegador usou a aplicação já disponível em `http://localhost:8000`, com rascunho local e consultas públicas; foi conferido que o módulo de comparação servido correspondia ao arquivo do projeto.

Os tempos 124,83 ms e 118,45 ms da monografia também constam no artefato histórico `.local-test/benchmark.json`. As novas medições abaixo de 500 ms são coerentes com esse resultado, mas a chamada mais lenta do catálogo nesta revisão levou 2180,35 ms. A meta documentada é percentil 95, não um teto para todas as chamadas.

O daemon Docker estava indisponível, portanto build e inicialização de contêineres não foram executados; a execução remota do GitHub Actions também não foi consultada. A suíte apresentou dois avisos de depreciação de bibliotecas de teste, sem falhas. Nenhum resultado parcial anterior, com integração ignorada ou ambiente ainda não configurado, foi usado como validação final.

## Prioridade de adequação

1. Resolver o comportamento alternativo de recuperação para alinhar a API ao RF04.
2. Corrigir ou contextualizar a Figura 3 e inserir a Figura 4.
3. Ajustar o critério de segurança e as frases sobre autenticação, sessão, exclusão de usuários e versão OpenAPI.
4. Para comprovar toda a infraestrutura e apresentação, executar Docker/CI e registrar a avaliação visual e de usabilidade com o escopo correspondente.
