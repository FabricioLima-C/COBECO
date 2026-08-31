# Escopo do projeto COBECO

## Objetivo

Desenvolver uma aplicação web que permita a usuários autenticados organizar listas de bens de consumo e comparar fornecedores por paridade de cobertura, identificando itens disponíveis, ausentes e o menor custo consolidado.

## Incluído no MVP

- cadastro, login, logout, recuperação de senha, consentimento e exclusão de conta;
- criação, edição, duplicação, exclusão e compartilhamento de listas;
- categorias e produtos normalizados em catálogo PostgreSQL;
- seleção dos fornecedores participantes da comparação;
- agrupamento por conjunto idêntico de itens disponíveis;
- percentual de cobertura, itens ausentes, total por fornecedor e menor custo consolidado do grupo;
- destaque do melhor grupo por maior cobertura e menor custo em caso de empate;
- persistência, reabertura, comparação e exclusão do histórico de cotações;
- exportação CSV e impressão/PDF pelo navegador;
- interface React responsiva, acessível por teclado e com tema claro/escuro;
- contrato OpenAPI e Swagger UI em `/docs`;
- execução em três serviços Docker: web, API e PostgreSQL;
- testes unitários, integração HTTP, BDD e E2E, executados na integração contínua quando aplicável.

## Fonte dos preços

O MVP usa preços determinísticos do catálogo seedado. O seed contém uma categoria, oito fornecedores e dez produtos, reproduzindo o cenário A–H da especificação. Provedores externos são extensão pós-MVP e ficam desativados por padrão.

## Fora do escopo do MVP

- pagamento, carrinho ou conclusão de compra;
- garantia de preço em tempo real ou estoque físico;
- aplicativo móvel nativo;
- autenticação social;
- alertas automáticos de queda de preço;
- painel administrativo completo para manutenção do catálogo;
- dependência obrigatória de APIs públicas de varejistas.

## Restrições

- demonstração em ambiente acadêmico e catálogo inicialmente limitado a supermercado;
- dados pessoais mínimos e senhas protegidas por Argon2;
- sessão renovável com janela máxima de 30 minutos sem atividade;
- HTTPS obrigatório na publicação em produção.
