/**
 * POST /api/intent-click
 * Body: { source?: string, kind?: string }   // optional metadata
 *
 * EXP-002 計測（B案）: shop ページの意向ボタン押下を記録する。
 * - Workers Analytics Engine バインディング ANALYTICS があればそちらに書き込む
 * - なくても 200 を返し、Pages Functions のリクエストログに痕跡を残す
 *   （CF Dashboard > Pages > ai-nowa > Functions > Logs で件数集計可能）
 *
 * Env (optional):
 *   ANALYTICS  - Workers Analytics Engine binding（dataset: shop_intent）
 *
 * セキュリティ:
 *   - 認証不要（クリック計測のため）
 *   - Bot/プリフェッチノイズは許容（B案の前提）
 *   - 受け取る値は kind/source のみ。連絡先や自由入力は受け付けない
 */
const ALLOWED_KIND = new Set(["intent_click", "shop_view"]);
const ALLOWED_SOURCE = /^[a-z0-9_\-]{1,32}$/i;

export async function onRequestPost(context) {
  const { request, env } = context;

  let kind = "intent_click";
  let source = "unknown";
  try {
    const body = await request.json();
    if (typeof body?.kind === "string" && ALLOWED_KIND.has(body.kind)) {
      kind = body.kind;
    }
    if (typeof body?.source === "string" && ALLOWED_SOURCE.test(body.source)) {
      source = body.source;
    }
  } catch {
    // 空 body / 不正 JSON も許容（デフォルト値で記録）
  }

  const ts = Date.now();
  const country = request.cf?.country || "XX";

  if (env.ANALYTICS && typeof env.ANALYTICS.writeDataPoint === "function") {
    try {
      env.ANALYTICS.writeDataPoint({
        blobs: [kind, source, country],
        doubles: [1],
        indexes: [kind],
      });
    } catch (e) {
      console.log(`intent-click AE write failed: ${e?.message || e}`);
    }
  } else {
    console.log(`intent-click ts=${ts} kind=${kind} source=${source} country=${country}`);
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

export function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
    },
  });
}
