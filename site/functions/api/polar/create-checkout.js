/**
 * POST /api/polar/create-checkout
 * Body: { product_id, email?, success_url?, metadata? }
 * Returns: { url, checkout_id, expires_at }
 *
 * Env vars (Cloudflare Pages):
 *   POLAR_API_KEY  - Organization Access Token (organization_id 指定不可)
 */

const POLAR_API = "https://api.polar.sh/v1";
const DEFAULT_PRODUCT_ID = "06c8e17c-036b-4128-9569-c16c0dad1a4f"; // AIチーム設計キット v0.1

export async function onRequestPost(context) {
  const { request, env } = context;

  const apiKey = env.POLAR_API_KEY;
  if (!apiKey) return json({ error: "POLAR_API_KEY not configured" }, 500);

  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const productId = body.product_id || DEFAULT_PRODUCT_ID;
  const successUrl = body.success_url || "https://ai-nowa.com/shop/thanks/";

  const payload = {
    products: [productId],
    success_url: successUrl,
  };
  if (body.email) payload.customer_email = body.email;
  if (body.metadata) payload.metadata = body.metadata;

  const polarRes = await fetch(`${POLAR_API}/checkouts/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!polarRes.ok) {
    const err = await polarRes.text();
    console.error("Polar checkout error:", err);
    return json({ error: "Checkout creation failed", detail: err }, 502);
  }

  const data = await polarRes.json();
  return json({
    url: data.url,
    checkout_id: data.id,
    expires_at: data.expires_at,
  });
}

export async function onRequestGet(context) {
  // ブラウザから直接アクセス時: そのまま Checkout URL を生成して 302 リダイレクト
  const fakeReq = new Request("https://internal/api/polar/create-checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const res = await onRequestPost({ ...context, request: fakeReq });
  if (!res.ok) return res;
  const { url } = await res.json();
  return Response.redirect(url, 302);
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
