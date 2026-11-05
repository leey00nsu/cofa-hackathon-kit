import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:net";
import { setTimeout as delay } from "node:timers/promises";

export async function unusedPort() {
  const server = createServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  assert(address && typeof address !== "string");
  await new Promise<void>((resolve) => server.close(() => resolve()));
  return address.port;
}

export async function withApp(databaseUrl: string, run: (base: string) => Promise<void>) {
  const generatedFiles = ["next-env.d.ts", "tsconfig.json"];
  const originals = await Promise.all(generatedFiles.map((file) => readFile(file)));
  const port = await unusedPort();
  const child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "dev", "--hostname", "0.0.0.0", "--port", String(port)], {
    env: { ...process.env, DATABASE_URL: databaseUrl, NEXT_TEST_DIST_DIR: ".next/test", NEXT_TELEMETRY_DISABLED: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  // Drain framework output so TAP has exactly one test-runner summary.
  child.stdout.resume();
  child.stderr.resume();
  const exited = once(child, "exit");
  const base = `http://127.0.0.1:${port}`;
  try {
    const deadline = Date.now() + 60_000;
    for (;;) {
      if (child.exitCode !== null) throw new Error("Test-owned Next.js server exited before readiness");
      try {
        const response = await fetch(base, { signal: AbortSignal.timeout(1_000) });
        if (response.ok) break;
      } catch { /* The test-owned server may still be starting. */ }
      if (Date.now() > deadline) throw new Error("Test-owned Next.js server did not become ready");
      await delay(100);
    }
    await run(base);
  } finally {
    child.kill("SIGTERM");
    const killTimer = setTimeout(() => child.kill("SIGKILL"), 5_000);
    try { await exited; } finally {
      clearTimeout(killTimer);
      // Dev type generation must not change source fingerprints for later checks.
      await Promise.all(generatedFiles.map((file, index) => writeFile(file, originals[index])));
    }
  }
}
