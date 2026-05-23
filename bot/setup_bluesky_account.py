"""Bluesky ai-nowa アカウント作成ワンショットスクリプト。

使い方:
    bot/.venv/bin/python bot/setup_bluesky_account.py --email YOUR_EMAIL

完了すると .env に BLUESKY_HANDLE / BLUESKY_APP_PASSWORD が追記される。
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)


def create_account(email: str, handle: str = "ai-nowa.bsky.social") -> dict:
    from atproto import Client, models

    password = secrets.token_urlsafe(20)
    c = Client()
    result = c.com.atproto.server.create_account(
        models.ComAtprotoServerCreateAccount.Data(
            handle=handle,
            email=email,
            password=password,
        )
    )
    return {"handle": result.handle, "did": result.did, "password": password}


def create_app_password(handle: str, password: str, app_name: str = "ai-nowa-bot") -> str:
    from atproto import Client

    c = Client()
    c.login(handle, password)
    result = c.com.atproto.server.create_app_password(
        {"name": app_name}
    )
    return result.password


def set_profile(handle: str, app_password: str) -> None:
    """アカウント作成直後にプロフィールを設定する。"""
    from atproto import Client

    c = Client()
    c.login(handle, app_password)
    c.com.atproto.repo.put_record({
        "repo": c.me.did,
        "collection": "app.bsky.actor.profile",
        "rkey": "self",
        "record": {
            "$type": "app.bsky.actor.profile",
            "displayName": "AI NOWA",
            "description": "AI社員9人が自律運営する会社、AI NOWAの公式アカウント。\n9人のキャラクターが毎日Discord上で会議して、記事を書いて、YouTubeを作っています。",
        }
    })
    print(f"✅ プロフィール設定完了: @{handle}")


def append_env(handle: str, app_password: str) -> None:
    existing = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    if "BLUESKY_HANDLE" not in existing:
        with ENV_PATH.open("a", encoding="utf-8") as f:
            f.write(f"\nBLUESKY_HANDLE={handle}\n")
            f.write(f"BLUESKY_APP_PASSWORD={app_password}\n")
        print(f"✅ .env に BLUESKY_HANDLE / BLUESKY_APP_PASSWORD を追記しました")
    else:
        print("⚠️  BLUESKY_HANDLE は既に .env にあります。手動で確認してください。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="アカウント登録用メアド")
    parser.add_argument("--handle", default="ai-nowa.bsky.social")
    args = parser.parse_args()

    print(f"[1/3] アカウント作成: {args.handle}")
    try:
        info = create_account(args.email, args.handle)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"[2/3] アプリパスワード生成")
    try:
        app_pw = create_app_password(info["handle"], info["password"])
    except Exception as e:
        print(f"ERROR (app password): {e}")
        print(f"  handle={info['handle']}, password={info['password']} でログインして手動生成してください")
        sys.exit(1)

    print(f"[3/4] プロフィール設定")
    try:
        set_profile(info["handle"], app_pw)
    except Exception as e:
        print(f"WARNING (profile): {e} — 手動で設定してください")

    print(f"[4/4] .env に書き込み")
    append_env(info["handle"], app_pw)

    print(f"\n完了:")
    print(f"  handle:  {info['handle']}")
    print(f"  DID:     {info['did']}")
    print(f"  bsky URL: https://bsky.app/profile/{info['handle']}")
