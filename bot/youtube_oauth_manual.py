"""YouTube OAuth (Manual Code 入力方式)。

state mismatch 問題と WSL2 localhost 接続問題を一気に解決するため、
ブラウザのリダイレクト URL をユーザーがコピペで返す方式。

Step1: 認証 URL を表示
Step2: ユーザーがブラウザで開いて承認
Step3: リダイレクト先（接続失敗してもアドレスバーに ?code=... が残る）の URL を全部コピー
Step4: それを exchange.py に渡す → token 交換
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google_auth_oauthlib.flow import Flow

BOT_DIR = Path(__file__).parent
CLIENT_SECRET = BOT_DIR / "youtube_client_secret.json"
TOKEN_FILE = BOT_DIR / "youtube_token.json"
STATE_FILE = BOT_DIR / ".oauth_state.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

REDIRECT_URI = "http://localhost:8080/"


def step1_show_url() -> None:
    """Step1: 認証 URL を表示。"""
    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    url, state = flow.authorization_url(access_type="offline", prompt="consent")
    code_verifier = flow.code_verifier

    STATE_FILE.write_text(
        json.dumps({"state": state, "code_verifier": code_verifier}, ensure_ascii=False),
        encoding="utf-8",
    )
    STATE_FILE.chmod(0o600)

    print("=" * 70, flush=True)
    print("📺 認証 URL（コピーしてブラウザで開く）", flush=True)
    print("=" * 70, flush=True)
    print(url, flush=True)
    print("=" * 70, flush=True)
    print("", flush=True)
    print("次の手順:", flush=True)
    print("  1. 上記 URL をブラウザで開く（シークレットウィンドウ推奨）", flush=True)
    print("  2. Google で認証 → 同意 → 「許可」をクリック", flush=True)
    print("  3. ブラウザは『このページに到達できません』エラーを出すが、それは正常", flush=True)
    print("  4. アドレスバーに 'http://localhost:8080/?state=XXX&code=YYY&...' のような URL が残る", flush=True)
    print("  5. その URL を全部コピーして、Discord でいくとさんに渡してください", flush=True)
    print("", flush=True)


def step2_exchange(redirect_url: str) -> None:
    """Step2: code を含むリダイレクト URL から token を取得。"""
    if not STATE_FILE.exists():
        raise SystemExit("❌ Step1 を先に実行してください: python -m bot.youtube_oauth_manual")

    state_data = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    # URL から code を取り出す（state は無視・自前で検証）
    parsed = urlparse(redirect_url)
    qs = parse_qs(parsed.query)
    code = qs.get("code", [None])[0]
    received_state = qs.get("state", [None])[0]

    if not code:
        raise SystemExit(f"❌ URL に code が含まれていません: {redirect_url}")

    # state は念のため検証（不一致なら警告のみ、エラーにしない）
    if received_state != state_data["state"]:
        print(f"⚠️  state 不一致（警告のみ、続行）:", flush=True)
        print(f"   保存: {state_data['state']}", flush=True)
        print(f"   受信: {received_state}", flush=True)

    # Flow を再構築して fetch_token
    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=received_state,  # 受信した state をそのまま使う
    )
    flow.code_verifier = state_data["code_verifier"]

    print(f"🔄 code: {code[:30]}... で token 交換中...", flush=True)
    flow.fetch_token(code=code)
    creds = flow.credentials

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }
    TOKEN_FILE.write_text(json.dumps(token_data, ensure_ascii=False, indent=2), encoding="utf-8")
    TOKEN_FILE.chmod(0o600)

    print(f"✅ token 保存: {TOKEN_FILE}", flush=True)
    print(f"   refresh_token set: {bool(creds.refresh_token)}", flush=True)
    print(f"   expiry: {creds.expiry}", flush=True)

    # 後始末
    STATE_FILE.unlink(missing_ok=True)


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)
    if not CLIENT_SECRET.exists():
        raise SystemExit(f"❌ client secret not found: {CLIENT_SECRET}")

    if len(sys.argv) < 2:
        step1_show_url()
    else:
        step2_exchange(sys.argv[1])


if __name__ == "__main__":
    main()
