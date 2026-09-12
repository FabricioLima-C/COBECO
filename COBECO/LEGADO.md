# Transição da aplicação anterior

O commit `d1f9e50` preserva a referência anterior à migração. O código de React/Express/Prisma permanece em `apps/` e `packages/`; o código atual usa `backend/` e `frontend/`. Os antigos arquivos npm são exclusivamente do legado. O Dockerfile atual copia somente o backend Python e o frontend estático.

## Dados

Nenhum banco, conta ou volume PostgreSQL existente foi apagado ou migrado automaticamente. O novo Compose cria outro volume MySQL. As migrations SQL atuais inicializam uma base MySQL vazia e não convertem o schema Prisma.

Caso seja necessário transportar dados reais do legado, a conversão deve ser uma tarefa própria, com backup e conferência de:

1. CUID → BIGINT e todas as referências de usuários, produtos, listas e itens.
2. Categorias de fornecedores → pivô N:N; remoção de categoria dos produtos.
3. Itens de descrição livre/sem produto → catálogo válido e consolidação de duplicados.
4. Senhas argon2 antigas → redefinição ou verificação compatível antes de gerar novo hash. O backend novo usa bcrypt de SHA-256 hexadecimal; não copie hashes sem indicar o formato.
5. Perguntas/respostas de segurança não existentes nas contas antigas → cadastro pelo titular; não inventar respostas.
6. Histórico de cotações, compartilhamentos e depoimentos → exportação histórica, pois não são tabelas da aplicação atual.

Não é seguro apenas trocar `provider = postgresql` para MySQL nas migrations Prisma antigas. O novo schema tem oito tabelas de negócio, índices/constraints e campos de sessão/recuperação em `users`, além de `schema_migrations`.

## Decisões de implantação

- MySQL 8.4 no Compose e CI; compatibilidade local testada com MySQL 8.0.46.
- Novo endereço padrão: http://localhost:8000. Não reutiliza portas 5173/3333 nem o volume PostgreSQL.
- Senhas do banco e JWT são configuradas por ambiente. Não há importação automática do `.env` do backend antigo.
- A API inicializa migrations/seed pelo entrypoint de Docker. No modo local, execute `python -m backend.seed` antes do Uvicorn.
- Rate limiting local exige uma instância/worker. Escalar para múltiplos processos exige armazenamento compartilhado para esses contadores.
