import { test, expect } from "@playwright/test";
import { execFileSync } from "child_process";
import path from "node:path";

test("anonymous user is sent to /login", async ({ page }) => {
  await page.goto("/dashboard/learn");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("button", { name: "Continue with Google" })).toBeVisible();
});

test.describe("logged in", () => {
  test.beforeEach(async ({ context }) => {
    const backendDir = path.resolve("../backend");

    const sid = execFileSync(
      path.join(backendDir, ".venv", "bin", "python"),
      ["manage.py", "e2e_session", "e2e@example.com"],
      {
        cwd: backendDir,
        encoding: "utf8",
      }
    ).trim();
    await context.addCookies([{ name: "sessionid", value: sid, domain: "localhost", path: "/" }]);
  });

  test("sees dashboard with their profile", async ({ page }) => {
    await page.goto("/dashboard/learn");
    await expect(page.getByText(/E2E User/i)).toBeVisible();
  });

  test("logout returns to login and blocks the dashboard", async ({ page }) => {
    await page.goto("/dashboard/learn");
    await page.getByRole("button", { name: "Log out" }).click();
    await page.goto("/dashboard/learn");
    await expect(page).toHaveURL(/\/login/);
  });

  test("logout ends the session everywhere", async ({ page, context }) => {
    await page.goto("/dashboard");
    const before = (await context.cookies()).find(c => c.name === "sessionid")!.value;

    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login/);

    // 1. Protected page is blocked
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);

    // 2. The old cookie value is dead even if replayed
    const res = await context.request.get("http://localhost:8000/api/me/", {
      headers: { cookie: `sessionid=${before}` },
    });
    expect([401, 403]).toContain(res.status());
  });
});