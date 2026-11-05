import assert from "node:assert/strict";
import test from "node:test";
import { once } from "node:events";
import { createServer, type Socket } from "node:net";
import { Pool } from "pg";
import { testDatabaseUrl } from "./database";
import { unusedPort, withApp } from "./server";

test("GET /api/health returns a safe 503 when DATABASE_URL is missing", { timeout: 90_000 }, async () => {
  await withApp("", async (base) => {
    const response = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(15_000) });
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), { status: "error", database: "unavailable" });
    assert.match(response.headers.get("cache-control") ?? "", /no-store/);
    const home = await fetch(base);
    assert.equal(home.status, 200);
    assert.match(await home.text(), /새 프로젝트/);
  });
});

test("GET /api/health returns 503 on refused connections without leaking secrets", { timeout: 90_000 }, async () => {
  const port = await unusedPort();
  await withApp(`postgresql://synthetic_user:synthetic_secret@127.0.0.1:${port}/cofa`, async (base) => {
    const response = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(15_000) });
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), { status: "error", database: "unavailable" });
  });
});

test("GET /api/health bounds a database connection that accepts TCP but never responds", { timeout: 90_000 }, async () => {
  const sockets = new Set<Socket>();
  const peer = createServer((socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
  });
  peer.listen(0, "127.0.0.1");
  await once(peer, "listening");
  const address = peer.address();
  assert(address && typeof address !== "string");
  try {
    await withApp(`postgresql://synthetic_user:synthetic_secret@127.0.0.1:${address.port}/cofa`, async (base) => {
      const response = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(12_000) });
      assert.equal(response.status, 503);
      assert.deepEqual(await response.json(), { status: "error", database: "unavailable" });
    });
  } finally {
    for (const socket of sockets) socket.destroy();
    await new Promise<void>((resolve) => peer.close(() => resolve()));
  }
});

test("real DB tests skip without an explicit TEST_DATABASE_URL and refuse application databases", () => {
  assert.equal(testDatabaseUrl(undefined, undefined), undefined);
  assert.throws(() => testDatabaseUrl("postgresql://local:local@localhost/cofa", undefined), /cofa_test/);
  assert.throws(() => testDatabaseUrl("postgresql://local:local@localhost/cofa_test", "postgresql://other:other@127.0.0.1/cofa_test"), /application database/);
  assert.throws(() => testDatabaseUrl("https://localhost/cofa_test", undefined), /cofa_test/);
  assert.throws(() => testDatabaseUrl("invalid", undefined), /configuration/);
  assert.equal(testDatabaseUrl("postgresql://local:local@localhost/cofa_test", "postgresql://local:local@localhost/cofa"), "postgresql://local:local@localhost/cofa_test");
});

test("GET /api/health returns 200 after SELECT 1 against a real isolated cofa_test database", {
  skip: !process.env.TEST_DATABASE_URL && "TEST_DATABASE_URL is unset; real PostgreSQL checks NOT_RUN",
  timeout: 90_000,
}, async () => {
  const url = testDatabaseUrl(process.env.TEST_DATABASE_URL, process.env.DATABASE_URL)!;
  const pool = new Pool({ connectionString: url, max: 1, connectionTimeoutMillis: 3_000, query_timeout: 3_500, statement_timeout: 3_000 });
  try {
    const identity = await pool.query<{ name: string }>("SELECT current_database() AS name");
    assert.equal(identity.rows[0]?.name, "cofa_test");
    // Session-local generic fixture only. It vanishes when this pool closes.
    await pool.query("CREATE TEMP TABLE starter_probe (value text NOT NULL)");
    await pool.query("INSERT INTO starter_probe(value) VALUES ($1)", ["synthetic"]);
    assert.deepEqual((await pool.query("SELECT value FROM starter_probe")).rows, [{ value: "synthetic" }]);
    await withApp(url, async (base) => {
      const response = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(15_000) });
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), { status: "ok", database: "connected" });
      assert.match(response.headers.get("cache-control") ?? "", /no-store/);
      const home = await fetch(base);
      assert.equal(home.status, 200);
      assert.match(await home.text(), /새 프로젝트/);
    });
  } finally {
    await pool.end();
  }
});
