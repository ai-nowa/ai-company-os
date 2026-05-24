/**
 * Deprecated Lemon Squeezy checkout endpoint.
 *
 * AI NOWA currently uses the /shop intent flow and Polar-oriented future
 * checkout work. Keep this route as an explicit tombstone so old clients do
 * not accidentally create stale purchases or collect customer data.
 */
export async function onRequest() {
  return new Response(
    JSON.stringify({
      error: "disabled",
      message: "Lemon Squeezy checkout is deprecated. Use the /shop intent flow.",
    }),
    {
      status: 410,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    },
  );
}
