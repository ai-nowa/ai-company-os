/**
 * POST /api/lemonsqueezy/create-checkout
 * Body: { variant_id, email?, custom_data? }
 * Returns: { url }
 *
 * Env vars (Cloudflare Pages):
 *   LEMONSQUEEZY_API_KEY  - JWT API key
 *   LS_STORE_ID           - "379291"
 */

const LS_API = "https://api.lemonsqueezy.com/v1";

export async function onRequestPost(context) {
  const { request, env } = context;

  const apiKey = env.LEMONSQUEEZY_API_KEY;
  const storeId = env.LS_STORE_ID || "379291";

  if (!apiKey) {
    return json({ error: "API key not configured" }, 500);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400);
  }

  const { variant_id, email, custom_data } = body;
  if (!variant_id) {
    return json({ error: "variant_id required" }, 400);
  }

  const attrs = {
    checkout_options: {
      embed: false,
      media: true,
      logo: true,
      desc: true,
      discount: true,
      dark: true,
      button_color: "#18181b",
    },
    checkout_data: {
      custom: custom_data || {},
    },
    test_mode: env.LS_TEST_MODE !== "false",
  };
  if (email) attrs.checkout_data.email = email;

  const payload = {
    data: {
      type: "checkouts",
      attributes: attrs,
      relationships: {
        store: { data: { type: "stores", id: storeId } },
        variant: { data: { type: "variants", id: String(variant_id) } },
      },
    },
  };

  const lsRes = await fetch(`${LS_API}/checkouts`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      Accept: "application/vnd.api+json",
      "Content-Type": "application/vnd.api+json",
    },
    body: JSON.stringify(payload),
  });

  if (!lsRes.ok) {
    const err = await lsRes.text();
    console.error("LS checkout error:", err);
    return json({ error: "Checkout creation failed", detail: err }, 502);
  }

  const data = await lsRes.json();
  const url = data?.data?.attributes?.url;

  if (!url) {
    return json({ error: "No URL in response" }, 502);
  }

  return json({ url });
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
