import { defineConfig, devices } from '@playwright/test';

// Generating with an AI model takes much longer than with the built-in generator.
const aiModel = !!process.env.WAIT_FOR_AI_MODEL;

export default defineConfig({
  testDir: './tests',
  timeout: aiModel ? 30 * 60_000 : 30_000,
  expect: { timeout: aiModel ? 10 * 60_000 : 5_000 },
  // The tests share the application with each other, so they run one at a time.
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]
});
