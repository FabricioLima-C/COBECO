import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import type { Server } from 'http';
import type { AddressInfo } from 'net';
import { createApp } from '../app';

/**
 * Testes de integração das rotas: sobem a aplicação inteira em uma porta
 * efêmera e falam HTTP de verdade. Só uma chamada nesta camada já teria pego o
 * `import` de um `.d.ts` que impedia a API de iniciar.
 */
describe('rotas da API', () => {
  let server: Server;
  let baseUrl: string;

  const credentials = {
    name: 'Usuária de Teste',
    email: 'Rotas.Teste@Example.com',
    password: 'Senha1234',
    consent: true,
  };

  async function call(path: string, init: RequestInit = {}) {
    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
    });
    const text = await response.text();
    return { status: response.status, body: text ? JSON.parse(text) : null, response };
  }

  beforeAll(async () => {
    process.env.PRICE_PROVIDERS = 'mock';
    server = createApp().listen(0);
    await new Promise((resolve) => server.once('listening', resolve));
    baseUrl = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  });

  afterAll(async () => {
    await new Promise((resolve) => server.close(resolve));
  });

  it('sobe a aplicação e responde ao health check', async () => {
    const { status, body } = await call('/health');
    expect(status).toBe(200);
    expect(body).toEqual({ status: 'ok' });
  });

  it('serve as rotas públicas sem autenticação', async () => {
    const retailers = await call('/api/public/retailers');
    expect(retailers.status).toBe(200);
    expect(Array.isArray(retailers.body)).toBe(true);

    const testimonials = await call('/api/public/testimonials');
    expect(testimonials.status).toBe(200);
  });

  it('bloqueia as rotas da plataforma sem token', async () => {
    const { status, body } = await call('/api/platform/lists');
    expect(status).toBe(401);
    expect(body.error.code).toBe('MISSING_TOKEN');
  });

  it('recusa o cadastro sem consentimento explícito', async () => {
    const { status, body } = await call('/api/auth/sign-up', {
      method: 'POST',
      body: JSON.stringify({ ...credentials, email: 'sem.consent@example.com', consent: false }),
    });
    expect(status).toBe(400);
    expect(body.error.message).toMatch(/aceitar o tratamento/i);
  });

  it('percorre cadastro, login e uso autenticado das listas', async () => {
    const signUp = await call('/api/auth/sign-up', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    expect(signUp.status).toBe(201);
    expect(signUp.body.email).toBe('rotas.teste@example.com');

    // Caixa diferente da usada no cadastro: o login normaliza o e-mail.
    const login = await call('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: 'ROTAS.TESTE@example.com', password: credentials.password }),
    });
    expect(login.status).toBe(200);

    const token: string = login.body.accessToken;
    const auth = { Authorization: `Bearer ${token}` };

    const created = await call('/api/platform/lists', {
      method: 'POST',
      headers: auth,
      body: JSON.stringify({ name: 'Lista de teste' }),
    });
    expect(created.status).toBe(201);

    const listId: string = created.body.id;

    // Regressão: a rota de duplicação não validava o corpo e quebrava com 500.
    const invalidDuplicate = await call(`/api/platform/lists/${listId}/duplicate`, {
      method: 'POST',
      headers: auth,
      body: JSON.stringify({ name: 123 }),
    });
    expect(invalidDuplicate.status).toBe(400);
    expect(invalidDuplicate.body.error.code).toBe('VALIDATION_ERROR');

    const duplicate = await call(`/api/platform/lists/${listId}/duplicate`, {
      method: 'POST',
      headers: auth,
      body: JSON.stringify({}),
    });
    expect(duplicate.status).toBe(201);
    expect(duplicate.body.name).toBe('Lista de teste (cópia)');
  });

  it('expõe o catálogo e gera os quatro grupos de paridade A-H', async () => {
    const login = await call('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: credentials.email, password: credentials.password }),
    });
    const auth = { Authorization: `Bearer ${login.body.accessToken}` };
    const categories = await call('/api/platform/categories', { headers: auth });
    expect(categories.status).toBe(200);
    const categoryId = categories.body[0].id;
    const suppliers = await call(`/api/platform/categories/${categoryId}/suppliers`, {
      headers: auth,
    });
    const products = await call(`/api/platform/categories/${categoryId}/products`, {
      headers: auth,
    });
    expect(suppliers.body).toHaveLength(8);

    const created = await call('/api/platform/lists', {
      method: 'POST',
      headers: auth,
      body: JSON.stringify({ name: 'Paridade', categoryId }),
    });
    const items = products.body.slice(0, 9).map((product: { id: string; name: string }) => ({
      description: product.name,
      productId: product.id,
      quantity: 1,
    }));
    await call(`/api/platform/lists/${created.body.id}/items/bulk`, {
      method: 'POST',
      headers: auth,
      body: JSON.stringify({ items }),
    });
    const quotation = await call(`/api/platform/lists/${created.body.id}/quote`, {
      method: 'POST',
      headers: auth,
      body: JSON.stringify({
        supplierIds: suppliers.body.map((supplier: { id: string }) => supplier.id),
      }),
    });
    expect(quotation.status).toBe(200);
    expect(quotation.body.groups).toHaveLength(4);
    expect(quotation.body.groups[0]).toMatchObject({ coverage: 100 });
    expect(quotation.body.bestGroupId).toBe(quotation.body.groups[0].groupId);
  });

  it('renova a sessão pelo cookie de refresh e rejeita o refresh como token de acesso', async () => {
    await call('/api/auth/sign-up', {
      method: 'POST',
      body: JSON.stringify({ ...credentials, email: 'refresh.teste@example.com' }),
    });

    const login = await call('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: 'refresh.teste@example.com', password: credentials.password }),
    });

    const setCookie = login.response.headers.get('set-cookie') || '';
    expect(setCookie).toMatch(/refreshToken=/);
    expect(setCookie).toMatch(/HttpOnly/i);

    const cookie = setCookie.split(';')[0];
    const refreshValue = cookie.split('=')[1];

    // O refresh token não pode valer como credencial de acesso.
    const misuse = await call('/api/platform/lists', {
      headers: { Authorization: `Bearer ${refreshValue}` },
    });
    expect(misuse.status).toBe(401);

    const refreshed = await call('/api/auth/refresh', { method: 'POST', headers: { cookie } });
    expect(refreshed.status).toBe(200);
    expect(typeof refreshed.body.accessToken).toBe('string');

    const withNewToken = await call('/api/platform/lists', {
      headers: { Authorization: `Bearer ${refreshed.body.accessToken}` },
    });
    expect(withNewToken.status).toBe(200);
  });

  it('recusa o refresh sem cookie', async () => {
    const { status, body } = await call('/api/auth/refresh', { method: 'POST' });
    expect(status).toBe(401);
    expect(body.error.code).toBe('SESSION_EXPIRED');
  });

  it('aplica o teto de paginação do histórico', async () => {
    const login = await call('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: credentials.email, password: credentials.password }),
    });
    const auth = { Authorization: `Bearer ${login.body.accessToken}` };

    const ok = await call('/api/platform/quotations/history?page=1&pageSize=20', { headers: auth });
    expect(ok.status).toBe(200);
    expect(ok.body.pageSize).toBe(20);

    const tooBig = await call('/api/platform/quotations/history?page=1&pageSize=999', {
      headers: auth,
    });
    expect(tooBig.status).toBe(400);
    expect(tooBig.body.error.code).toBe('VALIDATION_ERROR');
  });
});
