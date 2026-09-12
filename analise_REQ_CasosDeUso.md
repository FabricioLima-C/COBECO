# Requisitos e casos de uso — COBECO v3.1 / MySQL

**Atualização:** 12/09/2026. Referência de implementação: [decisões consolidadas](relatorio_analitico_COBECO.md). MySQL é a escolha expressa do usuário. A referência visual posterior é [COBECO_figma_RF01_RF17_v2.html](COBECO_figma_RF01_RF17_v2.html); a landing page desse modelo passa a ser a entrada, com criação de lista pública acessível pelo botão principal.

Esta revisão reconcilia a análise anterior com código e layouts. Evidências de execução ficam em [TAREFAS.md](TAREFAS.md), separadas de aprovação acadêmica e de testes ainda não realizados.

## Requisitos funcionais

| RF | Requisito e critério implementado | Tela / API |
|---|---|---|
| RF01 | Cadastro: username alfanumérico único 3–30; nome/e-mail; senha e confirmação; pergunta e resposta de segurança. Hash no servidor. | Cadastro; POST /api/auth/register |
| RF02 | Login por username/senha; seis falhas geram bloqueio de 15 min por identificador/IP; estados de carregamento, erro e bloqueio. | Login e modal de salvamento; POST /api/auth/login |
| RF03 | Logout revoga sessão no servidor e limpa cookie/token; preserva rascunho da aba. | Navegação; POST /api/auth/logout |
| RF04 | Recuperação em três etapas por pergunta, ou token do log em desenvolvimento; três erros/15 min; token de uso único/15 min. | Recuperar senha; /api/auth/recovery, /verify e /reset |
| RF05 | Visualizar perfil próprio com username somente leitura. | Perfil; GET /api/profile |
| RF06 | Alterar nome/e-mail/senha com senha atual; e-mail único; senha nova diferente e confirmada na interface. | Perfil; PATCH /api/profile |
| RF07 | Visitante cria rascunho local com nome e produtos do catálogo; quantidades 1–9999; autocomplete com debounce 300 ms/cache 5 min. | Nova lista; GET /api/products |
| RF08 | Salvar exige login; modal/promoção preserva rascunho; transação lista+itens; mínimo de um produto. | Nova lista e modais; POST /api/lists |
| RF09 | Minhas listas: criação DESC, busca por nome, 20/página; excluídas não aparecem. | Minhas listas; GET /api/lists |
| RF10 | Editar nome/itens/quantidades com propriedade verificada; confirmação para remover item. | Abrir/Editar lista; PUT /api/lists/{id} |
| RF11 | Excluir lista exige digitar nome; soft delete por proprietário. | Minhas listas e modal; DELETE /api/lists/{id} |
| RF12 | Selecionar 2–10 fornecedores distintos ativos; categoria opcional; seleção transitória. | Fornecedores; /api/suppliers/availability |
| RF13 | Slider 0–100%, padrão 0; preserva apenas selecionados ainda elegíveis. | Fornecedores |
| RF14 | Comparação pública por fornecedor, preço × quantidade, timeout 10 s e cache frontend 5 min; invalidação após edição. | POST /api/compare |
| RF15 | Tabela ordenada por total, cobertura/ausências, N/D, valores parciais e empate. Melhor oferta prioriza cobertura, depois custo. | Resultados |
| RF16 | CSV da lista funciona para visitante e autenticado, antes ou depois de comparar; BOM, `;`, escape e nome lista_YYYYMMDD.csv. | Nova lista e resultados |
| RF17 | Impressão A4 da lista ou resultados, sem navegação/ações; itens ausentes incluídos. | Ctrl+P e botão Imprimir |

## Requisitos não funcionais

