/**
 * POST /api/polar/webhook
 * Polar.sh Webhook receiver
 *
 * Env vars (Cloudflare Pages):
 *   POLAR_WEBHOOK_SECRET  - Webhook signing secret
 *   RESEND_API_KEY        - Resend API key for email delivery
 *
 * R2 Binding (Cloudflare Pages設定):
 *   KIT_BUCKET            - R2バケット "ai-nowa-downloads"
 *
 * Phase A (現在): RESEND_API_KEY or KIT_BUCKET 未設定 → ログのみ・手動メール
 * Phase B: 両方設定済み → order.paid → R2署名付きURL → Resend自動送信
 */

const KIT_FILE_KEY = "ai_nowa_os_starter_kit_v0.1.zip";
const PRESIGNED_EXPIRES = 7 * 24 * 60 * 60; // 7日

export async function onRequestPost(context) {
  const { request, env } = context;
  const webhookSecret = env.POLAR_WEBHOOK_SECRET;

  let body;
  if (webhookSecret) {
    body = await request.text();
    const signature = request.headers.get("webhook-signature");
    if (!signature) return new Response("Missing signature", { status: 401 });
    if (!(await verifySignature(body, signature, webhookSecret))) {
      return new Response("Invalid signature", { status: 401 });
    }
  } else {
    body = await request.text();
  }

  let event;
  try {
    event = JSON.parse(body);
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  return handleEvent(event, env);
}

async function handleEvent(event, env) {
  const type = event.type || "unknown";
  const orderId = event.data?.id || "unknown";
  console.log(`[polar-webhook] type=${type} order_id=${orderId}`);

  if (type === "order.paid") {
    const email = event.data?.customer?.email;
    const productName = event.data?.product?.name || "AI NOWA OS Starter Kit v0.1";

    if (!email) {
      console.error("[polar-webhook] order.paid without customer email");
      return json({ received: true, type, warning: "no email" });
    }

    const phaseB = env.KIT_BUCKET && env.RESEND_API_KEY;
    if (phaseB) {
      await deliverKit(email, productName, orderId, env);
    } else {
      console.log(`[polar-webhook] Phase A: manual delivery needed order=${orderId} email_present=${Boolean(email)}`);
    }
  }

  return json({ received: true, type });
}

async function deliverKit(email, productName, orderId, env) {
  // R2署名付きURL発行（7日有効）
  let downloadUrl;
  try {
    downloadUrl = await env.KIT_BUCKET.createPresignedUrl("GET", KIT_FILE_KEY, {
      expiresIn: PRESIGNED_EXPIRES,
    });
  } catch (e) {
    console.error("[polar-webhook] R2 presign failed:", e.message);
    return;
  }

  // Resendでメール送信
  const emailBody = buildEmailHtml(productName, downloadUrl);
  const resendRes = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: "AI NOWA <noreply@ai-nowa.com>",
      to: [email],
      subject: `【AI NOWA】${productName} — ダウンロードURLのご案内`,
      html: emailBody,
    }),
  });

  if (resendRes.ok) {
    const { id } = await resendRes.json();
    console.log(`[polar-webhook] email sent: resend_id=${id} order=${orderId}`);
  } else {
    const err = await resendRes.text();
    console.error(`[polar-webhook] email failed: ${err}`);
  }
}

function buildEmailHtml(productName, downloadUrl) {
  return `<!DOCTYPE html><html lang="ja"><body style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:2rem;color:#222;">
<h2 style="font-size:1.1rem;margin-bottom:1.5rem;">ご購入ありがとうございます</h2>
<p>「${productName}」をご購入いただき、ありがとうございます。<br>AI NOWA 運営チームです。</p>
<p style="margin-top:1.5rem;">以下のURLよりファイルをダウンロードください。</p>
<div style="background:#f4f4f4;border-radius:8px;padding:1rem 1.2rem;margin:1.5rem 0;">
  <a href="${downloadUrl}" style="color:#7c6fff;word-break:break-all;">${downloadUrl}</a>
  <p style="font-size:0.8rem;color:#888;margin-top:0.5rem;">※ このURLは7日間有効です。</p>
</div>
<p style="font-size:0.85rem;color:#666;">ご不明な点は <a href="mailto:ainowa.supports@gmail.com">ainowa.supports@gmail.com</a> までご連絡ください。</p>
<p style="font-size:0.85rem;color:#666;margin-top:1.5rem;">AI NOWA 運営<br><a href="https://ai-nowa.com">https://ai-nowa.com</a></p>
</body></html>`;
}

async function verifySignature(body, signatureHeader, secret) {
  for (const part of signatureHeader.split(",")) {
    const [, ts, sig] = part.match(/^wh1;(\d+);(.+)$/) || [];
    if (!ts || !sig) continue;
    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const mac = await crypto.subtle.sign(
      "HMAC",
      key,
      new TextEncoder().encode(`${ts}.${body}`)
    );
    const expected = Array.from(new Uint8Array(mac))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    if (expected === sig) return true;
  }
  return false;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
