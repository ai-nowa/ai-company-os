/**
 * POST /api/polar/create-checkout
 * Body: { product_id?, email?, success_url?, metadata? }
 * Returns: { url, checkout_id, expires_at }
 *
 * Env vars (Cloudflare Pages):
 *   POLAR_API_KEY  - Organization Access Token (organization_id 指定不可)
 */

const POLAR_API = "https://api.polar.sh/v1";
const DEFAULT_PRODUCT_ID = "";

// 現在の /shop は意向受付。実決済を再開する場合は環境変数側で明示的にONにする。
const CHECKOUT_ENABLED = false;

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!CHECKOUT_ENABLED) {
    return json({ error: "Checkout temporarily unavailable", message: "現在販売準備中です。" }, 503);
  }

  const apiKey = env.POLAR_API_KEY;
  if (!apiKey) return json({ error: "POLAR_API_KEY not configured" }, 500);

  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const productId = body.product_id || env.POLAR_PRODUCT_ID || DEFAULT_PRODUCT_ID;
  if (!productId) return json({ error: "POLAR_PRODUCT_ID not configured" }, 500);
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
  if (!CHECKOUT_ENABLED) {
    return new Response(
      `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>販売準備中 — AI NOWA</title><meta http-equiv="refresh" content="3;url=/shop/"></head><body style="font-family:sans-serif;max-width:480px;margin:4rem auto;padding:2rem;text-align:center;color:#222;"><h1 style="font-size:1.3rem;">現在販売準備中です</h1><p>3秒後に商品ページへ戻ります。</p><p><a href="/shop/">商品ページに戻る</a></p></body></html>`,
      { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } }
    );
  }
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
