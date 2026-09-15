# COBECO v3.2 — especificação de implementação

Data: 14/09/2026. Base documental: remoto `462a2fd`; base da aplicação: `611beba`.

Este documento consolida as decisões usadas na implementação incremental das tarefas V32. O estado de entrega está em `TAREFAS.md`; uma função descrita aqui só está entregue quando seu aceite estiver registrado. As instruções de instalação continuam no README.

## Escopo e compatibilidade

- FastAPI/Python, MySQL/InnoDB e HTML/CSS/JavaScript em módulos. Catálogo de demonstração próprio, sem email ou fornecedores externos.
- Visitantes selecionam categorias, montam listas, comparam e exportam; autenticação é exigida para persistência e perfil.
- RF01–RF18 e RNF01–RNF12 são a base v3.2. Textos remotos com React/NestJS/PostgreSQL, SQLite/WAL ou PDF fora do escopo são históricos e não orientam esta implementação.
- Recuperação por código individual permanece padrão e único modo de produção. Hashes de recuperação, revogação de sessão e migrations fazem parte do modelo físico e não devem ser removidos para reproduzir um DER incompleto.
- Contrato HTTP permanece em snake_case inglês e OpenAPI 3.1. Nomes de negócio em português não implicam renomear o JSON. A versão de OpenAPI é diferente da versão da aplicação.
- SQL em inglês, IDs BIGINT, preço DECIMAL(12,2), precisão de datas e collation atual serão preservados nesta primeira entrega. A adequação do DER/tamanhos e do seed é uma etapa própria com migration incremental e validação em banco isolado.

## Categorias — RF08, RF12 e RF13

1. Uma ou mais categorias distintas e existentes são obrigatórias para disponibilidade, comparação e salvamento. O campo HTTP é `category_ids`, lista de inteiros positivos estritos, com limite técnico de 100 categorias por pedido.
2. A seleção usa a **união**: um fornecedor de qualquer categoria escolhida aparece uma vez. A resposta inclui todas as suas categorias. Somente fornecedores ativos são elegíveis.
3. Categorias classificam fornecedores. Os produtos continuam independentes de categorias. Um produto sem oferta pode ser salvo e aparecer como ausente na comparação.
4. Antes de haver itens, `POST /api/suppliers/search` recebe apenas `category_ids` e retorna fornecedores e categorias, sem percentual fictício de disponibilidade. O percentual é calculado apenas quando há uma lista não vazia.
5. `POST /api/suppliers/availability` recebe `category_ids` e itens. `POST /api/compare` também recebe de 2 a 10 IDs de fornecedores distintos, todos pertencentes à união escolhida.
6. `POST /api/lists` e `PUT /api/lists/{id}` validam categorias e produtos na transação de salvamento. Categorias não são persistidas na lista.
7. Seleção de categorias fica somente em memória da aba. Recarregar exige selecionar novamente; o rascunho continua no sessionStorage. Abrir uma lista antiga preserva seus itens e solicita categorias antes de prosseguir quando a aba não tiver seleção. Não há migração das listas para usar este fluxo.
8. Alterar categorias limpa a seleção de fornecedores e os resultados. Alterar itens/quantidades invalida disponibilidade e comparação; filtros preservam apenas fornecedores que continuam elegíveis.
9. Todas as categorias cadastradas são selecionáveis. Não existe campo de categoria ativa no modelo atual; a referência remota a `categorias.ativo` fica fora desta entrega.

Exemplo: A pertence a Mercado e Informática, B apenas a Mercado, C apenas a Vestuário. Escolher Mercado e Informática retorna A e B uma vez cada. Enviar C à comparação retorna `INVALID_SUPPLIER`; enviar uma categoria inexistente retorna `CATEGORY_NOT_FOUND` (404). Uma lista antiga continua legível sem `category_ids`, mas uma nova gravação exige o campo.

### Atualização coordenada do cliente

`category_id` opcional é substituído por `category_ids` obrigatório. Pedidos antigos sem categorias retornam 422. Publicar API e frontend juntos e recarregar abas abertas; as respostas de listas existentes mantêm seu formato. Não se converte silenciosamente a ausência de categoria em seleção de todas.

## Comparação e limites — decisões para as próximas entregas

- Preservar melhor oferta por maior cobertura e, entre fornecedores com essa cobertura, menor total. Ordenar a tabela por total crescente, distinguir total parcial e destacar todos os empates elegíveis. Exemplo: 50%/R$ 5 fica antes de 100%/R$ 10, mas a melhor oferta é 100%/R$ 10. Corrigir a expressão remota “menor preço” para refletir essa regra.
- Manter tabela resumida por fornecedor, acrescentando detalhes de item ausente (produto, quantidade e motivo) na etapa correspondente. Matriz completa por produto/fornecedor fica fora deste incremento.
- Não apresentar subtotal ou valor estimado antes de definir uma oferta por fornecedor. Listas salvas são listas de produtos/quantidades, não snapshots de preços. Comparações usam o rascunho enviado, mesmo que sua lista de origem tenha sido excluída depois de aberta.
- Limites: 1–100 produtos distintos, quantidades inteiras 1–9999, 2–10 fornecedores. PDF deve paginar dentro desse limite. Listas acima de 100 itens e geração assíncrona de arquivos maiores que 10 MB não pertencem ao MVP; não aumentar os limites do corpo HTTP para atender a esses cenários.
- PDF público gerado no servidor será adicionado na etapa 5; CSV e impressão continuam disponíveis. PDF pelo diálogo de impressão não equivale à entrega de RF17.
- Cache de comparação no servidor e prazo de processamento permanecem pendentes. O cache atual de 5 minutos no cliente e timeout de 10 segundos da requisição não comprovam prazo total de execução do servidor.

## Erros, segurança e concorrência

- Lista alheia, inexistente ou excluída: 404. Página excessiva: última página disponível. Exclusão exige confirmação na interface e validação de propriedade no servidor.
- Uma sessão renovável por conta, revogável no servidor. Código/token de recuperação de uso único; sem divulgação da existência de contas ou da pergunta cadastrada.
- Edição concorrente de listas: última gravação válida vence, com transação e lock de escrita; não é controle otimista por versão.
- Limites atuais de autenticação permanecem até a etapa V32-19; não considerar os cenários novos certificados apenas pela documentação.

## Rastreabilidade deste incremento

| Requisito | Implementação prevista | Aceite |
| --- | --- | --- |
| RF12 / UC03 | Tela de categorias, `category_ids`, consulta pública anterior à lista | União sem duplicatas; categoria inválida/ausente rejeitada; seleção transitória |
| RF13 / UC04 | Fornecedores ativos da união de categorias | API rejeita fornecedor de categoria não selecionada, mesmo em pedido direto |
| RF08 / UC14 e UC17 | Categorias validadas ao salvar/promover rascunho | Escrita atômica; lista anterior legível; atualização exige seleção válida |

A renumeração global de UCs e sincronização dos diagramas permanecem na tarefa V32-02. Estes três IDs não colidem no conjunto usado neste incremento.
