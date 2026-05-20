"""Discord bot メインループ（Phase 2.7 マルチクライアント版）。

主要変更点:
- メイン bot (AI NOWA, DISCORD_BOT_TOKEN) と 9社員 bot を 1プロセス内で並列起動
- メンション解析は Discord ネイティブの message.mentions を最優先
- 各社員の応答は その社員 bot として channel.send（プレフィックス不要）
- フォールバック: 社員 client 未起動時は メイン bot がプレフィックス付きで代理投稿
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import uuid
from typing import Optional

import discord

from .architect import run_architect
from .config import (
    DISCORD_BOT_TOKEN,
    DISPLAY_TO_ID,
    EMPLOYEES,
    append_discord_log,
)
from .employee_runner import run_employee_result
from .idea_capture import capture_ideas_from_text
from .mention_chain import (
    chain_call_limit,
    enqueue_deferred_mention,
    extract_mentions,
    extract_meta_tag,
    max_depth,
    mentions_per_response_limit,
    mode_for_mention,
    parse_meta_tag,
    strip_meta_tag,
)
from . import multi_client, thread_registry

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dispatcher")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
main_client = discord.Client(intents=intents)

# 正規表現
MENTION_DISPLAY_RE = re.compile("|".join(re.escape(d) for d in DISPLAY_TO_ID.keys()))
COMMAND_RE = re.compile(r"^!ask\s+(\w+)\s+(.+)$", re.DOTALL)
ARCHITECT_COMMAND_RE = re.compile(r"^!architect\s+(.+)$", re.DOTALL)
KICKOFF_COMMAND_RE = re.compile(r"^!kickoff(?:\s+(.*))?$", re.DOTALL)
USER_MENTION_RE = re.compile(r"<@!?\d+>")

OWNER_DISCORD_NAMES = {"ikuto", "yikuto", "yikuto9805", "0ja3865p244394s"}


def normalize_sender(discord_name: str) -> str:
    base = discord_name.split("#")[0].lower()
    if base in OWNER_DISCORD_NAMES or "ikuto" in base:
        return "いくと"
    return discord_name


def convert_text_mentions_to_discord(text: str) -> str:
    """応答テキスト中の `@表示名`/`@英語ID`/`@名`/`@名字` を `<@&role_id>` に置換。
    Discord 上で本物のメンション（青ハイライト + 通知）として表示される。
    """
    import re as _re
    from .mention_chain import _split_display

    for emp_id, info in EMPLOYEES.items():
        role_id = multi_client.get_role_id_for_emp(emp_id)
        if role_id is None:
            continue
        display = info.get("display", "")
        if not display:
            continue
        family, given = _split_display(display)
        tag = f"<@&{role_id}>"
        # 長いパターンから先に置換（部分マッチを防ぐ）
        candidates = [display, emp_id]
        if family and len(family) >= 2 and family != display:
            candidates.append(family)
        if given and len(given) >= 2 and given != display and given != family:
            candidates.append(given)
        for cand in candidates:
            text = text.replace(f"@{cand}", tag)
    return text


def resolve_initial_targets_native(message: discord.Message) -> list[str]:
    """Discord ネイティブメンション (user + role) から社員IDを順序保持で抽出.
    Bot 招待時に自動生成されるマネージドロールへのメンション (<@&role_id>) も対応."""
    targets: list[str] = []
    seen: set[str] = set()
    # user mention
    for user in message.mentions:
        emp_id = multi_client.get_emp_for_user_id(user.id)
        if emp_id and emp_id not in seen:
            targets.append(emp_id)
            seen.add(emp_id)
    # role mention (bot-managed role)
    for role in getattr(message, "role_mentions", []):
        emp_id = multi_client.get_emp_for_role_id(role.id)
        if emp_id and emp_id not in seen:
            targets.append(emp_id)
            seen.add(emp_id)
    return targets


async def send_employee_response(
    emp_id: str,
    channel: discord.abc.Messageable,
    content: str,
) -> bool:
    """社員 bot として投稿。社員 client が無ければメインbot代理（プレフィックス付き）"""
    if not content:
        return False
    channel_name = getattr(channel, "name", "dm")
    if hasattr(channel, "id"):
        ok = await multi_client.send_as_employee(emp_id, channel.id, content)
        if ok:
            append_discord_log(channel_name, {
                "kind": "employee",
                "author": EMPLOYEES[emp_id]["display"],
                "employee_id": emp_id,
                "text": content,
            })
            capture_ideas_from_text(emp_id, channel_name, content)
            return True
    # フォールバック
    display = EMPLOYEES[emp_id]["display"]
    chunks = [content[i:i + 1900] for i in range(0, len(content), 1900)]
    for i, chunk in enumerate(chunks):
        await channel.send((f"**{display}**:\n" if i == 0 else "") + chunk)
    append_discord_log(channel_name, {
        "kind": "employee",
        "author": display,
        "employee_id": emp_id,
        "text": content,
    })
    capture_ideas_from_text(emp_id, channel_name, content)
    return True


async def send_chunked(channel: discord.abc.Messageable, header: str, text: str) -> None:
    """メインbot として投稿（!architect / コマンド応答用）"""
    if not text:
        text = "(空応答)"
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)]
    for i, chunk in enumerate(chunks):
        await channel.send((header if i == 0 else "") + chunk)


async def find_channel_by_substr(needle: str) -> Optional[discord.TextChannel]:
    needle = needle.strip().lstrip("#").lstrip("📢🏢👀🗓🧾🏛🎯🧩🛠🎬📈⚖☕🌱👏🧯🔁🧠📦")
    needle = needle.strip("｜| -")
    if not needle:
        return None
    for guild in main_client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None


async def create_thread_with_invite(
    parent_channel: discord.TextChannel,
    thread_name: str,
    creator_emp: str,
    invite_emps: list[str],
    private: bool,
) -> Optional[discord.Thread]:
    """メインbot権限でスレッドを作成。同名 active スレッドがあれば使い回す（重複防止）"""
    # 同名 active スレッドが既にあれば使い回す
    existing = thread_registry.find_active_thread_by_name(thread_name, parent_channel.id)
    if existing:
        existing_id = int(existing["thread_id"])
        # 招待された社員を追加（未参加なら）
        for emp in [creator_emp, *invite_emps]:
            if emp not in existing["participants"]:
                thread_registry.add_participant(existing_id, emp)
        # Discord 上のスレッドオブジェクトを取得
        thread_obj = parent_channel.guild.get_thread(existing_id)
        if thread_obj is not None:
            log.info(f"Reusing existing thread: {thread_name} (id={existing_id})")
            return thread_obj
        # オブジェクト取れない場合は新規作成にフォールバック
        log.info(f"Existing thread {existing_id} not accessible, will create new")

    try:
        if private:
            new_thread = await parent_channel.create_thread(
                name=thread_name[:100],
                type=discord.ChannelType.private_thread,
                auto_archive_duration=1440,
                invitable=True,
            )
        else:
            new_thread = await parent_channel.create_thread(
                name=thread_name[:100],
                type=discord.ChannelType.public_thread,
                auto_archive_duration=1440,
            )
        participants = list({creator_emp, *invite_emps})
        thread_registry.register_thread(
            thread_id=new_thread.id,
            name=thread_name,
            channel_id=parent_channel.id,
            participants=participants,
            private=private,
            creator=creator_emp,
        )
        log.info(f"Thread created: {thread_name} (id={new_thread.id}, private={private}, participants={participants})")
        return new_thread
    except discord.HTTPException as e:
        log.warning(f"Thread creation failed: {e}")
        return None


async def process_mention_chain(
    text: str,
    sender: str,
    channel: discord.abc.Messageable,
    depth: int,
    visited: set[str],
    chain_id: Optional[str] = None,
    call_count: int = 0,
    origin: str = "mention",
) -> int:
    """応答本文からメンション抽出 → 各社員を順次起動 → さらに連鎖"""
    chain_id = chain_id or uuid.uuid4().hex[:12]
    channel_name = getattr(channel, "name", "dm")
    targets = extract_mentions(text, exclude=visited)
    if depth >= max_depth():
        for target in targets:
            enqueue_deferred_mention(
                target,
                text=text,
                sender=sender,
                channel=channel_name,
                chain_id=chain_id,
                depth=depth,
                reason=f"chain_depth_limit:{max_depth()}",
            )
        log.warning(f"連鎖深さ {max_depth()} 到達、残りメンションはinboxへ退避")
        return 0

    in_thread = isinstance(channel, discord.Thread)
    allowed_set: Optional[set[str]] = None
    if in_thread:
        allowed_set = set(thread_registry.get_participants(channel.id))

    if allowed_set is not None:
        new_targets: list[str] = []
        for t in targets:
            if t in allowed_set:
                new_targets.append(t)
            else:
                if thread_registry.add_participant(channel.id, t):
                    log.info(f"thread {channel.id}: 自動招待 {t}")
                    new_targets.append(t)
        targets = new_targets

    per_response = mentions_per_response_limit(text, origin=origin)
    immediate_targets = targets[:per_response]
    for deferred in targets[per_response:]:
        enqueue_deferred_mention(
            deferred,
            text=text,
            sender=sender,
            channel=channel_name,
            chain_id=chain_id,
            depth=depth,
            reason=f"per_response_limit:{per_response}",
        )

    total_used = 0
    max_calls = chain_call_limit(origin=origin)
    for target in immediate_targets:
        if call_count + total_used >= max_calls:
            enqueue_deferred_mention(
                target,
                text=text,
                sender=sender,
                channel=channel_name,
                chain_id=chain_id,
                depth=depth,
                reason=f"chain_call_limit:{max_calls}",
            )
            continue
        used = await dispatch_to_employee(
            target,
            text,
            sender,
            channel,
            depth + 1,
            visited | {target},
            chain_id=chain_id,
            call_count=call_count + total_used,
            origin=origin,
        )
        total_used += used
    return total_used


async def dispatch_to_employee(
    target: str,
    user_message: str,
    sender: str,
    channel: discord.abc.Messageable,
    depth: int,
    visited: set[str],
    chain_id: Optional[str] = None,
    call_count: int = 0,
    origin: str = "mention",
) -> int:
    """1人の社員を起動 → 応答投稿 → メタタグ処理 → 連鎖"""
    if target not in EMPLOYEES:
        return 0

    channel_name = getattr(channel, "name", "dm")
    chain_id = chain_id or uuid.uuid4().hex[:12]

    # typing インジケータは「その社員 bot」名義で出す
    typing_target: discord.abc.Messageable = channel
    if hasattr(channel, "id"):
        emp_ch = multi_client.get_channel_for_employee(target, channel.id)
        if emp_ch is not None:
            typing_target = emp_ch

    try:
        async with typing_target.typing():
            result = await run_employee_result(
                target,
                user_message,
                sender=sender,
                channel=channel_name,
                mode=mode_for_mention(user_message),
                reason=f"mention_chain from {sender} in #{channel_name}",
                chain_id=chain_id,
                depth=depth,
            )
    except Exception as e:
        log.exception(f"dispatch_to_employee failed: {target}")
        return 0

    call_used = 1 if result.prompt_chars > 0 else 0
    if not result.ok or not result.text:
        log.info(
            "employee response suppressed: target=%s reason=%s error=%s",
            target,
            result.skipped_reason,
            result.system_error,
        )
        return call_used

    # メタタグ抽出
    raw_response = result.text
    meta_raw = extract_meta_tag(raw_response)
    meta = parse_meta_tag(meta_raw) if meta_raw else {}
    clean_text = strip_meta_tag(raw_response)
    # テキスト @ メンションを Discord ネイティブメンションに変換（投稿時のみ。連鎖検出は変換前の text 経由）
    discord_text = convert_text_mentions_to_discord(clean_text)

    # 投稿先決定
    post_target: discord.abc.Messageable = channel
    if "post_to" in meta:
        alt = await find_channel_by_substr(str(meta["post_to"]))
        if alt:
            post_target = alt

    # スレッド作成
    if "thread" in meta:
        invite = meta.get("invite", [])
        if isinstance(invite, str):
            invite = [s.strip() for s in invite.split(",") if s.strip()]
        private = bool(meta.get("private", False))
        parent = post_target
        if isinstance(parent, discord.Thread):
            parent = parent.parent
        if isinstance(parent, discord.TextChannel):
            new_thread = await create_thread_with_invite(
                parent, str(meta["thread"]), target, list(invite), private
            )
            if new_thread:
                post_target = new_thread

    # 投稿（その社員 bot として、Discord native mention に変換済み）
    posted = await send_employee_response(target, post_target, discord_text)
    if not posted:
        return call_used

    # スレッドクローズ
    if meta.get("close_thread") and isinstance(channel, discord.Thread):
        thread_registry.close_thread(channel.id)
        try:
            await channel.edit(archived=True)
        except discord.HTTPException as e:
            log.warning(f"Thread archive failed: {e}")

    # 連鎖（visited は target 自身のみ → A→B→A→B... の往復が可能、無限ループは depth 100 で防ぐ）
    # ただし「いくと依頼」チャンネル内では連鎖しない（依頼投稿専用、議論は別チャンネルで）
    post_channel_name = getattr(post_target, "name", "")
    if "いくと依頼" in post_channel_name or "📥" in post_channel_name:
        log.info(f"いくと依頼チャンネル内では連鎖スキップ: {target}")
    else:
        child_used = await process_mention_chain(
            clean_text,
            target,
            post_target,
            depth,
            {target},
            chain_id=chain_id,
            call_count=call_count + call_used,
            origin=origin,
        )
        return call_used + child_used
    return call_used


async def ensure_required_channels() -> None:
    """必要なチャンネルが Discord 側に存在するか確認、不足は自動作成。
    discord_setup.CATEGORIES を真実の定義として参照。"""
    from .discord_setup import CATEGORIES
    for guild in main_client.guilds:
        existing_categories = {c.name: c for c in guild.categories}
        existing_channels = {c.name for c in guild.channels}
        for cat_def in CATEGORIES:
            cat = existing_categories.get(cat_def["name"])
            if cat is None:
                try:
                    cat = await guild.create_category(cat_def["name"], reason="auto-create on dispatcher start")
                    log.info(f"created category: {cat_def['name']}")
                except discord.HTTPException as e:
                    log.warning(f"failed to create category {cat_def['name']}: {e}")
                    continue
            for ch_name in cat_def["channels"]:
                if ch_name in existing_channels:
                    continue
                try:
                    await guild.create_text_channel(ch_name, category=cat, reason="auto-create on dispatcher start")
                    log.info(f"created channel: {ch_name}")
                except discord.HTTPException as e:
                    log.warning(f"failed to create channel {ch_name}: {e}")


async def process_architect_outbox_loop() -> None:
    """Architect (Claude) からの投稿要求を 10秒ごとに処理。
    bot/architect_outbox.py の submit_post で提出されたファイルを拾って Discord に投稿。
    """
    import json
    from .architect_outbox import OUTBOX_DIR
    while True:
        try:
            await asyncio.sleep(10)
            if not OUTBOX_DIR.exists():
                continue
            for f in sorted(OUTBOX_DIR.glob("post_*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    ch = await find_channel_by_substr(data["channel"])
                    if ch is None:
                        log.warning(f"architect_outbox: channel '{data['channel']}' not found, keeping file")
                        continue
                    text = convert_text_mentions_to_discord(data["content"])
                    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or ["(空)"]
                    for c in chunks:
                        await ch.send(c)
                    f.unlink()
                    log.info(f"architect_outbox posted: {f.name} -> {ch.name}")
                except Exception:
                    log.exception(f"architect_outbox error processing {f.name}")
        except Exception:
            log.exception("architect_outbox loop error")
            await asyncio.sleep(10)


async def notify_owner_channel_once() -> None:
    """初回起動時のみ、いくと依頼チャンネル開設を全社員に通知（フラグファイルで1回限り保証）"""
    from .config import BASE_DIR
    flag = BASE_DIR / "company" / ".owner_channel_notified"
    if flag.exists():
        return
    log.info("初回通知: いくと依頼チャンネル開設を全社員に発信")
    try:
        from .notify_owner_request_channel import run as notify_run
        await notify_run(main_client)
        flag.touch()
        log.info("初回通知 完了")
    except Exception:
        log.exception("初回通知 失敗")


@main_client.event
async def on_ready() -> None:
    log.info(f"Main client logged in as {main_client.user}")
    # 必要チャンネルの自動作成（不足分のみ）
    try:
        await ensure_required_channels()
    except Exception:
        log.exception("ensure_required_channels failed")
    log.info("9社員 client の起動を開始...")
    status = await multi_client.start_all(intents)
    ready_count = sum(1 for s in status.values() if s.startswith("ready"))
    log.info(f"社員 client 起動結果: {ready_count}/9 ready")
    for emp_id, s in status.items():
        log.info(f"  {emp_id}: {s}")

    # bot-managed role を社員に紐付ける（Discord で @役職名 メンション解決用）
    role_map = await multi_client.build_role_map_from(main_client)
    log.info(f"Role map built: {len(role_map)} employees mapped")
    for emp_id, roles in role_map.items():
        log.info(f"  {emp_id}: {roles}")

    from .daily_loop import make_jobs
    scheduler = make_jobs(main_client)
    scheduler.start()
    log.info("Daily scheduler started (08:05/08:30/12:00/18:00/18:15)")

    # 会社の鼓動: 5分間隔で沈黙チェック、10分沈黙したら誰か起こす（全体の非常用）
    from .heartbeat import make_heartbeat_scheduler
    hb_scheduler = make_heartbeat_scheduler(main_client)
    hb_scheduler.start()
    log.info("Heartbeat scheduler started (check=30min, idle_threshold=90min, daily_limit=4, silent=23-7時)")

    # 各社員の自律ループ: 起動前に should_wake_employee で安く判定し、必要時だけLLM実行
    from .employee_autonomy import start_all_autonomy_loops
    start_all_autonomy_loops(main_client)
    log.info("Employee autonomy loops started (9社員、wake判定付き、silent=23-7時)")

    # 初回限定: いくと依頼チャンネル開設の通知（フラグファイルで1回保証）
    asyncio.create_task(notify_owner_channel_once())

    # Architect (Claude) からの投稿要求を処理するループ（dispatcher 動作中でも投稿可能に）
    asyncio.create_task(process_architect_outbox_loop())
    log.info("Architect outbox loop started (10秒間隔でファイル監視)")


@main_client.event
async def on_message(message: discord.Message) -> None:
    # メイン bot 自身の投稿は無視
    if message.author == main_client.user:
        return

    # 社員 bot の投稿は無視（連鎖は dispatch_to_employee 内の process_mention_chain で
    # in-process に管理する。Discord 経由で2系統発火すると重複起動して暴走するため）
    if message.author.id in multi_client.all_employee_user_ids():
        return

    # 他の bot は無視
    if message.author.bot:
        return

    channel_name = getattr(message.channel, "name", "dm")
    raw = message.content.strip()

    append_discord_log(channel_name, {
        "kind": "human",
        "author": str(message.author),
        "text": raw,
    })

    sender = normalize_sender(str(message.author))

    # !kickoff
    kick_cmd = KICKOFF_COMMAND_RE.match(raw)
    if kick_cmd:
        if sender != "いくと":
            await message.channel.send("`!kickoff` は創業者のみ実行可能です。")
            return
        from .kickoff import kickoff as run_kickoff_sequence
        try:
            await message.channel.send("📡 AI NOWA キックオフを開始します...")
            await run_kickoff_sequence(main_client)
            await message.channel.send("✓ キックオフ完了。")
        except Exception as e:
            log.exception("kickoff failed")
            await message.channel.send(f"(キックオフ失敗: {type(e).__name__}: {e})")
        return

    # !architect
    arch_cmd = ARCHITECT_COMMAND_RE.match(raw)
    if arch_cmd:
        msg = arch_cmd.group(1)
        try:
            async with message.channel.typing():
                response = await run_architect(msg, sender=sender, channel=channel_name)
        except Exception as e:
            log.exception("run_architect failed")
            response = f"(Architect 起動失敗: {type(e).__name__}: {e})"
        # bot 名「設計者（Opus）」が表示されるので、プレフィックスは不要
        await send_chunked(message.channel, "", response)
        return

    # !ask <emp_id> <msg>
    cmd = COMMAND_RE.match(raw)
    if cmd:
        target = cmd.group(1)
        msg = cmd.group(2)
        if target in EMPLOYEES:
            await dispatch_to_employee(target, msg, sender, message.channel, 0, {target})
        else:
            await message.channel.send(f"未登録の社員です: `{target}`")
        return

    # メンション解析: Discord ネイティブ最優先、テキスト @ メンションがフォールバック
    native_targets = resolve_initial_targets_native(message)
    targets = native_targets if native_targets else extract_mentions(raw)

    if not targets:
        # bot 自身（メインbot）がメンションされた場合は COO ミオがデフォルト受信
        if main_client.user in message.mentions:
            targets = ["saegusa_mio"]
            raw = USER_MENTION_RE.sub("", raw).strip()
        else:
            return

    # スレッド内なら参加者制限
    if isinstance(message.channel, discord.Thread):
        participants = set(thread_registry.get_participants(message.channel.id))
        if participants:
            new_targets = []
            for t in targets:
                if t in participants:
                    new_targets.append(t)
                else:
                    thread_registry.add_participant(message.channel.id, t)
                    new_targets.append(t)
            targets = new_targets

    # 並列ターゲットは同じ depth で起動。visited は target 自身のみ（次の連鎖で再帰可能）
    seen: set[str] = set()
    for target in targets:
        if target in seen:
            continue
        seen.add(target)
        await dispatch_to_employee(target, raw, sender, message.channel, 0, {target})


def main() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN が未設定です (.env を確認)")
    main_client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
