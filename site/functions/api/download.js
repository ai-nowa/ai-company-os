/**
 * Legacy download endpoint disabled.
 *
 * The old URL scheme included email in query parameters. Downloads should be
 * reintroduced only with opaque tokens that do not expose customer PII.
 */
export async function onRequest() {
  return new Response("Legacy download endpoint disabled", {
    status: 410,
    headers: { "Cache-Control": "no-store" },
  });
}
