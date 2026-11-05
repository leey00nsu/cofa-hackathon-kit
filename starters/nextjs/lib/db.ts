import "server-only";
import { Pool } from "pg";

const state = globalThis as typeof globalThis & { databasePool?: Pool };

function getPool(): Pool {
  if (!process.env.DATABASE_URL) throw new Error("Database is not configured");
  if (!state.databasePool) {
    const pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 5,
      connectionTimeoutMillis: 3_000,
      idleTimeoutMillis: 10_000,
      statement_timeout: 3_000,
      query_timeout: 3_500,
      allowExitOnIdle: true,
    });
    // Idle socket failures must not crash the server or expose connection details.
    // pg removes the failed client; the next request tries a fresh connection.
    pool.on("error", () => {});
    state.databasePool = pool;
  }
  return state.databasePool;
}

export async function isDatabaseAvailable(): Promise<boolean> {
  try {
    const result = await getPool().query<{ value: number }>("SELECT 1 AS value");
    return result.rows[0]?.value === 1;
  } catch {
    return false;
  }
}
