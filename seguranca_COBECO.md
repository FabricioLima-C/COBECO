# Varredura de segurança do COBECO

Data: **13/09/2026**. Referência do repositório ao concluir a revisão: `94ff824`.

## Correções aplicadas após a varredura

Os achados S01–S07 abaixo foram tratados no código, contrato, interface, configuração e dependências. O restante do documento preserva as evidências da varredura inicial.

| Achado | Estado após a correção |
|---|---|
| S01 | Cadastro público reserva o username demo; seed demo rejeitado em produção; recuperação da demo bloqueada em todos os modos; login, access e refresh da demo bloqueados em produção |
| S02 | `/auth/reset` exige token; modo padrão `code` entrega código aleatório individual de 256 bits; produção rejeita pergunta/log; novo código no perfil exige senha atual |
| S03 | Início de recuperação em code/question devolve instrução genérica sem consultar a existência do usuário nem revelar sua pergunta |
| S04 | Enum explícito de ambiente, validação de origem, rejeição de segredo JWT de exemplo/repetitivo, senha MySQL de exemplo e demo em produção |
| S05 | Reservas atômicas de tentativas, sem manter o lock global durante bcrypt/SQL; operações simultâneas limitadas sem impedir requisições de outras identidades |
| S06 | Middleware ASGI limita corpo a 64 KiB, inclusive sem Content-Length ou com tamanho declarado falso; envio limitado a 10 s; Uvicorn no Docker com concorrência 64 |
| S07 | qs 6.16.0 e body-parser 1.20.8 no lockfile; override impede resolução de qs anterior à correção; pacotes locais atualizados sem executar scripts de instalação |

O código de recuperação é exibido uma vez, pode ser baixado pelo usuário e não é gravado no armazenamento do navegador. Somente SHA-256 é persistido na nova tabela `recovery_codes`. Gerar outro código revoga o anterior e tokens de reset pendentes; redefinir ou alterar a senha elimina o código anterior. As contas existentes geram seu primeiro código no perfil após autenticar com a senha atual.

Também foram adicionados proteção CSV para caracteres iniciais de controle, bind local da API no Compose, permissões mínimas de leitura no CI e auditorias automáticas de dependências/achados estáticos altos. As medidas de ambiente descritas adiante (proxy HTTPS, contas de banco, retenção de logs e serviço de testes local) dependem da implantação e não foram aplicadas a serviços pessoais ou produção.

### Verificação das correções

- **60 testes de backend passaram**, com MySQL 8.0.46 isolado, e **97,69% de cobertura** de domínio/casos de uso, incluindo branches.
- **8 testes JavaScript passaram**; **12 testes de rotas/segurança do legado passaram**.
- Chromium: cadastro sem pergunta, entrega/download do código, limpeza ao fechar e ao pressionar Escape, geração de outro código com senha atual, recusa do antigo, recuperação em três etapas e login com a nova senha; sem erros JavaScript.
- pip-audit: **35 dependências, zero vulnerabilidades conhecidas**. npm audit: **zero vulnerabilidades** após atualizar a resolução efetiva do lockfile e os pacotes locais.
- Bandit: nenhum achado de severidade alta; permanecem os oito alertas SQL e o valor artificial do contrato já triados abaixo.
- Ruff, contrato OpenAPI e `docker compose config --quiet` aprovados. O build de imagem e execução remota do CI não foram realizados nesta etapa.

### Ativação em uma instalação existente

Atualize os valores de exemplo do `.env`, configure `RECOVERY_MODE=code`, aplique a migration aditiva com `python -m backend.seed` e reinicie a API (o Docker aplica migrations ao iniciar). Usuários existentes devem gerar e guardar seu código pelo perfil. A migração foi exercitada somente na base isolada `cobeco_securityfix_20260913_test`; não foram alteradas senhas de usuários reais ou credenciais de serviços pessoais. A monografia continua descrevendo a recuperação anterior e deve considerar esta evolução de segurança.

## Varredura inicial — registro histórico

**Resultado inicial:** havia correções necessárias na recuperação de contas e na validação de configuração, além de medidas de proteção de disponibilidade antes de uma publicação na internet. Não foi confirmada uma vulnerabilidade crítica nesta varredura. Isso não certifica ausência de vulnerabilidades.

