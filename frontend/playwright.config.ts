import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendDir = fileURLToPath(new URL(".", import.meta.url));
const projectRoot = path.resolve(frontendDir, "..");

const backendURL = "http://127.0.0.1:5011";
const frontendURL = "http://127.0.0.1:5174";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: frontendURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      name: "FastAPI",
      command: "python -m uvicorn backend.app:app --host 127.0.0.1 --port 5011",
      cwd: projectRoot,
      url: `${backendURL}/openapi.json`,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        SESSION_SECRET_KEY: "e2e-test-only-session-secret-key-0123456789",
        SESSION_COOKIE_SECURE: "false",
        ANALYSIS_MAX_CONCURRENT: "1",
        OTHELLO_DB_PATH: path.join(projectRoot, "data", "othello-e2e.db"),
      },
    },
    {
      name: "Vite",
      command: "npm run dev -- --host 127.0.0.1 --port 5174 --strictPort",
      cwd: frontendDir,
      url: frontendURL,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        OTHELLO_API_TARGET: backendURL,
      },
    },
  ],
});