| RNF | Implementação / forma de validar |
|---|---|
| RNF01 | Camadas de domínio, casos de uso, adaptadores e rotas; composição em main.py |
| RNF02 | OpenAPI versionado, schemas de entrada/saída e autenticação; Swagger /docs |
| RNF03 | MySQL/InnoDB, transações explícitas, SQL parametrizado, FK/UNIQUE/CHECK e teste de rollback |
| RNF04 | Layout do modelo desktop; adaptações existentes do próprio modelo em telas menores |
| RNF05 | Toasts, modais, spinners, estados de login, mensagens de validação e navegação por teclado |
| RNF06 | pytest/pytest-cov: mínimo 80% de domínio/casos de uso exigido no CI |
| RNF07 | Compose MySQL+API, volume persistente, CI de lint/testes/contrato/build; duração remota depende da execução |
| RNF08 | Seed idempotente: 5 categorias, 10 fornecedores, 50 produtos, 20 relações, 294 ofertas |
| RNF09 | Meta de p95 <500 ms; medir amostra, endpoint, ambiente e concorrência, sem extrapolar uma chamada |
| RNF10 | Hash bcrypt, JWT em memória, cookie httpOnly, revogação, limites, validação de Origin e CSP |

## Casos de uso e rastreabilidade

| UC | Caso de uso | RF |
|---|---|---|
| UC01 | Criar lista local | RF07 |
| UC02 | Buscar produto | RF07 |
| UC03 | Selecionar fornecedores | RF12 |
| UC04 | Filtrar disponibilidade | RF13 |
| UC05 | Calcular orçamento | RF14 |
| UC06 | Visualizar resultados | RF15 |
| UC07 | Exportar lista | RF16 |
| UC08 | Imprimir | RF17 |
| UC09 | Cadastrar usuário | RF01 |
| UC10 | Login | RF02 |
| UC11 | Logout | RF03 |
| UC12 | Recuperar senha | RF04 |
| UC13 | Salvar lista | RF08 |
| UC14 | Listar minhas listas | RF09 |
| UC15 | Editar/excluir lista | RF10/RF11 |
| UC16 | Editar perfil | RF06 |
| UC17 | Promover rascunho | RF08 |
| UC18 | Visualizar perfil | RF05 |
| UC19 | Validar entrada | Transversal |
| UC20 | Hash de senha/resposta | RF01/RF04/RF06 |
| UC21 | Emitir sessão | RF02 |
| UC22 | Fornecer catálogo | RF07 |
| UC23 | Fornecer fornecedores | RF12 |
| UC24 | Fornecer preços/estoque | RF14 |
| UC25 | Limitar tentativas | RF02/RF04 |
| UC26 | Invalidar/rotacionar sessão | RF02/RF03/RF04/RF06 |

Visitante e usuário autenticado são atores humanos. “Sistema” e “API Mock” no desenho representam serviços auxiliares internos da implementação; não implicam integração com um fornecedor externo real. UC04 estende opcionalmente UC03; a seleção é precondição, sem duplicar include/extend. Exportação não depende da visualização de resultados. Generalização usa linha sólida.

## Fluxos e exceções relevantes

1. **Visitante:** landing → nova lista → autocomplete/adicionar → fornecedores → slider/seleção → resultados. CSV e impressão independem de login. Produto inexistente/inativo, quantidade inválida e menos de dois fornecedores são rejeitados; edição invalida resultado e cancela respostas antigas.
2. **Salvar:** visitante abre modal de login, pode cadastrar/recuperar e retornar; após login confirma promoção. Cancelamento e erro de rede preservam rascunho. Sem nome/itens não salva. Outro usuário não pode ler, alterar ou excluir a lista persistida.
3. **Conta:** cadastro valida confirmação e unicidade; login retorna credenciais inválidas em falha; sexta falha bloqueia por 15 minutos. Refresh rotaciona token, login novo troca sessão, logout revoga. Access não é armazenado em localStorage.
4. **Recuperação:** username → pergunta → resposta validada na API → token transitório → nova senha. Resposta errada conta tentativa; três erros bloqueiam. Token expirado/reutilizado não altera senha. Modo log em desenvolvimento gera link sem expor token na resposta do pedido.
5. **Perfil/listas:** dados próprios, confirmação de senha para perfil, exclusão digitada e remoção de item confirmada. Listas paginadas e filtradas por nome. Falha no meio de salvamento reverte lista e itens na mesma transação.
6. **Resultado:** stock insuficiente torna o item ausente; total parcial é identificado. Fornecedor sem oferta recebe N/D e não vence. Empates entre melhores coberturas/custos são destacados. Categoria não filtra produtos nem restringe lista mista.

