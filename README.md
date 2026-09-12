# COBECO — comparação de listas de compras

Aplicação acadêmica com **Python 3.12/FastAPI, MySQL/InnoDB e HTML/CSS/JavaScript em módulos**. MySQL substitui a decisão anterior de SQLite por orientação do usuário. A aplicação atual está em `COBECO/backend` e `COBECO/frontend`.

Visitantes podem criar listas, escolher fornecedores, comparar disponibilidade/preços, exportar CSV e imprimir. A autenticação é exigida para salvar, consultar ou editar listas pessoais e gerenciar o perfil.

## Executar com Docker

```powershell
cd COBECO
Copy-Item .env.example .env
# Edite .env: defina MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD e JWT_SECRET próprios.
docker compose up --build
```

Interface: http://localhost:8000 · API/Swagger: http://localhost:8000/docs · Contrato: http://localhost:8000/openapi.json

O Compose sobe MySQL 8.4 e a API, que aplica migrations e seed antes de servir o frontend. O banco usa volume `mysql_data`. Não use `down -v` se deseja preservar seus dados. `APP_ORIGIN` deve corresponder à URL usada no navegador; o padrão é `http://localhost:8000`. Para publicar em HTTPS, configure `APP_ENV=production` e o endereço HTTPS em `APP_ORIGIN`.

O seed contém 5 categorias macro, 10 fornecedores fictícios, 50 produtos, 20 vínculos de categoria e 294 ofertas. Para criar a conta `demo`, defina `SEED_DEMO_PASSWORD` com senha forte; a resposta de segurança dessa conta é `cobeco`. Não há senha de demonstração padrão.

## Executar sem Docker

É necessário um servidor MySQL 8.0.16+ (recomendado 8.4) disponível. Crie um banco vazio e um usuário com permissões apenas sobre ele, usando `utf8mb4`. Não aponte a instalação para a base PostgreSQL antiga.

```powershell
cd COBECO
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Configure conexão MySQL, JWT_SECRET e APP_ORIGIN no .env.
.\.venv\Scripts\python -m backend.seed
.\.venv\Scripts\python -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

As variáveis de ambiente prevalecem sobre `.env`. Migrations estão em `backend/migrations`; são aplicadas por ordem e registradas em `schema_migrations`. Há oito tabelas de negócio e uma tabela técnica de migrations. DDL MySQL não é transacional; o runner usa lock e só registra a versão após concluir os comandos idempotentes.

## Comportamento da aplicação

- Rascunho preservado no `sessionStorage` da aba, inclusive durante login. Seleção e access token ficam em memória. Ao entrar, o usuário escolhe salvar ou manter o rascunho.
- Produtos independem de categorias; categorias filtram fornecedores, que podem pertencer a várias. Sem filtro, todos os fornecedores ativos aparecem.
- Estoque deve atender a quantidade inteira. A tabela ordena por total disponível e identifica valores parciais; a melhor oferta considera maior cobertura, depois menor total. Empates são destacados; fornecedor sem itens recebe N/D.
- Listas salvas têm produtos distintos, quantidades de 1–9999, nome de até 100 caracteres, busca e paginação de 20. Exclusão lógica exige digitar o nome.
- CSV é produzido no navegador com BOM, `;` e nome `lista_YYYYMMDD.csv`. Impressão usa A4.
- Cadastro por username alfanumérico, confirmação de senha e pergunta de segurança. Perfil exige senha atual em qualquer alteração.
- Access JWT: 15 minutos; refresh: 7 dias em cookie httpOnly/SameSite Strict. Uma sessão renovável por conta; login novo substitui a sessão anterior. Logout, reset e mudança de senha invalidam a sessão no servidor.
- Login: seis falhas por identificador/IP bloqueiam por 15 minutos. Recuperação: três falhas por 15 minutos. O limitador é em memória; execute **um worker**. Reiniciar a API limpa esses contadores.
- Recuperação acadêmica: `RECOVERY_MODE=question` (padrão) ou `log` em desenvolvimento. No modo log, o link tem token de uso único, válido por 15 minutos. Não há serviço de e-mail.

## Validação

```powershell
cd COBECO
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
node --test frontend/tests/*.test.mjs
.\.venv\Scripts\python -m backend.export_openapi --check
```

Para testes de integração, configure **um banco isolado com nome terminado em `_test`**, em vez da base de uso normal:

```powershell
$env:MYSQL_TEST='1'
$env:MYSQL_DATABASE='cobeco_test'
# Configure as demais MYSQL_* para a instância de teste.
.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-report=xml
```

Os testes não usam SQLite: domínio/validação são puros e integração executa MySQL real. O CI inclui MySQL 8.4, ruff, pytest, cobertura mínima de 80% em domínio/casos de uso, testes JavaScript, comparação do OpenAPI versionado e build Docker.

## Documentos e legado

O layout segue o [modelo HTML recebido do Figma](COBECO_figma_RF01_RF17_v2.html), atualizado pelo pull até `611d558`. A extração reproduzível está em `scripts/sync_figma_layout.py`; estilos e markup são preservados, enquanto os módulos da aplicação substituem os dados e autenticação simulados do protótipo.

- [Tarefas e validações](TAREFAS.md)
- [Decisões implementadas](relatorio_analitico_COBECO.md)
- [Requisitos e casos de uso](analise_REQ_CasosDeUso.md)
- [DER MySQL](diagrama_DER.md)
- [Contrato da API](COBECO/openapi/CONTRATO.md)
- [Transição e dados antigos](COBECO/LEGADO.md)

`COBECO/apps`, `COBECO/packages` e seus arquivos npm/Prisma são a implementação anterior preservada. Não integram o Dockerfile ou o CI atuais. Documentos de `brain`, `prj_docs` e a monografia podem descrever decisões anteriores; a referência de execução é este README e os documentos acima. Histórico, compartilhamento, integrações externas e paridade não fazem parte do fluxo atual.
