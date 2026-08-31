# Requisitos não funcionais — COBECO

| Código | Requisito |
|---|---|
| RNF01 | Separar domínio puro, serviços, adapters de persistência e framework web, aplicando Clean Code. |
| RNF02 | Manter API REST documentada em OpenAPI; novas rotas devem partir do contrato antes da implementação. |
| RNF03 | Usar PostgreSQL com transações ACID e migrations versionadas. |
| RNF04 | Disponibilizar frontend, API e PostgreSQL como três serviços Docker. |
| RNF05 | Descrever regras críticas em Gherkin e executá-las com Cucumber. |
| RNF06 | Cobrir funções do domínio e serviços com Vitest. |
| RNF07 | Cobrir o fluxo cadastro → login → lista → cotação com Playwright. |
| RNF08 | Executar lint, testes e build a cada push e pull request no GitHub Actions. |
| RNF09 | Otimizar a interface para desktop a partir de 1024×768, preservando responsividade. |
| RNF10 | Exibir estados de carregamento e erros compreensíveis. |
| RNF11 | Garantir foco visível, navegação por teclado, contraste adequado, HTML semântico e rótulos. |
| RNF12 | Destacar o melhor orçamento sem depender apenas de cor. |
| RNF13 | Armazenar senha somente com hash Argon2. |
| RNF14 | Usar HTTPS no ambiente de produção. |
| RNF15 | Expirar a sessão após 30 minutos sem renovação/atividade. |
| RNF16 | Indexar chaves usadas em catálogo, histórico e relacionamentos. |
| RNF17 | Servir os artefatos estáticos da UI independentemente da API; informar indisponibilidade de dados. |
| RNF18 | Utilizar apenas tecnologias FOSS ou de uso gratuito. |
| RNF19 | Implementar o backend em Node.js, TypeScript e Express. |
| RNF20 | Implementar o frontend em React 18 + TypeScript, sem jQuery. A escolha preserva componentização e tipagem já validadas; o anti-pattern vetado é misturar React e jQuery. |
| RNF21 | Usar PostgreSQL 16 e Prisma ORM 5. |
| RNF22 | Versionar no GitHub e adotar GitHub Flow. |