## Backlog fora do fluxo atual

RD01 histórico de comparações; RD02 importação CSV; RD03 alertas de preço; RD04 compartilhamento; RD05 PWA/mobile; RD06 fornecedores reais; RD07 IA; RD08 idiomas/moedas adicionais.

## Diagrama editável

[uc.drawio](uc.drawio). Os auxiliares internos são convenção deste artefato; validação final da modelagem acadêmica continua separada da implementação.

```xml
<mxfile host="app.diagrams.net" modified="2026-09-12T00:00:00.000Z" agent="COBECO MVP v3.1" version="24.0.0" type="device">
  <diagram id="cobeco-ucd-v31" name="COBECO — Casos de Uso MVP v3.1">
    <mxGraphModel dx="2800" dy="2000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2800" pageHeight="2000" math="0" shadow="1">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="title" value="&lt;b&gt;Diagrama de Casos de Uso — COBECO MVP v3.1&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:11px;&quot; color=&quot;#666&quot;&gt;26 Casos de Uso (18 principais + 8 internos) • 4 Atores • 12/09/2026&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontColor=#1A237E;" vertex="1" parent="1">
          <mxGeometry x="700" y="20" width="1400" height="55" as="geometry" />
        </mxCell>
        <mxCell id="boundary" value="Sistema COBECO — Comparador de Compras (MVP v3.1)" style="swimlane;startSize=35;fillColor=#FAFAFA;strokeColor=#1A237E;fontStyle=1;fontSize=15;rounded=1;arcSize=4;shadow=1;strokeWidth=2;swimlaneLine=0;" vertex="1" parent="1">
          <mxGeometry x="450" y="100" width="1900" height="1700" as="geometry" />
        </mxCell>
        <mxCell id="actorVisitor" value="Visitante&#10;(Não Autenticado)" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontSize=13;fontStyle=1;fillColor=#FFEBEE;strokeColor=#C62828;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="150" y="300" width="50" height="100" as="geometry" />
        </mxCell>
        <mxCell id="actorAuth" value="Usuário&#10;Autenticado" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontSize=13;fontStyle=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="150" y="900" width="50" height="100" as="geometry" />
        </mxCell>
        <mxCell id="actorSystem" value="Sistema" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontSize=13;fontStyle=1;fillColor=#FFF3E0;strokeColor=#E65100;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="2500" y="300" width="50" height="100" as="geometry" />
        </mxCell>
        <mxCell id="actorAPI" value="API Mock&#10;de Fornecedores" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontSize=13;fontStyle=1;fillColor=#E3F2FD;strokeColor=#1565C0;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="2500" y="1000" width="50" height="100" as="geometry" />
        </mxCell>
        <mxCell id="gen1" value="" style="endArrow=empty;endSize=20;html=1;strokeColor=#616161;strokeWidth=2;dashed=0;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="actorVisitor" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="gen1t" value="&lt;i&gt;generaliza&lt;/i&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontStyle=2;fontColor=#616161;" vertex="1" parent="1">
          <mxGeometry x="180" y="600" width="80" height="20" as="geometry" />
        </mxCell>
        <mxCell id="area1" value="🔐 AUTENTICAÇÃO (RF01–RF04)" style="swimlane;startSize=28;fillColor=#FFEBEE;strokeColor=#C62828;rounded=1;arcSize=6;fontStyle=1;fontSize=13;fontColor=#B71C1C;swimlaneLine=0;shadow=0;" vertex="1" parent="boundary">
          <mxGeometry x="40" y="50" width="900" height="280" as="geometry" />
        </mxCell>
        <mxCell id="UC09" value="UC09&#10;Cadastrar-se" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C62828;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area1">
          <mxGeometry x="40" y="60" width="170" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC10" value="UC10&#10;Realizar Login" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C62828;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area1">
          <mxGeometry x="240" y="60" width="170" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC12" value="UC12&#10;Recuperar Senha" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C62828;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area1">
          <mxGeometry x="440" y="60" width="170" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC11" value="UC11&#10;Realizar Logout" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C62828;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area1">
          <mxGeometry x="640" y="60" width="170" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC18" value="UC18&#10;Visualizar Perfil" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C62828;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area1">
          <mxGeometry x="240" y="170" width="170" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC16" value="UC16&#10;Gerenciar Perfil" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C62828;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area1">
          <mxGeometry x="440" y="170" width="170" height="70" as="geometry" />
        </mxCell>
        <mxCell id="area2" value="📝 GESTÃO DE LISTAS (RF07–RF11)" style="swimlane;startSize=28;fillColor=#E3F2FD;strokeColor=#1565C0;rounded=1;arcSize=6;fontStyle=1;fontSize=13;fontColor=#0D47A1;swimlaneLine=0;shadow=0;" vertex="1" parent="boundary">
          <mxGeometry x="40" y="360" width="900" height="380" as="geometry" />
        </mxCell>
        <mxCell id="UC01" value="UC01&#10;Criar Lista&#10;em Memória" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1565C0;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area2">
          <mxGeometry x="40" y="60" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC02" value="UC02&#10;Buscar Produtos&#10;(Autocomplete)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1565C0;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area2">
          <mxGeometry x="250" y="60" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC13" value="UC13&#10;Salvar Lista&#10;(Persistir)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1565C0;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area2">
          <mxGeometry x="460" y="60" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC17" value="UC17&#10;Promover Lista&#10;Efêmera" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1565C0;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area2">
          <mxGeometry x="670" y="60" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC14" value="UC14&#10;Listar Minhas&#10;Listas" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1565C0;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area2">
          <mxGeometry x="40" y="180" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC15" value="UC15&#10;Editar/Excluir&#10;Lista Salva" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1565C0;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area2">
          <mxGeometry x="250" y="180" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="area3" value="🔄 COMPARAÇÃO DE FORNECEDORES (RF12–RF15)" style="swimlane;startSize=28;fillColor=#E8F5E9;strokeColor=#2E7D32;rounded=1;arcSize=6;fontStyle=1;fontSize=13;fontColor=#1B5E20;swimlaneLine=0;shadow=0;" vertex="1" parent="boundary">
          <mxGeometry x="980" y="50" width="880" height="400" as="geometry" />
        </mxCell>
        <mxCell id="UC03" value="UC03&#10;Selecionar&#10;Fornecedores" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2E7D32;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area3">
          <mxGeometry x="40" y="60" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC04" value="UC04&#10;Filtrar por&#10;Disponibilidade" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2E7D32;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area3">
          <mxGeometry x="40" y="180" width="180" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC05" value="UC05&#10;Calcular Orçamento&#10;(Tabela Flat)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2E7D32;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area3">
          <mxGeometry x="260" y="60" width="200" height="80" as="geometry" />
        </mxCell>
        <mxCell id="UC06" value="UC06&#10;Visualizar Resultados&#10;(Tabela Comparativa)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2E7D32;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area3">
          <mxGeometry x="500" y="60" width="200" height="80" as="geometry" />
        </mxCell>
        <mxCell id="area4" value="📤 EXPORTAÇÃO (RF16–RF17)" style="swimlane;startSize=28;fillColor=#F3E5F5;strokeColor=#6A1B9A;rounded=1;arcSize=6;fontStyle=1;fontSize=13;fontColor=#4A148C;swimlaneLine=0;shadow=0;" vertex="1" parent="boundary">
          <mxGeometry x="980" y="480" width="880" height="260" as="geometry" />
        </mxCell>
        <mxCell id="UC07" value="UC07&#10;Exportar Lista CSV" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#6A1B9A;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area4">
          <mxGeometry x="100" y="80" width="200" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC08" value="UC08&#10;Imprimir" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#6A1B9A;fontSize=12;fontStyle=1;shadow=1;strokeWidth=1.5;" vertex="1" parent="area4">
          <mxGeometry x="500" y="80" width="200" height="70" as="geometry" />
        </mxCell>
        <mxCell id="areaInternal" value="⚙️ CASOS INTERNOS / AUXILIARES DE DOMÍNIO" style="swimlane;startSize=28;fillColor=#F5F5F5;strokeColor=#616161;rounded=1;arcSize=6;fontStyle=1;fontSize=13;fontColor=#424242;swimlaneLine=0;shadow=0;dashed=1;dashPattern=8 4;" vertex="1" parent="boundary">
          <mxGeometry x="40" y="770" width="1820" height="300" as="geometry" />
        </mxCell>
        <mxCell id="UC19" value="UC19&#10;Validar Dados" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="40" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC20" value="UC20&#10;Hash de Senha&#10;(bcrypt)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="220" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC21" value="UC21&#10;Gerar Sessão&#10;(JWT)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="400" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC22" value="UC22&#10;Fornecer Catálogo" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="580" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC23" value="UC23&#10;Fornecer Fornecedores" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="760" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC24" value="UC24&#10;Fornecer Preços" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="940" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC25" value="UC25&#10;Rate Limiting" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="1120" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="UC26" value="UC26&#10;Invalidar Sessão" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;fontSize=11;fontStyle=2;shadow=0;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="areaInternal">
          <mxGeometry x="1300" y="60" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="a1" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;exitX=1;exitY=0.2;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorVisitor" target="UC09" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a2" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;exitX=1;exitY=0.35;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorVisitor" target="UC10" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a3" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorVisitor" target="UC12" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a4" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;exitX=1;exitY=0.65;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorVisitor" target="UC01" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a5" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;exitX=1;exitY=0.8;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorVisitor" target="UC03" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a6" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;exitX=1;exitY=0.95;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorVisitor" target="UC07" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a7" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC11" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a8" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.2;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC18" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a9" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.3;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC16" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a10" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC13" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a11" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC17" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a12" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.6;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC14" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a13" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.7;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC15" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a14" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.8;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC05" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="a15" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;exitX=1;exitY=0.9;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAuth" target="UC08" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="b1" style="endArrow=none;html=1;strokeColor=#E65100;strokeWidth=2;exitX=0;exitY=0.2;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorSystem" target="UC19" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="b2" style="endArrow=none;html=1;strokeColor=#E65100;strokeWidth=2;exitX=0;exitY=0.35;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorSystem" target="UC20" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="b3" style="endArrow=none;html=1;strokeColor=#E65100;strokeWidth=2;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorSystem" target="UC21" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="b4" style="endArrow=none;html=1;strokeColor=#E65100;strokeWidth=2;exitX=0;exitY=0.65;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorSystem" target="UC25" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="b5" style="endArrow=none;html=1;strokeColor=#E65100;strokeWidth=2;exitX=0;exitY=0.8;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorSystem" target="UC26" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="c1" style="endArrow=none;html=1;strokeColor=#1565C0;strokeWidth=2;exitX=0;exitY=0.3;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAPI" target="UC22" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="c2" style="endArrow=none;html=1;strokeColor=#1565C0;strokeWidth=2;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAPI" target="UC23" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="c3" style="endArrow=none;html=1;strokeColor=#1565C0;strokeWidth=2;exitX=0;exitY=0.7;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="actorAPI" target="UC24" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc1" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC09" target="UC19" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc2" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.3;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC09" target="UC20" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc3" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC10" target="UC21" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc4" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.7;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC10" target="UC25" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc5" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC12" target="UC25" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc6" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC16" target="UC19" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc7" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.3;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC13" target="UC19" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc8" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#1565C0;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#0D47A1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC02" target="UC22" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc9" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#1565C0;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#0D47A1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.3;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC05" target="UC19" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc10" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#1565C0;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#0D47A1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC05" target="UC23" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc11" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#1565C0;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#0D47A1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.7;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC05" target="UC24" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc12" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#1565C0;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#0D47A1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC03" target="UC23" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="inc14" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#BF360C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC11" target="UC26" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ext1" value="&lt;&lt;extend&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#4A148C;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="UC04" target="UC03" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ext3" value="&lt;&lt;extend&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#4A148C;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.7;entryY=0;entryDx=0;entryDy=0;" edge="1" source="UC08" target="UC06" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ext4" value="&lt;&lt;extend&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#4A148C;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="UC16" target="UC18" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ext5" value="&lt;&lt;extend&gt;&gt;" style="endArrow=open;endSize=12;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#4A148C;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="UC17" target="UC13" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="legend" value="&lt;b&gt;LEGENDA — COBECO MVP v3.1&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1A237E;align=left;verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=12;shadow=1;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="150" y="1200" width="280" height="500" as="geometry" />
        </mxCell>
        <mxCell id="leg1" value="" style="endArrow=none;html=1;strokeColor=#C62828;strokeWidth=2;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1250" as="sourcePoint" />
            <mxPoint x="230" y="1250" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg1t" value="Visitante (Não Autenticado)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1235" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg2" value="" style="endArrow=none;html=1;strokeColor=#2E7D32;strokeWidth=2;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1285" as="sourcePoint" />
            <mxPoint x="230" y="1285" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg2t" value="Usuário Autenticado" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1270" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg2b" value="" style="endArrow=empty;endSize=15;html=1;strokeColor=#616161;strokeWidth=2;dashed=0;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1320" as="sourcePoint" />
            <mxPoint x="230" y="1320" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg2bt" value="Generalização (herança)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1305" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg3" value="" style="endArrow=none;html=1;strokeColor=#E65100;strokeWidth=2;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1355" as="sourcePoint" />
            <mxPoint x="230" y="1355" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg3t" value="Sistema (ator secundário)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1340" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg4" value="" style="endArrow=none;html=1;strokeColor=#1565C0;strokeWidth=2;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1390" as="sourcePoint" />
            <mxPoint x="230" y="1390" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg4t" value="API Mock (ator secundário)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1375" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg5" value="&lt;&lt;include&gt;&gt;" style="endArrow=open;endSize=10;dashed=1;html=1;strokeColor=#E65100;strokeWidth=2;fontSize=9;fontStyle=1;fontColor=#BF360C;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1430" as="sourcePoint" />
            <mxPoint x="230" y="1430" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg5t" value="Inclusão (obrigatória)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1415" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg6" value="&lt;&lt;extend&gt;&gt;" style="endArrow=open;endSize=10;dashed=1;html=1;strokeColor=#6A1B9A;strokeWidth=2;fontSize=9;fontStyle=1;fontColor=#4A148C;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="170" y="1465" as="sourcePoint" />
            <mxPoint x="230" y="1465" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="leg6t" value="Extensão (opcional)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1450" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg7" value="" style="ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#616161;dashed=1;dashPattern=4 3;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="180" y="1500" width="40" height="25" as="geometry" />
        </mxCell>
        <mxCell id="leg7t" value="Caso Interno (auxiliar)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1495" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg8" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#C62828;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="180" y="1535" width="40" height="20" as="geometry" />
        </mxCell>
        <mxCell id="leg8t" value="Autenticação" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1530" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg9" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#1565C0;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="180" y="1560" width="40" height="20" as="geometry" />
        </mxCell>
        <mxCell id="leg9t" value="Gestão de Listas" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1555" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg10" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="180" y="1585" width="40" height="20" as="geometry" />
        </mxCell>
        <mxCell id="leg10t" value="Comparação" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1580" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg11" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F3E5F5;strokeColor=#6A1B9A;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="180" y="1610" width="40" height="20" as="geometry" />
        </mxCell>
        <mxCell id="leg11t" value="Exportação" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1605" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="leg12" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#616161;strokeWidth=1.5;dashed=1;dashPattern=4 3;" vertex="1" parent="1">
          <mxGeometry x="180" y="1635" width="40" height="20" as="geometry" />
        </mxCell>
        <mxCell id="leg12t" value="Casos Internos" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="240" y="1630" width="180" height="30" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
