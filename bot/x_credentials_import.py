"""X API 認証情報をローカルファイルから安全に取り込むスクリプト。

使い方:
  1. ~/x_api_keys.txt に以下の形式で値を書く（各行 KEY=VALUE）:
       api_key=xxxxx
       api_secret=xxxxx
       access_token=xxxxx
       access_token_secret=xxxxx
       bearer_token=xxxxx
  2. このスクリプトを実行する:
       python -m bot.x_credentials_import
  3. 完了後 ~/x_api_keys.txt を削除する:
       rm ~/x_api_keys.txt
"""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

KEYS_FILE = Path.home() / "x_api_keys.txt"
OUTPUT_FILE = Path(__file__).parent / "x_credentials.json"

REQUIRED_KEYS = {"api_key", "api_secret", "access_token", "access_token_secret", "bearer_token"}


def main() -> None:
    if not KEYS_FILE.exists():
        print(f"ERROR: {KEYS_FILE} not found.")
        print("Create it with the following content:")
        print("  api_key=YOUR_KEY")
        print("  api_secret=YOUR_SECRET")
        print("  access_token=YOUR_TOKEN")
        print("  access_token_secret=YOUR_TOKEN_SECRET")
        print("  bearer_token=YOUR_BEARER_TOKEN")
        sys.exit(1)

    creds: dict[str, str] = {}
    for line in KEYS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        creds[key.strip()] = value.strip()

    missing = REQUIRED_KEYS - set(creds.keys())
    if missing:
        print(f"ERROR: Missing keys: {missing}")
        sys.exit(1)

    OUTPUT_FILE.write_text(
        json.dumps({k: creds[k] for k in sorted(REQUIRED_KEYS)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUTPUT_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600

    print(f"OK: Credentials saved to {OUTPUT_FILE} (mode 0600)")
    print()
    print("Next step: delete the source file")
    print(f"  rm {KEYS_FILE}")
    print()
    print("Verify with dry-run:")
    print("  python -c \"from bot.x_publisher import post_tweet; print(post_tweet('test', dry_run=True))\"")


if __name__ == "__main__":
    main()