Foram examinados o backend FastAPI, o frontend JavaScript, schemas, SQL, autenticação, autorização, Docker/Compose, CI, dependências Python fixadas e o lockfile npm legado. Foram usados revisão manual, Bandit 1.9.4, pip-audit 2.10.1, npm audit, testes controlados de API com MySQL e Chromium. Na etapa inicial nenhuma correção havia sido aplicada; a seção acima registra a implementação posterior autorizada pelo usuário.

## Correções por prioridade

As prioridades abaixo consideram uma eventual exposição pública. Condições de exploração e limitações estão explicitadas para não confundir uma configuração insegura possível com uma invasão já ocorrida.

| ID | Prioridade | Achado | Correção necessária |
|---|---|---|---|
| S01 | Alta, se a conta demo estiver habilitada | Resposta de recuperação da conta `demo` é pública e fixa | Impedir sua criação em produção e desabilitar recuperação dessa conta ou eliminar a credencial de recuperação compartilhada |
| S02 | Alta antes de produção; desvio funcional confirmado | Recuperação depende somente da resposta de segurança; `/reset` também dispensa token | Exigir token de uso único em `/reset`; substituir pergunta como fator único em produção |
| S03 | Média | Recuperação distingue contas existentes e divulga sua pergunta | Respostas públicas uniformes e fluxo que não revele a existência da conta |
| S04 | Alta se configurado incorretamente | Configuração aceita segredo JWT do exemplo e nomes de ambiente inválidos | Validar enum de ambiente, rejeitar valores de exemplo e exigir configuração de produção consistente |
| S05 | Média | Lock global de autenticação é compartilhado com o middleware de toda a API | Evitar bcrypt/SQL sob o lock global; usar controle atômico por identidade e estratégia compatível com processamento assíncrono |
| S06 | Média antes de exposição pública | Sem limite explícito de corpo HTTP no projeto | Limitar tamanho antes da leitura completa, controlar concorrência e proteger rotas caras |
| S07 | Média, restrita ao legado Node | `qs` vulnerável afeta também os resultados de Express/body-parser | Atualizar a cadeia de dependências e o lockfile antes de reutilizar o legado |

### S01 — recuperação da conta demo com resposta conhecida

Em [seed.py](COBECO/backend/seed.py), a conta `demo`, quando `SEED_DEMO_PASSWORD` é definido, recebe resposta de segurança fixa `cobeco`, também documentada no README. A força da senha inicial não protege a conta de quem conhece essa resposta. Não há proibição de criar essa conta quando `APP_ENV=production`.

**Confirmação:** em uma base de auditoria, criei uma conta demo com senha aleatória; usando somente a resposta pública, obtive um token pela rota normal de verificação e redefini a senha com HTTP 204. Não foi necessário explorar o caminho sem token. Não verifiquei nem alterei a conta demo da aplicação em uso.

**Correção:** bloquear seed de demonstração em produção; desabilitar ou remover contas demo existentes antes de publicar; não reutilizar respostas conhecidas em contas que contenham dados. Testar que a configuração de produção rejeita a habilitação de demo e que essa conta não pode ser recuperada pela resposta pública.

### S02 — recuperação por pergunta e caminho alternativo sem token

[Auth.reset](COBECO/backend/usecases/auth.py) aceita `answer` quando não há `token`, no modo `question`. [Reset](COBECO/backend/adapters/schemas.py) torna os dois campos opcionais. A resposta de segurança continua sendo verificada, portanto não se trata de redefinição arbitrária sem credencial; o problema é permitir uma credencial estática como único fator e dispensar o token temporário descrito no RF04.

**Confirmação:** redefini uma conta descartável com username, resposta correta e nova senha, sem solicitar token: HTTP 204. O token de acesso anterior foi corretamente invalidado: HTTP 401.

**Correção imediata do RF04:** exigir token em `/api/auth/reset`, remover o caminho com resposta direta, manter hash do token no banco, prazo de 15 minutos, consumo atômico e revogação das sessões. Atualizar OpenAPI e o teste que atualmente espera sucesso na redefinição direta.

