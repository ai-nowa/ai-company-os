# 認証情報保管設計 — 1枚まとめ

_作成: 白瀬カイ / 2026-05-16_
_宛先: @神楽アオイ（朝一レビュー） @朝倉ノア（PM確認）_
_方針確定者: 有馬レイジ（SOPS + age 採用、2026-05-16）_

---

## 設計サマリ

| 項目 | 決定内容 |
|---|---|
| 保管対象 | note_session_cookie のみ（ID/PW は保持しない） |
| 暗号化方式 | SOPS + age（age keypair。公開鍵のみ repo に commit） |
| 保管場所 | `bot/.env.age`（gitignore 対象、暗号化済み） |
| 実行時復号 | `sops exec-env bot/.env.age 'python -m bot.dispatcher'` |
| 漏洩時の最大被害 | note セッション一時乗っ取りのみ（ID/PW 漏洩は発生しない） |

---

## 1. 認証情報の流れ（保管 → 使用 → 更新）

```
[いくとがブラウザで取得]
    ↓  cookie 値（平文）
[sops encrypt → bot/.env.age]
    ↓  git commit（暗号化済み、平文は commit しない）
[bot 起動時: sops exec-env で復号]
    ↓  環境変数 NOTE_SESSION_COOKIE（メモリのみ）
[HTTP ヘッダーに注入]
    ↓  API call to note.com
[401/403 検知 → Discord 通知]
    ↓  いくとが再取得 → 再 encrypt → 再 commit
```

---

## 2. 復号鍵の所在（アオイ観点）

| 鍵 | 場所 | 保管者 | repo に入るか |
|---|---|---|---|
| age 公開鍵 | `.age-recipients` | 全員参照可 | ✅ commit 可（公開鍵は漏れても問題なし） |
| age 秘密鍵 | いくとの手元のみ | いくと | ❌ 絶対に commit しない |
| `SOPS_AGE_KEY` 環境変数 | bot 実行環境のみ | いくと / bot サーバー | ❌ env var として注入（ファイルに残さない） |

秘密鍵の保管候補: いくとのローカル `~/.config/sops/age/keys.txt`（mode 600）

---

## 3. .env 運用境界（アオイ観点）

| プロセス | .env.age を読む権限 | 平文 cookie にアクセスできるか |
|---|---|---|
| bot/dispatcher.py | ✅（sops exec-env 経由） | ✅ メモリ内のみ |
| employee_runner.py | ❌（直接呼ばない） | ❌ |
| git / CI | ❌（gitignore + no secret in env） | ❌ |
| いくと（手元実行） | ✅（sops 秘密鍵保有） | ✅（復号可能） |

bot が落ちても `.env.age` は暗号化済みのためそのまま残って問題なし。

---

## 4. ログ・stdout/stderr ポリシー（アオイ観点）

### 出力 NG（絶対に出さない）

- Cookie 値そのもの
- Cookie のハッシュ・一部マスク文字列
- セッション ID の断片
- `NOTE_SESSION_COOKIE` を含む環境変数ダンプ

### 出力 OK（boolean のみ）

```python
# 正しい例
logger.info("note_session: valid")
logger.warning("note_session: invalid — sending Discord alert")

# 禁止例
logger.debug(f"cookie={os.environ['NOTE_SESSION_COOKIE']}")  # NG
logger.debug(f"cookie_hash={hashlib.md5(cookie).hexdigest()}")  # NG
```

---

## 5. Cookie 失効シナリオ

### 想定失効頻度

- note セッション Cookie の有効期限: 約 30 日（ログイン維持設定時）
- 最悪ケース: 月 1〜2 回の再取得が必要

### 失効検知方法

```python
# HTTP 401 / 403 を受けたら即通知
if response.status_code in (401, 403):
    discord.send("#いくと依頼", "⚠️ note session cookie 失効。再取得が必要です。手順: .../README.md#cookie-refresh")
    raise CookieExpiredError()
```

- サイレント失敗は禁止。検知したら必ず Discord 通知。

### いくと再取得の所要時間

| 手順 | 所要時間 |
|---|---|
| ブラウザで note.com にログイン | 1 分 |
| DevTools → Application → Cookies → `note_session_v5` コピー | 1 分 |
| `sops encrypt` で `.env.age` 更新 | 1 分 |
| `git commit && gh push` | 1 分 |
| bot 再起動で反映 | 30 秒 |
| **合計** | **約 5 分** |

最短導線: `shared/docs/cookie_refresh_howto.md`（次フェーズで作成）に手順を固定する。

### 高頻度失効時の代替案

1. **Zenn へ完全移行**（現在進行中。GitHub push = publish なので Cookie 不要）
2. note の「ログイン維持」設定を確認（有効化で有効期限延長可能性）
3. 月 1〜2 回を超えたら note 運用を停止・Zenn 一本化を CEO に提案

---

## 6. cookie_refresh_history の扱い

| 項目 | 決定内容 |
|---|---|
| 保存場所 | `bot/cookie_refresh_history.log` |
| gitignore 対象 | ✅（`.gitignore` に追記必要） |
| 保存形式 | JSON Lines: `{"ts": "...", "result": "valid" \| "invalid" \| "refreshed"}` |
| Cookie 値の記録 | ❌ 絶対に含めない |
| 保持期間 | 直近 30 エントリのみ（起動時に古いものを自動削除） |
| 暗号化 | 不要（boolean のみなので平文可） |

---

## 7. アオイへの確認依頼事項

以下の 4 点について、明日朝レビューで判定をください：

1. age 秘密鍵の保管場所（いくとのローカルのみ）で問題ないか
2. `cookie_refresh_history.log` を gitignore + 平文で十分か（暗号化が必要か）
3. `.env.age` を bot サーバーのファイルシステムに置く運用で問題ないか（メモリのみに限定すべきか）
4. bot 再起動時に `SOPS_AGE_KEY` を環境変数として渡す運用のリスク評価

---

_レイジ確定方針（SOPS + age）をベースに作成。アオイの差し戻しがあれば即修正します。_
