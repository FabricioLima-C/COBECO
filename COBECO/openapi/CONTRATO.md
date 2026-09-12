# Contrato HTTP v3.1 — antes da implementação

Prefixo `/api`; JSON snake_case; IDs inteiros positivos; erros `{error: {code, message}}`. Autenticação Bearer nos endpoints privados, refresh em cookie httpOnly SameSite=Strict. Valores monetários como strings decimais com duas casas.

| Método / caminho | Acesso | Entrada / resultado |
|---|---|---|
| GET /health | Público | Verifica MySQL; 503 se indisponível |
| GET /api/config | Público | recovery_mode |
| POST /api/auth/register | Público | username, name, email, password, confirm_password, security_question, security_answer; usuário 201 |
| POST /api/auth/login | Público | username, password; access_token e user; cookie refresh |
| POST /api/auth/refresh | Cookie | Rotação; access_token e user |
| POST /api/auth/logout | Cookie | Revoga refresh; limpa cookie; 204 |
| POST /api/auth/recovery | Público | username; pergunta ou confirmação genérica de log |
| POST /api/auth/recovery/verify | Público | username, answer; valida resposta e retorna token de uso único/15 min para a terceira etapa |
| POST /api/auth/reset | Público | username, answer ou token, new_password, confirm_password; 204 |
| GET /api/profile | Privado | Perfil sem hashes/segredos |
| PATCH /api/profile | Privado | name, email, current_password, new_password opcional; perfil; mudança de senha encerra sessão |
| GET /api/categories | Público | Categorias macro de fornecedores |
| GET /api/products?q= | Público | Termo 2–100 caracteres; até 10 produtos ativos |
| POST /api/suppliers/availability | Público | items[{product_id,quantity}], category_id opcional; fornecedores ativos com cobertura |
| POST /api/compare | Público | items, supplier_ids (2–10 distintos); rows, best_supplier_ids, tied; sem persistência |
| GET /api/lists?page=1&q= | Privado | items (incluindo item_count), total, page, page_size=20; criação DESC |
| POST /api/lists | Privado | name 1–100, items 1–100; transação; lista 201 |
| GET /api/lists/{id} | Privado | Lista do proprietário ou 404 |
| PUT /api/lists/{id} | Privado | Substituição atômica do nome/itens; lista |
| DELETE /api/lists/{id} | Privado | Soft delete; 204 |

Quantidade inteira 1–9999. Produto obrigatório, ativo e distinto. Categoria não limita produtos. Sem endpoint CSV, histórico ou compartilhamento. Falhas de validação 422; sessão inválida 401; rate limit 429 com Retry-After; duplicidade 409. Origin é validada nas mutações com cookies. OpenAPI JSON gerado e versionado deve refletir este contrato.
