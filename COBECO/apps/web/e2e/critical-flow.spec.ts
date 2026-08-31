import { expect, test } from '@playwright/test';

test('cadastro, login, lista e cotação por paridade', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  await page.goto('/sign-up');
  await page.getByRole('textbox', { name: /^nome/i }).fill('Pessoa E2E');
  await page.getByRole('textbox', { name: /^e-mail/i }).fill(email);
  await page.getByLabel(/^senha/i).fill('Senha1234');
  await page.getByLabel(/confirmar senha/i).fill('Senha1234');
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: /criar conta/i }).click();
  await page.waitForURL('**/platform');

  await page.goto('/login');
  await page.getByRole('textbox', { name: /^e-mail/i }).fill(email);
  await page.getByLabel(/senha/i).fill('Senha1234');
  await page.getByRole('button', { name: /fazer login/i }).click();
  await expect(page.getByText(/minhas listas/i)).toBeVisible();

  await page.getByPlaceholder('Nova lista').fill('Compra E2E');
  await page.getByLabel('Criar lista').click();
  await page.getByLabel('Produto').fill('Produto 1');
  await page.getByRole('button', { name: 'Adicionar', exact: true }).click();
  await page.getByRole('button', { name: /cotar lista completa/i }).click();
  await expect(page.getByRole('heading', { name: /grupos por paridade/i })).toBeVisible();
  await expect(page.getByText(/melhor orçamento/i)).toBeVisible();
});
