import { randomUUID } from 'node:crypto';
import { expect, test as base } from '@playwright/test';

const BUILTIN_MODEL = 'builtin/text-on-shapes';
const FILENAME = /^[a-z0-9-]+-[bcdfghjklmnpqrstvwxz2456789]{5}\.png$/;
const TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const IMAGE_PATH = /^\/api\/images\/[0-9a-f-]{36}\/image$/;

const test = base.extend({
  // The tests run against the real application, so each test deletes the images it created
  // (and only those) and then checks that they are gone.
  createdImages: [
    async ({ page, request }, use) => {
      const generator = await (await request.get('/api/generator')).json();
      if (generator.model !== BUILTIN_MODEL) {
        throw new Error(
          `These tests need the built-in generator, but ${generator.model} is online. ` +
            'Stop the generator and wait a minute for the backend to consider it offline.'
        );
      }

      const ids = [];
      const pending = [];
      page.on('response', (response) => {
        const { pathname } = new URL(response.url());
        if (response.request().method() === 'POST' && pathname === '/api/images' && response.ok()) {
          pending.push(response.json().then((image) => ids.push(image.id)));
        }
      });

      await use(ids);

      await Promise.all(pending);
      await Promise.all(ids.map((id) => request.delete(`/api/images/${id}`)));
      for (const id of ids) {
        expect((await request.get(`/api/images/${id}/image`)).status(), `image ${id} should be cleaned up`).toBe(404);
      }
    },
    { auto: true }
  ]
});

// Random suffix so tests only ever look at their own images.
const description = (label) => `e2e test ${label} ${randomUUID().slice(0, 8)}`;
const card = (page, text) => page.getByRole('listitem').filter({ hasText: text });

async function generate(page, text) {
  await page.getByLabel('Description').fill(text);
  await page.getByRole('button', { name: 'Generate' }).click();
  return card(page, text);
}

test('shows that the built-in generator is used', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByText('Generating images with')).toContainText(BUILTIN_MODEL);
});

test('generates an image from a description', async ({ page, request }) => {
  const text = description('generate');
  await page.goto('/');

  const image = await generate(page, text);

  await expect(image.getByRole('img', { name: text })).toHaveJSProperty('naturalWidth', 1024);
  await expect(image.getByText(FILENAME)).toBeVisible();
  await expect(image.getByText(TIMESTAMP)).toHaveCount(2);
  await expect(page.getByLabel('Description')).toHaveValue('');

  const created = (await (await request.get('/api/images')).json()).find((item) => item.description === text);
  expect(created).toMatchObject({ state: 'ready', state_details: `Generated with ${BUILTIN_MODEL}.` });
});

test('shows an error when the description is empty', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Generate' }).click();

  await expect(page.getByRole('alert')).toContainText('Generating image failed because description is required');
});

test('views a generated image in a new tab', async ({ page }) => {
  const text = description('view');
  await page.goto('/');
  const image = await generate(page, text);

  const popupPromise = page.waitForEvent('popup');
  await image.getByRole('link', { name: 'Show' }).click();
  const popup = await popupPromise;
  await popup.waitForLoadState();

  expect(new URL(popup.url()).pathname).toMatch(IMAGE_PATH);
  await expect(popup.locator('img')).toHaveJSProperty('naturalWidth', 1024);

  const response = await page.request.get(popup.url());
  const filename = await image.getByText(FILENAME).textContent();
  expect(response.headers()['content-type']).toBe('image/png');
  expect(response.headers()['content-disposition']).toBe(`inline; filename="${filename}"`);
  const png = await response.body();
  expect(png.subarray(1, 4).toString()).toBe('PNG');
  expect([png.readUInt32BE(16), png.readUInt32BE(20)]).toEqual([1024, 1024]);
});

test('lists images newest first and keeps them after a reload', async ({ page }) => {
  const first = description('first');
  const second = description('second');
  await page.goto('/');
  await expect(await generate(page, first)).toBeVisible();
  await expect(await generate(page, second)).toBeVisible();

  const newestFirst = async () => {
    const items = await page.getByRole('listitem').allInnerTexts();
    const [firstIndex, secondIndex] = [first, second].map((text) => items.findIndex((item) => item.includes(text)));
    return firstIndex >= 0 && secondIndex >= 0 && secondIndex < firstIndex;
  };
  await expect.poll(newestFirst).toBe(true);

  await page.reload();

  await expect.poll(newestFirst).toBe(true);
});

test('deletes an image', async ({ page, request }) => {
  const text = description('delete');
  await page.goto('/');
  const image = await generate(page, text);
  const href = await image.getByRole('link', { name: 'Show' }).getAttribute('href');
  expect((await request.get(href)).status()).toBe(200);

  await image.getByRole('button', { name: 'Delete' }).click();

  await expect(image).toHaveCount(0);
  expect((await request.get(href)).status()).toBe(404);
  await page.reload();
  await expect(card(page, text)).toHaveCount(0);
});
