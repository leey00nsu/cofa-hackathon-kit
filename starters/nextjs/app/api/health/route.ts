import { isDatabaseAvailable } from "../../../lib/db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Connectivity only: this does not establish completion of any business task.
export async function GET() {
  const available = await isDatabaseAvailable();
  return Response.json(
    available
      ? { status: "ok", database: "connected" }
      : { status: "error", database: "unavailable" },
    { status: available ? 200 : 503, headers: { "Cache-Control": "no-store" } },
  );
}
