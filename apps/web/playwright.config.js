// Journey test of the static demo, run against the system Chrome (no browser download).
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "tests",
  timeout: 30000,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:4173", channel: "chrome", headless: true },
  webServer: {
    command: "python3 -m http.server 4173 --bind 127.0.0.1",
    url: "http://127.0.0.1:4173/index.html",
    reuseExistingServer: false,
  },
});
