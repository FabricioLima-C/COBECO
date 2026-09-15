# COBECO — comparação de listas de compras

O **COBECO (Cotação de Bens de Consumo)** é uma aplicação web acadêmica para montar listas de compras e comparar seu custo e cobertura entre fornecedores. Destina-se a consumidores, pequenos empresários, estudantes e profissionais que planejam compras de múltiplos itens, com interface voltada ao uso em desktop.

A implementação utiliza **Python 3.12/FastAPI, MySQL/InnoDB e HTML/CSS/JavaScript em módulos** e está em `COBECO/backend` e `COBECO/frontend`. Preços e estoques vêm de catálogo próprio com carga determinística, permitindo uma demonstração reproduzível e independente de serviços externos. O objetivo, o escopo e a modelagem estão descritos na [monografia atualizada](Monografia%20e%20Demais%20Docs/COBECO_Monografia_new.docx).

Visitantes podem criar listas, escolher fornecedores, comparar disponibilidade/preços, exportar CSV e imprimir. A autenticação é exigida para salvar, consultar ou editar listas pessoais e gerenciar o perfil.

## Escopo do MVP

O fluxo principal consiste em selecionar **uma ou mais categorias de fornecedores**, montar a lista com produtos do catálogo, selecionar de **2 a 10 fornecedores ativos** dessas categorias, comparar os resultados e identificar a melhor oferta. A comparação apresenta custo total, percentual de cobertura e itens ausentes por fornecedor; a melhor oferta prioriza a **maior cobertura** e, em seguida, o **menor custo total**.

A implementação incremental v3.2 está registrada em [TAREFAS.md](TAREFAS.md), com regras consolidadas em [ESPECIFICACAO_V32.md](ESPECIFICACAO_V32.md). O primeiro incremento entrega categorias múltiplas na interface e API. PDF no servidor, seed de 11 categorias e demais adequações continuam pendentes conforme o checklist. A monografia abaixo descreve a entrega anterior.

A monografia organiza o projeto em **17 requisitos funcionais (RF01–RF17)**, **10 não funcionais (RNF01–RNF10)** e **26 casos de uso (UC01–UC26)**, abrangendo conta e autenticação, perfil, gestão de listas, fornecedores, comparação, exportação e impressão.

Compras, pagamentos, garantia de preço em tempo real, integração com fornecedores reais, aplicativo móvel nativo, autenticação por contas de terceiros, envio de e-mail e persistência do histórico de comparações estão fora do MVP.

Os oito requisitos desejáveis (RD01–RD08) contemplam histórico de comparações, importação de listas por CSV, alertas de preço, compartilhamento e colaboração, aplicação progressiva ou móvel, integração com fornecedores reais, sugestões por inteligência artificial e suporte a idiomas e moedas adicionais.

## Executar com Docker

```powershell
cd COBECO
Copy-Item .env.example .env
# Edite .env: defina MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD e JWT_SECRET próprios.
docker compose up --build
```

Interface: http://localhost:8000 · API/Swagger: http://localhost:8000/docs · Contrato: http://localhost:8000/openapi.json

O Compose sobe MySQL 8.4 e a API, que aplica migrations e seed antes de servir o frontend. O banco usa volume `mysql_data`. Não use `down -v` se deseja preservar seus dados. A porta da API fica restrita a `127.0.0.1`. `APP_ORIGIN` deve corresponder à origem usada no navegador, sem caminho ou barra final; o padrão é `http://localhost:8000`. Para publicar, configure um proxy HTTPS, `APP_ENV=production`, a origem HTTPS em `APP_ORIGIN` e `RECOVERY_MODE=code`. O Compose não fornece TLS por conta própria.

O seed contém 5 categorias macro, 10 fornecedores fictícios, 50 produtos, 20 vínculos de categoria e 294 ofertas. `SEED_DEMO_PASSWORD` permite criar a conta `demo` somente em desenvolvimento. Essa conta não permite recuperação de senha e não pode autenticar em produção. Não há senha de demonstração padrão. Senhas e segredo JWT do exemplo devem ser substituídos; a aplicação rejeita a chave JWT de exemplo.

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

As variáveis de ambiente prevalecem sobre `.env`. Migrations estão em `backend/migrations`; são aplicadas por ordem e registradas em `schema_migrations`. Há oito tabelas de negócio, a tabela técnica de migrations e `recovery_codes`, que guarda somente o hash do código de recuperação de cada usuário. DDL MySQL não é transacional; o runner usa lock e só registra a versão após concluir os comandos idempotentes.

### Atualização de segurança e contas existentes

Antes de usar a versão corrigida, aplique as migrations com `python -m backend.seed` (automático no Docker) e reinicie a API. A migration `002_recovery_codes.sql` adiciona a tabela sem alterar ou excluir listas/usuários existentes. Configure `RECOVERY_MODE=code`; contas existentes devem entrar com sua senha atual e usar **Perfil → Gerar código de recuperação**. Guarde o código fora do navegador, preferencialmente em um gerenciador de senhas. Ele é mostrado uma única vez e pode ser baixado pelo usuário.

Novos cadastros recebem um código aleatório individual. Recuperar a senha consome o código; depois de entrar, gere outro no perfil. Gerar outro código invalida o anterior e pedidos de recuperação pendentes. Alterar a senha também invalida o código anterior. Uma conta antiga sem código e sem a senha atual precisa de atendimento administrativo com verificação de identidade; não há bypass público por pergunta no modo seguro.

Para gerar uma chave JWT própria, execute `python -c "import secrets; print(secrets.token_urlsafe(48))"` e guarde o resultado no `.env`. Se uma instalação já utilizou uma chave pública/de exemplo, substitua-a; os tokens antigos deixam de ser aceitos. A monografia antecede estas correções: recuperação por código e a tabela adicional são descritas no [relatório de segurança](seguranca_COBECO.md).