**Correção para produção:** usar um canal previamente verificado, por exemplo e-mail verificado com token, ou códigos de recuperação aleatórios entregues ao usuário com segurança. Exigir token emitido pela mesma pergunta não resolve a fraqueza do fator original: apenas organiza o fluxo. A OWASP recomenda não usar perguntas como único mecanismo de recuperação. [Orientação OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

Se o projeto permanecer estritamente acadêmico e offline, a pergunta pode continuar como limitação documentada; isso não deve ser descrito como recuperação adequada para produção. O modo `log` também não é substituto de produção.

### S03 — enumeração de contas

Em [Auth.recovery](COBECO/backend/usecases/auth.py), uma conta existente retorna sua pergunta, enquanto uma inexistente recebe a pergunta genérica. O limite de seis solicitações por IP em 15 minutos reduz a velocidade, mas não elimina a informação revelada.

**Confirmação:** duas consultas controladas retornaram HTTP 200 com corpos diferentes, permitindo distinguir a conta descartável existente da inexistente.

**Correção:** resposta genérica uniforme e distribuição da recuperação pelo canal verificado; evitar diferenças observáveis de conteúdo e tempo. Uma mensagem genérica antes de outra etapa que volte a revelar a pergunta não elimina o problema. Essa recomendação acompanha a [orientação de recuperação da OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

### S04 — validação de configuração permite erros perigosos

[Settings](COBECO/backend/config.py) aceita qualquer string em `app_env`. As proteções só entram quando o valor é exatamente `production`. A propriedade `Secure` do cookie segue a mesma comparação em [routers/api.py](COBECO/backend/routers/api.py). O segredo JWT exige somente comprimento mínimo; a chave publicada em `.env.example` satisfaz esse critério.

**Confirmações locais, sem usar credenciais reais:**

- `APP_ENV=prodution`, origem HTTP e recuperação por log foram aceitos juntos.
- `APP_ENV=production` com origem HTTPS e o segredo JWT do exemplo foi aceito.

Isso não demonstra que a instalação em uso emprega aquele segredo. Um segredo de assinatura conhecido comprometeria a confiança nos JWTs; os controles adicionais de sessão no banco não tornam seu uso aceitável.

**Correção:** enum explícito de ambientes; rejeitar valores de exemplo e segredos vazios/conhecidos; fornecer chave aleatória própria; validar a origem como URL completa; impedir demo e modo log em produção. Testar rejeição de ambientes mal escritos e presença de `Secure` nos cookies de produção. Se uma implantação tiver usado uma chave pública/de exemplo, rotacioná-la e invalidar as sessões correspondentes.

### S05 — contenção global e proteção de disponibilidade

[Auth.login, verify_recovery e reset](COBECO/backend/usecases/auth.py) mantêm `self.limiter.lock` durante bcrypt e operações MySQL. [AttemptLimiter.request](COBECO/backend/usecases/limiter.py) usa o mesmo `RLock`, e [main.py](COBECO/backend/main.py) o chama sincronamente no middleware assíncrono de toda requisição `/api/`.

**Evidência:** uma retenção controlada de 250 ms desse lock fez uma chamada independente do limitador esperar 250,97 ms. A inspeção do código identifica o caminho pelo qual uma operação lenta de autenticação pode atrasar também requisições não relacionadas. Não foi feito ataque de indisponibilidade nem teste de saturação da aplicação em uso.

**Correção:** não manter o lock global durante hash ou consultas; preservar atomicidade contra tentativas concorrentes com estado por identidade e operações curtas. Para múltiplos processos, usar armazenamento compartilhado com operações atômicas, por exemplo Redis. Não simplesmente remover o lock, pois isso pode reintroduzir bypass do bloqueio.

O limitador também perde seus contadores ao reiniciar e não compartilha estado entre workers. O Docker já usa um worker e documenta essa limitação. Antes de escalar, corrigir o armazenamento do limitador e configurar de forma explícita os proxies confiáveis que determinam o IP do cliente.

### S06 — limites de requisição e concorrência

Os schemas limitam quantidades, listas de itens e campos, mas atuam após a recepção e interpretação do JSON. Não encontrei no projeto middleware de limite de bytes, configuração de proxy com limite de corpo ou limite explícito de concorrência no comando Uvicorn.

**Verificação limitada:** um corpo com campo extra de 256 KiB chegou à validação e recebeu 422, em vez de rejeição por tamanho. A resposta não refletiu o conteúdo grande. Isso confirma o processamento desse tamanho; não foi medido um limite máximo nem demonstrado esgotamento de memória.

**Correção:** definir um teto compatível com os payloads do aplicativo, inicialmente 64–128 KiB após conferir o contrato; aplicar o limite antes de acumular todo o corpo, incluindo transferência sem `Content-Length`; retornar 413. Definir limites de concorrência, tempo e taxa no proxy/servidor. Testar o limiar permitido e o excedente sem realizar testes destrutivos.

### S07 — dependências vulneráveis no legado Node

`npm audit --package-lock-only --ignore-scripts --json` encontrou **três pacotes afetados de severidade moderada**, sem pacotes classificados como altos ou críticos:

| Pacote no lockfile | Versão | Relação com os avisos |
|---|---|---|
| `qs` | 6.15.3 | Dois avisos próprios |
| `body-parser` | 1.20.6 | Dependência afetada por `qs` |
| `express` | 4.22.2 | Cadeia de dependências afetada |

São três entradas de pacotes no audit, não três falhas independentes no backend atual. Os avisos de `qs` são [CVE-2026-82562 / GHSA-x5fp-wj9c-mxmx](https://github.com/advisories/GHSA-x5fp-wj9c-mxmx) e [CVE-2026-82417 / GHSA-4mjr-xmp4-gh2g](https://github.com/advisories/GHSA-4mjr-xmp4-gh2g), ambos com correção em **6.16.0**. Eles envolvem bypass de limite de arrays e erro capaz de causar negação de serviço em percursos/configurações específicos.

**Correção:** atualizar a cadeia Express/body-parser/qs para resolver `qs` em uma versão corrigida, regenerar o lockfile e executar os testes do legado. Revisar o diff e repetir `npm audit`; evitar `npm audit fix --force` sem avaliar mudanças incompatíveis.

O Dockerfile atual copia apenas backend/frontend e instala Python; não inclui `apps`, `packages` ou `node_modules`. Assim, esses avisos não são vulnerabilidades de dependência da aplicação FastAPI em execução. Não executei provas de exploração no legado.

## Resultados dos scanners e revisão dos alertas

| Verificação | Resultado |
|---|---|
| pip-audit sobre `requirements.txt` | **35 dependências consultadas, nenhuma vulnerabilidade conhecida reportada**, sem dependências puladas |
| Bandit, backend excluindo testes | 1.130 linhas; 8 alertas médios B608 e 1 baixo B106; nenhum alto |
| Revisão dos oito B608 | Construção SQL com fragmentos internos, identificadores controlados/allowlist e valores parametrizados; não confirmada injeção SQL nesses pontos |
| Revisão do B106 | `contract-only` em `export_openapi.py` é um valor artificial para geração do contrato, não uma senha real de produção |
| npm audit, lockfile legado | 3 pacotes moderados afetados pela cadeia de `qs`; 0 altos e 0 críticos |
| Busca de padrões de segredos no conteúdo versionado atual | Não identificada credencial real de produção nos candidatos inspecionados; valores de teste, exemplos e falsos positivos de markup |

Não é necessário reescrever SQL parametrizado por causa dos alertas heurísticos B608. Se forem documentadas supressões, fazê-las pontualmente e com justificativa, sem desabilitar a regra para todo o repositório. A busca de segredos não cobriu todo o histórico Git nem equivale a uma auditoria especializada de todos os formatos de credenciais.

## Controles que passaram nas verificações dirigidas

- Um segundo usuário não conseguiu consultar, editar ou excluir a lista do primeiro: **404 nas três operações**, com a lista preservada.
- JWT assinado com chave diferente foi recusado: **401**.
- Token de acesso anterior à redefinição de senha foi recusado: **401**.
- POST com origem externa foi recusado: **403**.
- Entrada de teste SQL foi tratada literalmente, sem retornar o catálogo inteiro.
- Nomes e unidades contendo HTML foram renderizados como texto no Chromium; nenhum elemento injetado nem código executado nos campos testados.
- Respostas da API apresentaram CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` e `Cache-Control: no-store`.
- O código usa bcrypt com salt, comparação de hashes de tokens, consultas parametrizadas, validação de propriedade e access token em memória. A suíte funcional da revisão imediatamente anterior passou com 31 testes de backend e 7 de frontend; esses resultados não substituem os testes de segurança dirigidos desta revisão.

## Adequações de ambiente e manutenção

Estas medidas complementam as correções acima; não foram classificadas como explorações remotas confirmadas:

- **HTTPS e exposição:** o Compose publica a API em `8000:8000`, e não fornece terminação TLS. Para desenvolvimento local, preferir bind em loopback; para publicação, usar proxy HTTPS, manter a API interna e configurar cookies/ambiente corretamente. HSTS deve ser configurado no ponto de terminação HTTPS. A origem HTTPS no `.env` não cria TLS por si só.
- **Banco:** a instância auxiliar de testes na porta 33307 usa `root` sem senha, confirmadamente restrita a `127.0.0.1`. Não é uma exposição remota demonstrada, mas outros processos locais podem acessar essa instância. Criar usuário de teste com senha e privilégios restritos e encerrar o serviço auxiliar quando desnecessário. Não foram alteradas credenciais nem examinadas bases pessoais do serviço MySQL na porta 3306.
- **Privilégios em produção:** separar usuário de migrations do usuário da aplicação; evitar permissões de DDL e administração no processo que atende requisições. O aplicativo atual executa migrations/seed na inicialização com as mesmas credenciais.
- **CI:** adicionar pip-audit, Bandit com triagem, verificação de segredos e auditoria do npm enquanto o legado for mantido. Fixar Actions por SHA e explicitar `permissions: contents: read`. Separar dependências de teste das de execução e considerar hashes no arquivo de dependências.
- **Auditoria:** registrar eventos de login, bloqueio, recuperação e revogação sem senhas, respostas ou tokens; definir retenção e acesso aos registros. O modo log de recuperação deve continuar restrito ao desenvolvimento.
- **CSV:** há proteção para fórmulas iniciadas diretamente por `=`, `+`, `-` e `@`; ampliar testes para caracteres de controle iniciais e comportamento dos aplicativos de planilha escolhidos. Não foi demonstrada exploração em Excel/LibreOffice nesta revisão.

## Escopo dos testes e artefatos

Os testes que gravam dados usaram somente `cobeco_security_20260913_test`, criado na instância auxiliar local. A prova da conta demo também ocorreu nessa base, com senha aleatória. O navegador usou rascunho local e consultas públicas. Não houve redefinição de senha de usuários reais, alteração de dados da aplicação em uso, varredura de máquinas externas, flood ou teste destrutivo de disponibilidade.

As ferramentas foram instaladas separadamente em `COBECO/.local-test/security/tools`; `requirements.txt`, o ambiente de dependências da aplicação e o lockfile npm não foram atualizados. Artefatos locais, ignorados pelo Git:

- [Testes dirigidos](COBECO/.local-test/security/probes.py) e [resultados](COBECO/.local-test/security/probes.json).
- [Bandit](COBECO/.local-test/security/bandit.json).
- [pip-audit](COBECO/.local-test/security/pip-audit.json).
- [npm audit](COBECO/.local-test/security/npm-audit.json).

A avaliação não incluiu auditoria de imagens Docker/SO, exploração do legado, análise completa do histórico Git, infraestrutura pública ou teste sob carga. O daemon Docker estava indisponível na verificação de infraestrutura anterior. As bases de vulnerabilidades representam o que foi reportado na data da consulta, não uma garantia permanente.

## Ordem recomendada de implementação

1. Corrigir S01 e o caminho sem token de S02; atualizar contrato e testes.
2. Endurecer a configuração S04 e definir o mecanismo de recuperação de produção, resolvendo S02/S03 conjuntamente.
3. Corrigir contenção e limites de recursos S05/S06; configurar HTTPS e privilégios de banco para o ambiente de destino.
4. Atualizar o legado S07 se ele continuar mantido/utilizado e incorporar auditorias ao CI.
