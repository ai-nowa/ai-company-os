"""Polar.sh 移行を全社員に通達（Architect から各チャンネルへ）。

dispatcher を停止してから実行する。
- 📢お知らせ: 全社通達
- 経営会議: CEO/COO への商品コンセプト議論依頼
- 開発部: @白瀬カイ への Sandbox 実装着手指示
- 監査部: @神楽アオイ への日本法対応依頼

Usage:
    bot/.venv/bin/python -m bot.dispatcher_manager stop
    bot/.venv/bin/python -m bot.notify_polar_migration
    bot/.venv/bin/python -m bot.dispatcher_manager start
"""
from __future__ import annotations

import asyncio
import logging

import discord

from .architect import run_architect
from .config import DISCORD_BOT_TOKEN

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("notify_polar")


PROMPTS: dict[str, str] = {
    "お知らせ": """📢お知らせチャンネル向けの全社通達を書いてください。
設計者（Opus）の落ち着いた口調、6〜10行。

事実:
- いくと判断（2026-05-18）で決済プラットフォームを Lemon Squeezy → Polar.sh に変更
- 撤退理由: LS は API で商品作成不可（POST /v1/products → 405、実 API テスト確認済）、dashboard 手動必須 = 継続作業禁止令違反
- 採用理由: Polar.sh は全 CRUD API 対応、MoR、Stripe Connect Express 経由で日本対応
- 本番 OAT + Sandbox OAT は発行済（bot/.env: POLAR_API_KEY / POLAR_API_KEY_SANDBOX、いくと発行）
- Verification 申請中（〜2週間）、本番有効化はその後

各部門の役割は `shared/brand/payment.md` を参照。
詳細は経営会議・開発部・監査部で個別通達済。
""",

    "経営会議": """経営会議チャンネル向けの通達を書いてください。
設計者（Opus）の口調、8〜12行。CEO（@有馬レイジ）と COO（@三枝ミオ）が中心読者。

要点:
- Polar.sh 移行は完了（いくと判断）。これから商品ローンチに向けた経営判断が必要
- 商品コンセプト・価格・優先順位は CEO/COO の領分。Architect は議論進行役のみ
- 議論すべき項目:
  1. 初期 SKU は何にするか（候補: AI チーム設計キット v1 = PDF + Markdown + JSON）
  2. 価格帯（候補: 980〜1,980 円、@黒羽ユウ の試算待ち）
  3. ローンチ時期（Verification 通過後 = 2 週間以内に商品準備完了が望ましい）
  4. サブスク化の検討（後で追加可、最初は買い切りでも可）
- @黒羽ユウ にマーケ施策・商品説明文を依頼すること
- @神楽アオイ に特商法・利用規約更新を依頼済（監査部で別途通達）
- Verification 通過までに商品設計を確定させてほしい

参考: `shared/brand/payment.md`、`company/decision_matrix.md` の「商品・価格」行
""",

    "開発部": """開発部チャンネル向けの @白瀬カイ への技術指示を書いてください。
設計者（Opus）の口調、10〜15行。

要点:
- Polar.sh 移行に伴い、Sandbox OAT が .env に保存された（`POLAR_API_KEY_SANDBOX`）
- 本番 OAT も保存済（`POLAR_API_KEY`、Verification 通過後に有効化）
- Lemon Squeezy 撤退の原因（API で商品作成不可、POST /v1/products → 405）を踏まえ、
  Polar.sh では同等の API テストを Sandbox で**必ず最初に**実施し、再発防止すること

着手可能タスク（Sandbox で先に検証）:
1. Polar SDK 統合（@polar-sh/sdk Python、公式: https://github.com/polarsource/polar-python ）
2. **商品作成 API の動作確認**（POST /v1/products）← LS で踏んだ罠の再発防止、最優先
3. Checkout 作成 API（POST /v1/checkouts）
4. R2 時限ダウンロード URL vs Polar Benefits（Files）の比較検証
5. Webhook 受信エンドポイント（/api/polar-webhook、署名検証）の実装

Webhook Secret はいくとが Verification 通過後に発行・連携する。
Sandbox API base: `https://sandbox-api.polar.sh/v1`
Production API base: `https://api.polar.sh/v1`
公式 docs: https://polar.sh/docs

詳細: `shared/brand/payment.md`
""",

    "監査部": """監査部チャンネル向けの @神楽アオイ への法務面通達を書いてください。
設計者（Opus）の口調、6〜10行。

要点:
- Polar.sh は MoR（Merchant of Record）として消費税・VAT・海外決済を代行する
- ただし、日本国内の特商法表示・利用規約・返金規約は販売者側（AI NOWA）で整備が必要
- Polar 経由販売における日本法対応を整理し、ai-nowa.com に掲載するための文面を作成してほしい

参考:
- `shared/brand/payment.md` の「Polar.sh アーキテクチャ」
- `shared/brand/payment_lemonsqueezy_retired.md`（撤退理由の参考）
- 特商法ガイドライン: https://www.no-trouble.caa.go.jp/

成果物（案）: `company/legal/tokushoho.md`, `terms.md`, `refund_policy.md`
完了したら経営会議に報告 → @朝倉ノア が ai-nowa.com に統合する流れ。
""",
}


async def find_channel(client: discord.Client, needle: str):
    for guild in client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None


async def post(client: discord.Client, channel_needle: str, prompt: str) -> None:
    log.info(f"Architect が『{channel_needle}』向け通達を生成中...")
    msg = await run_architect(prompt, sender="ikuto", channel=channel_needle)
    log.info(f"  プレビュー: {msg[:120]}...")

    ch = await find_channel(client, channel_needle)
    if not ch:
        log.warning(f"  channel not found: {channel_needle}")
        return
    chunks = [msg[i:i + 1900] for i in range(0, len(msg), 1900)] or ["(空応答)"]
    for chunk in chunks:
        await ch.send(chunk)
    log.info(f"  ✓ 『{channel_needle}』投稿完了")


async def run(client: discord.Client) -> None:
    for needle, prompt in PROMPTS.items():
        try:
            await post(client, needle, prompt)
        except Exception:
            log.exception(f"post failed: {needle}")
        await asyncio.sleep(2)  # rate limit 回避


def main() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN 未設定")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        log.info(f"Logged in as {client.user}")
        try:
            await run(client)
        except Exception:
            log.exception("notify failed")
        finally:
            await client.close()

    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
