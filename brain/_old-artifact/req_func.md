# Requisitos funcionais — COBECO

Fonte normativa: `objetivos.md`, ajustada pelas decisões arquiteturais registradas em `decisoes.md`.

| Código | Requisito |
|---|---|
| RF01 | Permitir cadastro com nome, e-mail único, senha e consentimento. |
| RF02 | Autenticar por e-mail e senha e direcionar à área logada. |
| RF03 | Encerrar a sessão com segurança. |
| RF04 | Solicitar e concluir redefinição de senha. |
| RF05 | Proteger todas as rotas da plataforma. |
| RF06 | Criar listas nomeadas vinculadas a uma categoria. |
| RF07 | Incluir item com produto normalizado ou descrição livre, categoria herdada da lista e quantidade. |
| RF08 | Editar o nome da lista e editar/remover seus itens. |
| RF09 | Duplicar uma lista e seus itens. |
| RF10 | Excluir lista após confirmação. |
| RF11 | Exibir listas do usuário com itens e datas. |
| RF12 | Solicitar cotação de todos os itens de uma lista. |
| RF13 | Agrupar fornecedores que possuam exatamente o mesmo conjunto de itens disponíveis, exibindo o percentual de cobertura. |
| RF14 | Calcular, por grupo, totais individuais e o menor custo consolidado por item. |
| RF15 | Destacar o grupo de maior cobertura e, em caso de empate, menor custo consolidado. |
| RF16 | Listar os itens ausentes em cada grupo. |
| RF17 | Permitir incluir ou excluir fornecedores da comparação. |
| RF18 | Apresentar painel com fornecedores, cobertura, preços, itens ausentes e orçamento consolidado. |
| RF19 | Persistir cotações, data/hora, grupos e resultado destacado. |
| RF20 | Visualizar e reabrir cotações anteriores. |
| RF21 | Excluir registros do histórico pertencentes ao usuário. |
| RF22 | Informar quando nenhum fornecedor ou oferta válida for encontrado. |
| RF23 | Sinalizar produto não mapeado ou indisponível. |
| RF24 | Validar nome, quantidade, categoria e seleção de fornecedores antes da cotação. |

## Critério de agrupamento

```text
para cada fornecedor selecionado s:
    cobertura[s] = itens da lista com oferta ativa em s
agrupar fornecedores cuja cobertura seja o mesmo conjunto
ordenar por: mais itens, mais fornecedores, ordem alfabética
calcular itens ausentes = itens da lista - cobertura do grupo
```
