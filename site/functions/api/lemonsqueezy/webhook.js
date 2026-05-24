/**
 * Deprecated Lemon Squeezy webhook endpoint.
 *
 * The previous implementation handled order PII for an abandoned sales path.
 * This route now fails closed and stores nothing.
 */
export async function onRequest() {
  return new Response("Lemon Squeezy webhook disabled", {
    status: 410,
    headers: { "Cache-Control": "no-store" },
  });
}
