// The six steps of the minimal user journey (roadmap S9), plus security checks (S10).
const { test, expect } = require("@playwright/test");

function watch(page) {
  const errors = [];
  const external = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("request", (r) => {
    const u = new URL(r.url());
    if (u.hostname !== "127.0.0.1") external.push(r.url());
  });
  return { errors, external };
}

test("the six-step journey works end to end", async ({ page }) => {
  const seen = watch(page);
  await page.goto("/");
  // Provenance and limitation banner, always shown.
  const banner = page.locator("#banner");
  await expect(banner).toContainText("not financial advice");
  await expect(banner).toContainText("2026-11-15");
  await expect(banner).toContainText("not a realised sale");

  // 1. Set.
  await page.getByRole("radio", { name: "Surging Sparks" }).click();
  await expect(page.locator("#set-hint")).toContainText("Surging Sparks (sv08)");

  // 2. Cost scenario.
  await page.getByRole("radio", { name: "Adverse (prudent)" }).click();
  await expect(page.locator("#scenario-params")).toContainText("5.49 USD");

  // 3. Break-even price with editable costs.
  await expect(page.locator("#be-tiles")).toContainText("Break-even booster price");
  await page.locator("#in-booster").fill("0.10");
  await expect(page.locator("#calc-result")).toContainText("gains on average");
  await page.locator("#in-booster").fill("5.49");
  await expect(page.locator("#calc-result")).toContainText("opening loses about");
  await page.locator("#in-fixed").fill("");
  await expect(page.locator("#calc-result")).toContainText("Enter a number");
  await page.locator("#in-fixed").fill("0");
  await expect(page.locator("#be-chart svg")).toHaveCount(1);

  // 4. Budget (E1).
  await page.getByRole("radio", { name: "100 boosters" }).click();
  await expect(page.locator("#e1-table caption")).toContainText("100 × 5.49");
  await expect(page.locator("#e1-table tbody tr")).toHaveCount(4);
  await expect(page.locator("#e1-chart circle.dot-a")).toHaveCount(4);

  // 5. Target card (E2): two targets, no card price shown.
  await expect(page.locator("#e2-table tbody tr")).toHaveCount(2);
  await expect(page.locator("#e2-table")).toContainText("Most expensive card");

  // 6. Hypotheses, limits and downloads.
  await expect(page.locator("#hyp .hyp")).toHaveCount(4);
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#dl-csv").click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^pokequant-main-.*-comparisons\.csv$/);
  await expect(page.locator("#provenance")).toContainText("CC BY 4.0");

  expect(seen.errors).toEqual([]);
  expect(seen.external).toEqual([]);
});

test("no horizontal scroll on a phone and keyboard selection works", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const width = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(width).toBeLessThanOrEqual(375);
  await page.getByRole("radio", { name: "Stellar Crown" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("radio", { name: "Surging Sparks" })).toHaveAttribute("aria-checked", "true");
});

test("the page declares a strict content security policy", async ({ page }) => {
  await page.goto("/");
  const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
  expect(csp).toContain("default-src 'self'");
  expect(csp).toContain("script-src 'self'");
  expect(csp).not.toContain("unsafe-inline");
});
