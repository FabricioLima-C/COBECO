# Decisões implementadas — COBECO v3.1 / MySQL

**Atualização:** 12/09/2026. Implementação baseada nos RF01–RF17 e nos ADRs recebidos, com substituição de SQLite por **MySQL**, determinada pelo usuário e registrada também no commit `611d558`. Layout baseado no arquivo [COBECO_figma_RF01_RF17_v2.html](COBECO_figma_RF01_RF17_v2.html), recebido nesse commit.

## Stack e operação

| Área | Implementação |
|---|---|
| Frontend | HTML/CSS/JavaScript ES modules, sem build obrigatório; markup e CSS extraídos do protótipo aprovado |
| Backend | Python 3.12, FastAPI, schemas Pydantic de entrada e saída |
| Banco | MySQL 8.4/InnoDB no Compose/CI; compatibilidade testada localmente com MySQL 8.0.46 |
| Acesso a dados | PyMySQL, SQL parametrizado, transações explícitas e FKs/UNIQUE/CHECK |
| Arquitetura | Domain → Usecases → Adapters → Routers; composição em `backend/main.py` |
| Autenticação | JWT; bcrypt custo 12 sobre SHA-256 hexadecimal; access 15 min e refresh 7 dias |
| Exportação | CSV no navegador; UTF-8/BOM, `;`, aspas e proteção de células interpretadas como fórmulas |
| Qualidade | pytest/pytest-cov, ruff, testes JavaScript com Node e CI com serviço MySQL |
| Execução | API serve também o frontend na porta 8000; uma instância/worker |

O novo serviço e banco não apagam nem importam automaticamente a aplicação PostgreSQL anterior. A referência anterior à migração é `d1f9e50`; veja [LEGADO.md](COBECO/LEGADO.md). Os arquivos npm/Prisma antigos estão preservados e excluídos da imagem nova.

## ADRs consolidados

- **ADR-001:** interface em módulos ES6. A referência visual posterior do usuário prevalece sobre a antiga entrada direta na criação: a página inicial é a landing page do protótipo, com acesso público a “Criar minha lista”. Os nove estados/telas principais e modais seguem o modelo. Dados de exemplo na landing são ilustrações; catálogo, conta, listas e comparações usam a API.
- **ADR-002:** FastAPI/Pydantic com contratos de entrada/saída, `/docs` e `/openapi.json`. Contrato inicial em `COBECO/openapi/CONTRATO.md`; JSON exportado versionado e verificado no CI.
- **ADR-003, revisado pelo usuário:** MySQL/InnoDB substitui SQLite/WAL. Conexões usam utf8mb4 e UTC. Moeda usa DECIMAL; schema versionado, volume persistente e seed idempotente. Oito tabelas de negócio e uma tabela técnica `schema_migrations`. DDL MySQL faz commit implícito; migrations usam lock e registro de conclusão, não uma promessa de rollback de DDL.
- **ADR-004, esclarecido:** access apenas em memória e refresh cookie httpOnly/SameSite Strict. Hash do refresh e versão em `users` permitem uma sessão por conta, rotação e revogação, sem tabela de sessões. Login novo invalida a sessão anterior; logout, reset e troca de senha revogam os tokens. Cookie Secure em produção HTTPS. Armazenamento em memória reduz persistência de tokens, sem prometer imunidade a XSS.
- **ADR-005:** CSV de lista funciona sem login e sem comparação prévia. Impressão A4 de lista ou resultados. O navegador controla download e impressora; a aplicação não promete detectar disco cheio ou impressora offline.
- **ADR-006:** recuperação acadêmica por pergunta ou log de desenvolvimento. A tela por pergunta tem três etapas: identificar conta, verificar resposta no servidor e redefinir senha com token de uso único de 15 min. Modo log é proibido em `APP_ENV=production`. Não há e-mail real.

## Regras de negócio resolvidas

1. **Rascunho:** `sessionStorage` por aba; login cancelado ou salvamento com erro preserva os itens. Seleção de fornecedores e tokens ficam em memória. Ao entrar, o usuário pode promover o rascunho. Trocar conta salva uma nova cópia, sem alterar a lista de outro proprietário.
2. **Categoria:** classificação macro de fornecedor N:N, usada como filtro transitório. Produto não pertence a categoria. Filtro vazio consulta todos os fornecedores; não escolhe implicitamente a primeira categoria.
3. **Lista:** nome obrigatório até 100 caracteres, 1–100 produtos ativos distintos, quantidade inteira 1–9999. Interface soma itens repetidos sem exceder limite; servidor rejeita duplicatas. Salvamento lista+itens é atômico. Exclusão lógica e consultas por proprietário.
4. **Disponibilidade:** oferta ativa e estoque suficiente para toda a quantidade. Item sem oferta/estoque suficiente é ausente. Não há compra fracionada nem promessa de reserva de estoque.
5. **Comparação:** 2–10 fornecedores ativos distintos. Uma linha por fornecedor, soma de preço × quantidade, cobertura e ausências. Ordenação pelo total; fornecedores sem oferta ficam no fim com N/D. Melhor oferta considera maior cobertura e, entre essas, menor total. Empates são destacados; total parcial é identificado. Essa regra evita indicar fornecedor sem produtos como a compra mais barata.
6. **Cache:** cinco minutos no frontend por itens/quantidades/seleção. Mudanças invalidam cache/resultados e cancelam requisições antigas. Timeout de 10 segundos. Comparações não são gravadas no banco.
7. **Tentativas:** seis falhas de login por identificador e IP bloqueiam por 15 minutos a partir da sexta falha. Sucesso limpa a contagem da conta; não limpa a contagem compartilhada do IP. Recuperação permite três falhas por 15 minutos. Limite geral de 100 requisições/minuto por IP; memória local, uma instância. Reinício limpa contadores.
8. **Perfil:** username somente leitura. Nome/e-mail/senha exigem senha atual; e-mail único e nova senha diferente. Senha nova é confirmada na interface e validada no servidor.

## Dados de demonstração

5 categorias, 10 fornecedores fictícios, 50 produtos, 20 vínculos fornecedor/categoria e 294 ofertas. Estoque e preços são determinísticos; o produto 10 não possui oferta. CNPJs são identificadores fictícios do seed, não registros de empresas reais. Conta demo só é criada se `SEED_DEMO_PASSWORD` for configurada; não sobrescreve usuário/senha existente ao repetir seed.

## Escopo e documentação

Implementados RF01–RF17, com rastreabilidade e verificações em [TAREFAS.md](TAREFAS.md). Histórico, compartilhamento, integrações de preços externas, notificações, IA e mobile permanecem fora do fluxo atual. BDD/E2E antigos não são exigências do CI novo; a inspeção de navegador desta migração foi usada para verificar o fluxo e os layouts.

O relatório anterior e suas assinaturas/estimativas permanecem no histórico Git. Esta revisão registra decisões e evidências de implementação; não representa assinatura acadêmica dos stakeholders. Tempo de CI remoto, build/execução Docker e transferência de dados antigos devem ser distinguidos dos testes locais já executados.

Referências técnicas consultadas: [transações InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-transaction-model.html), [PyMySQL](https://pymysql.readthedocs.io/en/latest/user/examples.html), [testes FastAPI](https://fastapi.tiangolo.com/tutorial/testing/).
