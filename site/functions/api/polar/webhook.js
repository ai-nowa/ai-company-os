/**
 * POST /api/polar/webhook
 * Polar.sh Webhook receiver (暫定: ログ記録のみ、メール配信は手動運用)
 *
 * Env vars (Cloudflare Pages):
 *   POLAR_WEBHOOK_SECRET - Webhook signing secret (設定後に有効化)
 *
 * 本番 Webhook 実装フェーズ:
 *   Phase A (現在): ログ記録のみ → 購入通知はPolar管理画面で確認し手動メール
 *   Phase B (次): R2 + Resend でダウンロードURL自動発行
 */

export async function onRequestPost(context) {
  const { request, env } = context;

  // Webhook signature verification (POLAR_WEBHOOK_SECRET が設定されている場合のみ)
  const webhookSecret = env.POLAR_WEBHOOK_SECRET;
  if (webhookSecret) {
    const signature = request.headers.get("webhook-signature");
    if (!signature) {
      return new Response("Missing signature", { status: 401 });
    }
    const body = await request.text();
    const valid = await verifySignature(body, signature, webhookSecret);
    if (!valid) {
      return new Response("Invalid signature", { status: 401 });
    }
    const event = JSON.parse(body);
    return handleEvent(event);
  }

  // POLAR_WEBHOOK_SECRET 未設定時: bodyをそのまま処理（暫定）
  let event;
  try {
    event = await request.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  return handleEvent(event);
}

async function handleEvent(event) {
  const type = event.type || "unknown";
  const orderId = event.data?.id || "unknown";

  console.log(`[polar-webhook] type=${type} order_id=${orderId}`);

  // order.paid: 購入完了イベント
  if (type === "order.paid") {
    const email = event.data?.customer?.email || "unknown";
    const product = event.data?.product?.name || "unknown";
    console.log(`[polar-webhook] PURCHASE: email=${email} product=${product} order=${orderId}`);
    // TODO Phase B: R2からダウンロードURLを生成 → Resendでメール送信
    // 現在は Polar 管理画面 (polar.sh/dashboard) で注文確認 → 手動メール
  }

  return new Response(JSON.stringify({ received: true, type }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

async function verifySignature(body, signatureHeader, secret) {
  // Polar webhook uses "wh1;timestamp;signature" format
  const parts = signatureHeader.split(",");
  for (const part of parts) {
    const [, ts, sig] = part.match(/^wh1;(\d+);(.+)$/) || [];
    if (!ts || !sig) continue;
    const payload = `${ts}.${body}`;
    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload));
    const expected = Array.from(new Uint8Array(mac))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    if (expected === sig) return true;
  }
  return false;
}
