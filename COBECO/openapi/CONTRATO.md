# Contrato HTTP v3.2 — categorias múltiplas e segurança

Prefixo `/api`; JSON snake_case; IDs inteiros positivos; erros `{error: {code, message}}`. Autenticação Bearer nos endpoints privados, refresh em cookie httpOnly SameSite=Strict. Valores monetários como strings decimais com duas casas.

| Método / caminho | Acesso | Entrada / resultado |
|---|---|---|
| GET /health | Público | Verifica MySQL; 503 se indisponível |
| GET /api/config | Público | recovery_mode |
| POST /api/auth/register | Público | username, name, email, password, confirm_password; usuário e recovery_code exibido uma vez, 201; pergunta/resposta apenas no modo acadêmico |
| POST /api/auth/login | Público | username, password; access_token e user; cookie refresh |
| POST /api/auth/refresh | Cookie | Rotação; access_token e user |
| POST /api/auth/logout | Cookie | Revoga refresh; limpa cookie; 204 |
| POST /api/auth/recovery | Público | username; instrução genérica igual para contas existentes/inexistentes, sem revelar pergunta |
| POST /api/auth/recovery/verify | Público | username, answer (código individual em modo code); retorna token de uso único/15 min para a terceira etapa |
| POST /api/auth/reset | Público | username, token obrigatório, new_password, confirm_password; 204; consome código e revoga sessões |
| GET /api/profile | Privado | Perfil sem hashes/segredos |
| PATCH /api/profile | Privado | name, email, current_password, new_password opcional; perfil; mudança de senha encerra sessão |
| POST /api/profile/recovery-code | Privado | current_password; recovery_code novo, invalida código anterior e token de reset pendente |
| GET /api/categories | Público | Categorias macro de fornecedores |
| GET /api/products?q= | Público | Termo 2–100 caracteres; até 10 produtos ativos |
| POST /api/suppliers/search | Público | category_ids (1–100 distintos); fornecedores ativos da união, com id, name e categories; não exige itens |
| POST /api/suppliers/availability | Público | items[{product_id,quantity}], category_ids obrigatório; fornecedores ativos com cobertura e categorias |
| POST /api/compare | Público | items, category_ids, supplier_ids (2–10 distintos pertencentes às categorias); rows, best_supplier_ids, tied; sem persistência |
| GET /api/lists?page=1&q= | Privado | items (incluindo item_count), total, page, page_size=20; criação DESC |
| POST /api/lists | Privado | name 1–100, items 1–100, category_ids; validação de categorias e produtos na transação; lista 201 |
| GET /api/lists/{id} | Privado | Lista do proprietário ou 404 |
| PUT /api/lists/{id} | Privado | name, items, category_ids; substituição atômica do nome/itens; categorias transitórias |
| DELETE /api/lists/{id} | Privado | Soft delete; 204 |

Quantidade inteira 1–9999. Produto obrigatório, ativo e distinto. Categoria não limita produtos. Sem endpoint CSV, histórico ou compartilhamento. Falhas de validação 422; sessão inválida 401; rate limit 429 com Retry-After; duplicidade 409. Origin é validada nas mutações com cookies. OpenAPI JSON gerado e versionado deve refletir este contrato.

`category_ids` contém de 1 a 100 inteiros positivos distintos. IDs inexistentes retornam 404 (`CATEGORY_NOT_FOUND`). A união das categorias não duplica fornecedores. Fornecedor inativo, inexistente ou fora da união retorna 422 (`INVALID_SUPPLIER`) ao comparar. Listas lidas continuam sem categorias, pois a seleção não é persistida. `category_id` antigo e pedidos de comparação/salvamento sem categorias retornam 422: atualizar frontend e API juntos. Regras consolidadas em [ESPECIFICACAO_V32.md](../../ESPECIFICACAO_V32.md).

Corpo HTTP limitado a 64 KiB: excesso retorna 413; envio acima de 10 s retorna 408. O modo padrão é `code`; produção rejeita `question`, `log` e habilitação da conta demo. A conta demo existente não pode recuperar senha nem autenticar em produção. Rotas com código de recuperação respondem com `Cache-Control: no-store`. Códigos são aleatórios de 256 bits e somente seu SHA-256 é persistido em `recovery_codes`.
