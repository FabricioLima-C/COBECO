# Stack tecnológica

Versões são as declaradas nos manifests do projeto em 30/08/2026.

| Camada | Tecnologia | Versão/faixa | Finalidade |
|---|---|---:|---|
| Linguagem | TypeScript | 5.9 | Tipagem compartilhada em API e UI |
| Backend | Node.js + Express | 20 / 4.22 | API REST |
| Validação | Zod | 3.25 | Validação de payloads |
| Autenticação | JWT + Argon2 | 9.0 / 0.44 | Sessão e hash de senha |
| ORM | Prisma | 5.22 | Persistência e migrations |
| Banco | PostgreSQL | 16 | Dados transacionais |
| Frontend | React + React Router | 18.3 / 7.18 | Interface componentizada e rotas |
| Build web | Vite | 8.2 | Desenvolvimento e bundle |
| CSS | Tailwind CSS | 3.4 | Design responsivo |
| Testes unitários | Vitest | 4.1 | Domínio, serviços e componentes |
| BDD | Cucumber | 13.2 | Cenários Gherkin |
| E2E | Playwright | 1.62 | Fluxos críticos no navegador |
| Contrato | OpenAPI | 3.0.3 | Documentação da API e Swagger UI |
| Infraestrutura | Docker Compose + Nginx | Compose atual / Nginx 1.27 | Três serviços e proxy da UI |
| CI | GitHub Actions | — | lint, testes e build |

## Decisão sobre React

O React é mantido porque o projeto já possui páginas, contextos e componentes TypeScript funcionais. Não há jQuery. A redação do RNF20 foi corrigida para proibir a combinação que motivou o requisito original, sem condenar a tecnologia efetivamente adotada.
