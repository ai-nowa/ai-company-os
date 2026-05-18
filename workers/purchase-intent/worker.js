const HTML = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI NOWA design kit 購入意思確認</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f0f0f;
      color: #e8e8e8;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
    }
    .card {
      background: #1a1a1a;
      border: 1px solid #2a2a2a;
      border-radius: 12px;
      padding: 2.5rem 2rem;
      max-width: 480px;
      width: 100%;
    }
    .badge {
      display: inline-block;
      background: #6c63ff22;
      color: #a89fff;
      font-size: 0.72rem;
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      margin-bottom: 1.2rem;
      letter-spacing: 0.05em;
    }
    h1 {
      font-size: 1.35rem;
      font-weight: 700;
      line-height: 1.4;
      margin-bottom: 0.6rem;
    }
    .subtitle {
      color: #888;
      font-size: 0.88rem;
      margin-bottom: 2rem;
      line-height: 1.6;
    }
    label {
      display: block;
      font-size: 0.85rem;
      color: #aaa;
      margin-bottom: 0.4rem;
    }
    input[type="email"] {
      width: 100%;
      background: #111;
      border: 1px solid #333;
      border-radius: 8px;
      color: #e8e8e8;
      font-size: 0.95rem;
      padding: 0.7rem 0.9rem;
      margin-bottom: 1.2rem;
      outline: none;
      transition: border-color 0.2s;
    }
    input[type="email"]:focus { border-color: #6c63ff; }
    .radio-group { display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1.8rem; }
    .radio-label {
      display: flex;
      align-items: center;
      gap: 0.7rem;
      background: #111;
      border: 1px solid #2a2a2a;
      border-radius: 8px;
      padding: 0.75rem 1rem;
      cursor: pointer;
      font-size: 0.9rem;
      transition: border-color 0.2s;
    }
    .radio-label:has(input:checked) { border-color: #6c63ff; background: #6c63ff11; }
    .radio-label input { accent-color: #6c63ff; }
    button[type="submit"] {
      width: 100%;
      background: #6c63ff;
      color: #fff;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      padding: 0.85rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    button[type="submit"]:hover { background: #5a52e0; }
    .privacy { font-size: 0.75rem; color: #555; margin-top: 1rem; text-align: center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">AI NOWA</div>
    <h1>design kit 購入意思確認</h1>
    <p class="subtitle">AIだけで運営される会社「AI NOWA」が構築した、チーム設計・ワークフロー素材集です。<strong>9,800円・正式リリース時に購入可能</strong>になります。</p>
    <p class="subtitle" style="font-size:0.85rem;color:#999;">本フォームは購入意思を確認するためのものです。ご回答いただいた方には、リリース時にメールでお知らせします。</p>
    <form id="form">
      <label for="email">メールアドレス <span style="color:#f87">*</span></label>
      <input type="email" id="email" name="email" placeholder="your@email.com" required>
      <label>購入意思 <span style="color:#f87">*</span></label>
      <div class="radio-group">
        <label class="radio-label">
          <input type="radio" name="intent" value="yes" required> はい（購入したい）
        </label>
        <label class="radio-label">
          <input type="radio" name="intent" value="maybe"> 検討中
        </label>
      </div>
      <button type="submit" id="btn">送信する</button>
    </form>
    <p class="privacy">メールアドレスはリリース通知のみに使用します</p>
  </div>
  <script>
    document.getElementById('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btn');
      btn.textContent = '送信中...';
      btn.disabled = true;
      const body = {
        email: document.getElementById('email').value,
        intent: document.querySelector('input[name="intent"]:checked').value
      };
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (res.ok) {
        document.querySelector('.card').innerHTML =
          '<div style="text-align:center;padding:2rem 0"><div style="font-size:2.5rem;margin-bottom:1rem">✅</div><h2 style="margin-bottom:0.8rem">ありがとうございます</h2><p style="color:#888;font-size:0.9rem">リリース時にご連絡します</p></div>';
      } else {
        btn.textContent = '送信する';
        btn.disabled = false;
        alert('送信に失敗しました。もう一度お試しください。');
      }
    });
  </script>
</body>
</html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/submit' && request.method === 'POST') {
      let body;
      try {
        body = await request.json();
      } catch {
        return new Response('Bad Request', { status: 400 });
      }
      const { email, intent } = body;
      if (!email || !intent) return new Response('Missing fields', { status: 400 });
      if (!['yes', 'maybe'].includes(intent)) return new Response('Invalid intent', { status: 400 });

      const ts = new Date().toISOString();
      const key = `${ts}_${Math.random().toString(36).slice(2, 8)}`;
      await env.PURCHASE_INTENT.put(key, JSON.stringify({ email, intent, ts }));

      return new Response(JSON.stringify({ ok: true }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (url.pathname === '/api/list' && request.method === 'GET') {
      const secret = url.searchParams.get('secret');
      if (secret !== env.ADMIN_SECRET) {
        return new Response('Unauthorized', { status: 401 });
      }
      const list = await env.PURCHASE_INTENT.list();
      const entries = [];
      for (const key of list.keys) {
        const val = await env.PURCHASE_INTENT.get(key.name);
        if (val) entries.push(JSON.parse(val));
      }
      entries.sort((a, b) => a.ts.localeCompare(b.ts));
      return new Response(JSON.stringify(entries, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(HTML, {
      headers: { 'Content-Type': 'text/html; charset=UTF-8' }
    });
  }
};
