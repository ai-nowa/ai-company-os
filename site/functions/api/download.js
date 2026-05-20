/**
 * GET /api/download?order_id=X&email=Y&exp=Z&sig=W
 * トークン検証 → R2からファイルを返す（有効期限72時間）
 *
 * Env vars:
 *   DOWNLOAD_SECRET  - webhook.jsと同じ署名シークレット
 *   R2_BUCKET        - R2バインディング（バケット: ai-nowa-downloads）
 */

const DOWNLOAD_KEY = "downloads/ai-team-kit-v01.zip";

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const orderId = url.searchParams.get("order_id");
  const email = url.searchParams.get("email");
  const exp = url.searchParams.get("exp");
  const sig = url.searchParams.get("sig");

  if (!orderId || !email || !exp || !sig) {
    return new Response("Missing parameters", { status: 400 });
  }

  if (!env.DOWNLOAD_SECRET) {
    return new Response("Not configured", { status: 500 });
  }

  if (Math.floor(Date.now() / 1000) > Number(exp)) {
    return new Response("Link expired", { status: 410 });
  }

  const valid = await verifyToken(env.DOWNLOAD_SECRET, orderId, email, exp, sig);
  if (!valid) {
    return new Response("Invalid token", { status: 403 });
  }

  if (!env.R2_BUCKET) {
    return new Response("Download not available yet", { status: 503 });
  }

  const obj = await env.R2_BUCKET.get(DOWNLOAD_KEY);
  if (!obj) {
    return new Response("File not found", { status: 404 });
  }

  return new Response(obj.body, {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="ai-team-kit-v01.zip"`,
      "Cache-Control": "no-store",
    },
  });
}

async function verifyToken(secret, orderId, email, exp, sigHex) {
  const msg = `${orderId}:${email}:${exp}`;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const sigBytes = hexToBytes(sigHex);
  if (!sigBytes) return false;
  return crypto.subtle.verify("HMAC", key, sigBytes, new TextEncoder().encode(msg));
}

function hexToBytes(hex) {
  if (hex.length % 2 !== 0) return null;
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.slice(i, i + 2), 16);
  }
  return bytes;
}