## Comportamento da aplicação

- Rascunho preservado no `sessionStorage` da aba, inclusive durante login. Seleção e access token ficam em memória. Ao entrar, o usuário escolhe salvar ou manter o rascunho.
- Produtos independem de categorias; fornecedores podem pertencer a várias. A seleção obrigatória de uma ou mais categorias mostra a união de fornecedores ativos, sem duplicatas. Antes de montar a lista, a tela permite consultar seus nomes; a disponibilidade é calculada depois de adicionar itens.
- A seleção aceita de 2 a 10 fornecedores ativos distintos pertencentes às categorias escolhidas, com filtro opcional por percentual mínimo de disponibilidade. Categorias e fornecedores ficam em memória da aba; recarregar exige selecionar categorias novamente, preservando o rascunho. Comparações não são persistidas.
- Estoque deve atender a quantidade inteira. A tabela ordena por total disponível e identifica valores parciais; a melhor oferta considera maior cobertura, depois menor total. Empates são destacados; fornecedor sem itens recebe N/D.
- Listas salvas têm produtos distintos, quantidades de 1–9999, nome de até 100 caracteres, busca e paginação de 20. Exclusão lógica exige digitar o nome.
- Salvar e comparar exigem `category_ids` válido na API. Categorias não são gravadas na lista: listas anteriores continuam legíveis, e a interface solicita seleção ao abri-las se a aba não tiver categorias escolhidas. Alterar categorias limpa fornecedores selecionados e resultados anteriores.
- CSV é produzido no navegador com BOM, `;` e nome `lista_YYYYMMDD.csv`. Impressão usa A4.
- Cadastro por username alfanumérico, confirmação de senha e entrega de código individual de recuperação. Perfil exige senha atual nas alterações e na geração de outro código.
- Access JWT: 15 minutos; refresh: 7 dias em cookie httpOnly/SameSite Strict. Uma sessão renovável por conta; login novo substitui a sessão anterior. Logout, reset e mudança de senha invalidam a sessão no servidor.
- Login: seis falhas por identificador/IP bloqueiam por 15 minutos. Recuperação: três falhas por 15 minutos. O limitador é em memória; execute **um worker**. Reiniciar a API limpa esses contadores.
- Recuperação: `RECOVERY_MODE=code` é o padrão e o único modo permitido em produção. A verificação do código gera um token de uso único válido por 15 minutos; `/auth/reset` sempre exige esse token. `question` e `log` são opções legadas de desenvolvimento; a resposta pública não revela a pergunta cadastrada. Não há serviço de e-mail.
- Corpo HTTP limitado a 64 KiB antes do processamento de JSON, inclusive sem `Content-Length`; tempo total de envio de 10 segundos. O Docker limita a concorrência a 64 conexões/tarefas. As reservas do limitador não mantêm lock global durante bcrypt ou SQL; o armazenamento continua local a um único processo.

## Validação

### Atualização do contrato de categorias

API e frontend devem ser atualizados juntos. Reinicie a API e recarregue as abas após esta atualização: o campo opcional `category_id` foi substituído por `category_ids` obrigatório em disponibilidade, comparação e salvamento. Clientes antigos recebem 422. Este incremento não exige migration ou nova carga de seed.

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

O CI também executa pip-audit, Bandit para achados de severidade alta e npm audit do lockfile legado. Os alertas médios de SQL dinâmico do Bandit foram revisados: os valores são parametrizados e os identificadores são controlados internamente.

### Resultados registrados na monografia

A monografia relata 31 testes no backend, com 97,61% de cobertura em domínio e casos de uso, e 7 testes no frontend, além de análise estática, conferência do contrato OpenAPI e validação do Compose. Registra também o fluxo completo em navegador a 1440 × 1000 pixels, sem erros de JavaScript.

As medições locais relatadas apresentam percentil 95 de 124,83 ms no catálogo e 118,45 ms na comparação, frente à meta de 500 ms. A amostra foi de 30 requisições com concorrência unitária e não caracteriza teste sob carga. Esses números documentam a validação descrita na monografia; não representam uma nova execução dos testes a cada atualização deste README.

## Documentos e legado

O layout segue o [modelo HTML recebido do Figma](COBECO_figma_RF01_RF17_v2.html), atualizado pelo pull até `611d558`. A extração reproduzível está em `scripts/sync_figma_layout.py`; estilos e markup são preservados, enquanto os módulos da aplicação substituem os dados e autenticação simulados do protótipo.

- [Monografia — objetivo, escopo, requisitos, casos de uso, DER, protótipos, tecnologias e considerações finais](Monografia%20e%20Demais%20Docs/COBECO_Monografia_new.docx)
- [Tarefas e validações](TAREFAS.md)
- [Decisões implementadas](relatorio_analitico_COBECO.md)
- [Requisitos e casos de uso](analise_REQ_CasosDeUso.md)
- [DER MySQL](diagrama_DER.md)
- Diagramas editáveis: [casos de uso](uc.drawio) e [entidade-relacionamento](der.drawio)
- [Contrato da API](COBECO/openapi/CONTRATO.md)
- [Transição e dados antigos](COBECO/LEGADO.md)

`COBECO/apps`, `COBECO/packages` e seus arquivos npm/Prisma são a implementação anterior preservada. Não integram o Dockerfile ou o CI atuais. Documentos de `brain` e `prj_docs` podem descrever decisões anteriores; a monografia atualizada documenta o MVP em FastAPI/MySQL, e as instruções de execução estão neste README. Histórico, compartilhamento, integrações externas e agrupamento por paridade não fazem parte do fluxo atual.
