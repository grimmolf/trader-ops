// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/playwright',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'tests/reports/test-results.json' }],
    ['junit', { outputFile: 'tests/reports/junit.xml' }],
    ['list']
  ],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 30000,
    navigationTimeout: 30000
  },
  expect: {
    timeout: 10000,
    toHaveScreenshot: {
      mode: 'off', // Disable until we have baseline screenshots
      threshold: 0.2
    }
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] }
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] }
    }
  ],
  globalSetup: require.resolve('./tests/playwright/global-setup.ts'),
  globalTeardown: require.resolve('./tests/playwright/global-teardown.ts'),
  webServer: [
    {
      command: 'cd src/backend && uv run uvicorn src.backend.datahub.server:app --port 8000',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000, // 2 minutes
      env: {
        TRADING_ENV: 'test',
        USE_MOCK_BROKERS: 'true',
        ENABLE_PAPER_TRADING: 'true'
      }
    }
  ]
})