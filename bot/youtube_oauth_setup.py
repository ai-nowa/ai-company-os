"""YouTube Data API v3 の OAuth 初回認証スクリプト（refresh token 取得）。

実行: bot/.venv/bin/python -m bot.youtube_oauth_setup

フロー:
1. ローカルに http サーバを立てる（port 8080）
2. URL を表示する
3. ユーザーが Windows のブラウザで URL を開く → Google ログイン → 同意
4. リダイレクトでこのスクリプトに code が届く → token 交換
5. bot/youtube_token.json に refresh token を保存

これ以降は YouTube API を refresh_token で自動利用可能。
"""
from __future__ import annotations

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

BOT_DIR = Path(__file__).parent
CLIENT_SECRET = BOT_DIR / "youtube_client_secret.json"
TOKEN_FILE = BOT_DIR / "youtube_token.json"

# 最小スコープ: アップロード可能
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",  # チャンネル情報取得
    "https://www.googleapis.com/auth/yt-analytics.readonly",  # YouTube Analytics
]


def main() -> None:
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # unbuffered output

    if not CLIENT_SECRET.exists():
        raise SystemExit(f"❌ client secret not found: {CLIENT_SECRET}")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET),
        SCOPES,
    )
    flow.redirect_uri = "http://localhost:8080/"

    # 認証 URL を自分で組み立てて先に表示（buffer 問題回避）
    auth_url, _state = flow.authorization_url(
        access_type="offline",  # refresh_token を取るため必須
        prompt="consent",       # 毎回 refresh_token を返してもらう
    )
    print("=" * 70, flush=True)
    print("📺 YouTube OAuth 認証 URL", flush=True)
    print("=" * 70, flush=True)
    print(auth_url, flush=True)
    print("=" * 70, flush=True)
    print("", flush=True)
    print("👉 上記 URL を Windows のブラウザで開いてください", flush=True)
    print("   ログイン → スコープ確認 → 許可", flush=True)
    print("   → localhost:8080 にリダイレクトされて自動完了します", flush=True)
    print("", flush=True)

    # 0.0.0.0:8080 で待ち受け（WSL2 NAT モードでも Windows から localhost でアクセス可能）
    creds = flow.run_local_server(
        host="0.0.0.0",
        port=8080,
        open_browser=False,
        authorization_prompt_message="",  # 既に上で表示済
        success_message="✓ 認証成功。このタブは閉じて構いません。",
    )

    print()
    print("✅ 認証成功！")
    print(f"   access_token (一時): set={bool(creds.token)}")
    print(f"   refresh_token (永続): set={bool(creds.refresh_token)}")
    print(f"   token_uri: {creds.token_uri}")
    print(f"   expiry: {creds.expiry}")
    print()

    # token を保存（refresh_token を含む）
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    TOKEN_FILE.write_text(json.dumps(token_data, ensure_ascii=False, indent=2), encoding="utf-8")
    TOKEN_FILE.chmod(0o600)

    print(f"💾 保存先: {TOKEN_FILE}")
    print()
    print("これで YouTube アップロードが社員から完結できます。")
    print("以降は社員側で:")
    print("  from google.oauth2.credentials import Credentials")
    print(f"  creds = Credentials.from_authorized_user_file('{TOKEN_FILE}')")


if __name__ == "__main__":
    main()
