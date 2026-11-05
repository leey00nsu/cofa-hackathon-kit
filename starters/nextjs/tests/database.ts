export function testDatabaseUrl(testUrl: string | undefined, appUrl: string | undefined): string | undefined {
  if (!testUrl) return undefined;
  let test: URL;
  let app: URL | undefined;
  try {
    test = new URL(testUrl);
    app = appUrl ? new URL(appUrl) : undefined;
  } catch {
    throw new Error("Invalid database test configuration");
  }
  if (!["postgres:", "postgresql:"].includes(test.protocol) || decodeURIComponent(test.pathname) !== "/cofa_test") {
    throw new Error("Real database tests require a separate database named cofa_test");
  }
  // Conservatively reject any app configured to use cofa_test, including aliases.
  if (app && decodeURIComponent(app.pathname) === "/cofa_test") {
    throw new Error("Refusing to run database tests against the application database");
  }
  return testUrl;
}
