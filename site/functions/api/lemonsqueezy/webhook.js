/**
 * POST /api/lemonsqueezy/webhook
 * Lemon Squeezy Webhook receiver
 *
 * 対応イベント: order_created
 * フロー: 署名検証 → order情報取得 → (TODO: R2ダウンロードURL発行 → メール送信)
 *
 * Env vars (Cloudflare Pages):
 *   LS_WEBHOOK_SECRET     - Webhook signing secret
 *   LEMONSQUEEZY_API_KEY  - JWT API key (order詳細取得用)
 */

export async function onRequestPost(context) {
  const { request, env } = context;

  const webhookSecret = env.LS_WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error("LS_WEBHOOK_SECRET not set");
    return new Response("Webhook secret not configured", { status: 500 });
  }

  const rawBody = await request.arrayBuffer();
  const signatureHeader = request.headers.get("X-Signature") || "";

  const valid = await verifySignature(rawBody, signatureHeader, webhookSecret);
  if (!valid) {
    console.warn("Webhook signature mismatch");
    return new Response("Unauthorized", { status: 401 });
  }

  let payload;
  try {
    payload = JSON.parse(new TextDecoder().decode(rawBody));
  } catch {
    return new Response("Bad JSON", { status: 400 });
  }

  const eventName = payload?.meta?.event_name;
  console.log("LS webhook:", eventName);

  if (eventName === "order_created") {
    await handleOrderCreated(payload, env);
  }

  return new Response("OK", { status: 200 });
}

async function handleOrderCreated(payload, env) {
  const order = payload?.data?.attributes;
  if (!order) return;

  const customerEmail = order.user_email;
  const orderId = payload?.data?.id;
  const orderNumber = order.order_number;
  const totalFormatted = order.total_formatted;

  console.log(`Order #${orderNumber} (id=${orderId}) from ${customerEmail}, amount=${totalFormatted}`);

  const downloadUrl = await generateDownloadToken(env, orderId, customerEmail);
  if (downloadUrl) {
    console.log(`Download URL generated for order #${orderNumber}: ${downloadUrl}`);
  }

  // TODO: Resendでメール送信する
  // await sendOrderEmail(env, { customerEmail, orderNumber, downloadUrl });
}

/**
 * HMAC-SHA256 署名付きダウンロードURL生成（有効期限72時間）
 * 受信側: GET /api/download?order_id=X&exp=Y&sig=Z
 * Env vars: DOWNLOAD_SECRET, SITE_ORIGIN
 */
async function generateDownloadToken(env, orderId, email) {
  if (!env.DOWNLOAD_SECRET || !env.SITE_ORIGIN) return null;

  const exp = Math.floor(Date.now() / 1000) + 72 * 3600;
  const msg = `${orderId}:${email}:${exp}`;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(env.DOWNLOAD_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg));
  const sigHex = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  const params = new URLSearchParams({ order_id: orderId, email, exp: String(exp), sig: sigHex });
  return `${env.SITE_ORIGIN}/api/download?${params}`;
}

async function verifySignature(bodyBuffer, signatureHex, secret) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const key = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );

  const sigBytes = hexToBytes(signatureHex);
  if (!sigBytes) return false;

  return crypto.subtle.verify("HMAC", key, sigBytes, bodyBuffer);
}

function hexToBytes(hex) {
  if (hex.length % 2 !== 0) return null;
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.slice(i, i + 2), 16);
  }
  return bytes;
}
