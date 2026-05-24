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
import time
import uuid
from typing import Optional

import discord

from .architect import run_architect
from .architect_policy import (
    auto_response_max_calls,
    auto_response_window_seconds,
    should_auto_architect_respond,
)
from .config import (
    DISCORD_BOT_TOKEN,
    DISPLAY_TO_ID,
    EMPLOYEES,
    append_discord_log,
)
from .context_assembler import write_usage_metric
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
from . import dynamic_config, multi_client, thread_registry

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
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

# Architect 自動応答: 社員が @設計者 とメンションした時に自動起動
ARCHITECT_MENTION_PATTERNS = ["@設計者", "@Architect", "@Opus", "設計者（Architect）", "設計者（Opus）", "@AI NOWA"]
_architect_auto_response_history: list[float] = []  # [timestamp, ...]

def _has_architect_mention(text: str) -> bool:
    return any(p in text for p in ARCHITECT_MENTION_PATTERNS)

def _can_architect_auto_respond() -> bool:
    """Architect 自動応答の rate limit。デフォルトは過去30分で2回まで。"""
    import time
    now = time.time()
    window = auto_response_window_seconds()
    max_calls = auto_response_max_calls()
    _architect_auto_response_history[:] = [t for t in _architect_auto_response_history if now - t < window]
    if len(_architect_auto_response_history) >= max_calls:
        return False
    _architect_auto_response_history.append(now)
    return True


def _record_architect_auto_skip(reason: str, sender: str, content: str) -> None:
    write_usage_metric(
        employee_id="architect",
        mode="architect:auto",
        reason=f"{sender}: {content[:160]}",
        skipped_reason=reason,
    )


def _cfg_bool(path: str, default: bool = True) -> bool:
    value = dynamic_config.get(path, default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _admin_queue_enabled() -> bool:
    env_enabled = os.environ.get("AI_NOWA_ADMIN_QUEUE_ENABLED", "").strip().lower()
    if env_enabled in {"1", "true", "yes", "on"}:
        return True
    return _cfg_bool("admin_queue.enabled", False)


def _safe_architect_failure_text(exc: Exception) -> str:
    """Discord に CLI の生エラーや usage limit 文言を出さない。"""
    return "設計者の実行が一時的に失敗しました。詳細はサーバーログに記録しました。"


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
    original = needle
    needle = needle.strip().lstrip("#").lstrip("📢🏢👀🗓🧾🏛🎯🧩🛠🎬📈⚖☕🌱👏🧯🔁🧠📦")
    needle = needle.strip("｜| -")
    if not needle:
        return None

    # main_client.guilds を優先。autonomy 経由など main_client がまだ ready でない文脈では空になりうるため、
    # 社員 bot client（multi_client）にフォールバックする。
    guilds = list(main_client.guilds)
    if not guilds:
        for client in multi_client.get_clients().values():
            if client.guilds:
                guilds = list(client.guilds)
                break

    if not guilds:
        log.warning(
            f"find_channel_by_substr: no guilds available (main_client and multi_client both empty) "
            f"for needle={original!r}"
        )
        return None

    for guild in guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch

    # マッチしなかった: デバッグ用にチャンネル一覧をログ
    available = [ch.name for guild in guilds for ch in guild.channels if isinstance(ch, discord.TextChannel)]
    log.warning(
        f"find_channel_by_substr: needle={original!r} (stripped={needle!r}) not matched "
        f"in {len(available)} text channels. sample={available[:8]}"
    )
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

    # 社員間メンション暴走防止: 同一 emp_id が 1 時間 20 件超で clip
    if sender in EMPLOYEES and immediate_targets:
        from .mention_rate_limiter import clip_employee_mentions
        immediate_targets, _clipped = clip_employee_mentions(sender, immediate_targets)
        if _clipped > 0:
            log.warning(
                f"employee mention burst clipped: sender={sender} dropped={_clipped} "
                f"(1時間20件上限)"
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

    _t0 = time.perf_counter()
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
    finally:
        try:
            _latency_ms = int((time.perf_counter() - _t0) * 1000)
            write_usage_metric(
                employee_id=target,
                mode="mention_chain",
                reason=f"latency_hook: {sender} → {target}",
                chain_id=chain_id,
                latency_ms=_latency_ms,
            )
        except Exception:
            pass

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

    # POST ブロック処理: [POST: ...]...[/POST] があれば中身を抽出しチャンネルルーティング
    # チャンネル指定ありのブロックはそのチャンネルへ、指定なしは元チャンネルへ投稿
    from .employee_autonomy import extract_post_blocks, POST_BLOCK_RE
    post_blocks = extract_post_blocks(clean_text)
    routed_blocks: list[tuple[str, str]] = []  # (channel_hint, content)
    if post_blocks:
        default_parts: list[str] = []
        for ch_hint, content in post_blocks:
            if ch_hint:
                routed_blocks.append((ch_hint, content))
            else:
                default_parts.append(content)
        clean_text = "\n\n".join(default_parts)
    else:
        # POST マーカーだけ残っている場合は除去（中身は保持）
        clean_text = POST_BLOCK_RE.sub(lambda m: (m.group(2) or "").strip(), clean_text)

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
    # clean_text が空の場合（全ブロックが別チャンネル指定）は元チャンネルへの投稿をスキップ
    posted = False
    if clean_text.strip():
        posted = await send_employee_response(target, post_target, discord_text)
        if not posted:
            return call_used

    # チャンネル指定ありのPOSTブロックを各チャンネルへ個別投稿
    for ch_hint, routed_content in routed_blocks:
        routed_ch = await find_channel_by_substr(ch_hint)
        if routed_ch is None:
            log.warning(f"routed POST: channel '{ch_hint}' not found, skipping")
            continue
        routed_discord = convert_text_mentions_to_discord(routed_content)
        await send_employee_response(target, routed_ch, routed_discord)
        log.info(f"routed POST: {target} → #{routed_ch.name} ({len(routed_content)} chars)")
        posted = True

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
            files = sorted(OUTBOX_DIR.glob("post_*.json")) + sorted(OUTBOX_DIR.glob("processing_post_*.json"))
            for f in files:
                try:
                    if f.name.startswith("post_"):
                        processing = OUTBOX_DIR / f"processing_{f.name}"
                        try:
                            f.rename(processing)
                        except FileNotFoundError:
                            continue
                        except OSError:
                            log.exception("architect_outbox: failed to acquire %s", f.name)
                            continue
                        f = processing

                    data = json.loads(f.read_text(encoding="utf-8"))
                    ch = await find_channel_by_substr(data["channel"])
                    if ch is None:
                        log.warning(f"architect_outbox: channel '{data['channel']}' not found, keeping file")
                        if f.name.startswith("processing_") and not data.get("posted_at"):
                            original = OUTBOX_DIR / f.name.removeprefix("processing_")
                            if not original.exists():
                                f.rename(original)
                        continue

                    if not data.get("posted_at"):
                        text = convert_text_mentions_to_discord(data["content"])
                        chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or ["(空)"]
                        for c in chunks:
                            await ch.send(c)
                        from .config import now_jst_iso
                        data["posted_at"] = now_jst_iso()
                        data["posted_channel"] = getattr(ch, "name", "")
                        data["posted_chunks"] = len(chunks)
                        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

                    dispatch_targets = data.get("dispatch_to") or []
                    if isinstance(dispatch_targets, str):
                        dispatch_targets = [dispatch_targets]
                    valid_targets = [t for t in dispatch_targets if t in EMPLOYEES]
                    for t in dispatch_targets:
                        if t not in EMPLOYEES:
                            log.warning("architect_outbox: unknown dispatch target: %s", t)
                    if valid_targets:
                        max_targets = int(dynamic_config.get("architect_outbox.max_dispatch_targets", 2))
                        if len(valid_targets) > max_targets:
                            dropped = valid_targets[max_targets:]
                            log.warning(
                                "architect_outbox: dispatch target cap applied: kept=%s dropped=%s",
                                valid_targets[:max_targets],
                                dropped,
                            )
                            write_usage_metric(
                                employee_id="architect",
                                mode="architect_outbox",
                                reason=f"dispatch target cap: {f.name}",
                                skipped_reason=f"dispatch_targets_clipped:{len(dropped)}",
                            )
                            valid_targets = valid_targets[:max_targets]
                        log.info(f"architect_outbox: dispatching to {len(valid_targets)} employees in PARALLEL: {valid_targets}")
                        tasks = [
                            dispatch_to_employee(
                                target,
                                data["content"],
                                "設計者（Architect）",
                                ch,
                                0,
                                {target},
                                origin="architect",
                            )
                            for target in valid_targets
                        ]
                        timeout_s = int(dynamic_config.get("architect_outbox.dispatch_timeout_seconds", 900))
                        results = await asyncio.wait_for(
                            asyncio.gather(*tasks, return_exceptions=True),
                            timeout=timeout_s,
                        )
                        for target, result in zip(valid_targets, results):
                            if isinstance(result, Exception):
                                log.error(f"architect_outbox parallel dispatch failed: {target}: {result}")
                    f.unlink()
                    log.info(f"architect_outbox posted: {f.name} -> {ch.name}")
                except asyncio.TimeoutError:
                    log.exception(f"architect_outbox dispatch timeout: {f.name}")
                except Exception:
                    log.exception(f"architect_outbox error processing {f.name}")
        except Exception:
            log.exception("architect_outbox loop error")
            await asyncio.sleep(10)


async def execute_admin_op(op: str, params: dict) -> dict:
    """Architect からの管理操作を実行（dispatcher を停止せずチャンネル作成・招待リンク等）"""
    if not _admin_queue_enabled():
        return {"ok": False, "error": "admin_queue_disabled"}

    allowed_ops = set(dynamic_config.get("admin_queue.allowed_ops", [
        "create_channel",
        "create_invite",
        "update_everyone_permission",
    ]))
    if op not in allowed_ops:
        return {"ok": False, "error": f"op_not_allowed: {op}"}

    guild = main_client.guilds[0] if main_client.guilds else None
    if not guild:
        return {"ok": False, "error": "no guild"}

    if op == "create_channel":
        name = params["name"]
        topic = params.get("topic", "")
        allow_everyone_send = params.get("allow_everyone_send", False)
        category_name = params.get("category", None)
        overwrites = {}
        if allow_everyone_send:
            everyone = guild.default_role
            overwrites[everyone] = discord.PermissionOverwrite(
                send_messages=True,
                view_channel=True,
                read_message_history=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
            )
        category = None
        if category_name:
            for c in guild.categories:
                if c.name == category_name:
                    category = c
                    break
        ch = await guild.create_text_channel(
            name=name, topic=topic, overwrites=overwrites, category=category,
        )
        return {"ok": True, "channel_id": ch.id, "channel_name": ch.name}

    if op == "create_invite":
        channel_id = params.get("channel_id")
        max_age = int(params.get("max_age", dynamic_config.get("admin_queue.default_invite_max_age", 86400)))
        max_uses = int(params.get("max_uses", dynamic_config.get("admin_queue.default_invite_max_uses", 1)))
        if max_age <= 0 or max_uses <= 0:
            return {"ok": False, "error": "unlimited_invite_rejected"}
        ch = guild.get_channel(channel_id) if channel_id else None
        if not ch:
            for c in guild.text_channels:
                if c.name == params.get("channel_name", ""):
                    ch = c
                    break
        if not ch:
            return {"ok": False, "error": f"channel not found: {params}"}
        invite = await ch.create_invite(max_age=max_age, max_uses=max_uses, unique=True)
        return {"ok": True, "invite_url": invite.url, "channel": ch.name}

    if op == "update_everyone_permission":
        channel_id = params.get("channel_id")
        channel_name = params.get("channel_name")
        ch = guild.get_channel(channel_id) if channel_id else None
        if not ch and channel_name:
            for c in guild.text_channels:
                if c.name == channel_name:
                    ch = c
                    break
        if not ch:
            return {"ok": False, "error": "channel not found"}
        everyone = guild.default_role
        perm_kwargs = {}
        if "send_messages" in params:
            perm_kwargs["send_messages"] = params["send_messages"]
        if "view_channel" in params:
            perm_kwargs["view_channel"] = params["view_channel"]
        if "add_reactions" in params:
            perm_kwargs["add_reactions"] = params["add_reactions"]
        await ch.set_permissions(everyone, **perm_kwargs)
        return {"ok": True, "channel": ch.name, "permissions": perm_kwargs}

    return {"ok": False, "error": f"unknown op: {op}"}


async def process_admin_queue_loop() -> None:
    """Architect からの管理操作キューを 10 秒ごとに処理。
    bot/architect_admin_queue.py の submit_admin_op で提出されたファイルを拾って実行、結果を .result.json に書き出す。
    """
    import json as _json
    from .architect_admin_queue import ADMIN_QUEUE_DIR
    while True:
        try:
            await asyncio.sleep(10)
            if not _admin_queue_enabled():
                continue
            if not ADMIN_QUEUE_DIR.exists():
                continue
            for f in sorted(ADMIN_QUEUE_DIR.glob("admin_*.json")):
                if f.name.endswith(".result.json"):
                    continue
                try:
                    data = _json.loads(f.read_text(encoding="utf-8"))
                    op = data.get("op", "")
                    params = data.get("params", {})
                    log.info(f"admin_queue executing: {f.name} ({op})")
                    result = await execute_admin_op(op, params)
                    result_path = f.with_suffix(".result.json")
                    result_path.write_text(
                        _json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    if result.get("ok"):
                        f.unlink()
                        log.info(f"admin_queue ok: {f.name} -> {result}")
                    else:
                        log.warning(f"admin_queue failed: {f.name} -> {result}")
                except Exception:
                    log.exception(f"admin_queue error processing {f.name}")
        except Exception:
            log.exception("admin_queue loop error")
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

    # AutoMod 違反 → 自動 BAN リスナーをセットアップ（再エントリ安全のため一度のみ）
    try:
        from . import spam_auto_ban
        if not getattr(main_client, "_spam_auto_ban_ready", False):
            spam_auto_ban.setup(main_client)
            main_client._spam_auto_ban_ready = True
    except Exception:
        log.exception("spam_auto_ban setup failed")
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
    log.info("Daily scheduler started (08:05/08:30/12:00/18:00/18:15/21:30/03:00)")

    # 会社の鼓動: 5分間隔で沈黙チェック、10分沈黙したら誰か起こす（全体の非常用）
    from .heartbeat import make_heartbeat_scheduler
    hb_scheduler = make_heartbeat_scheduler(main_client)
    hb_scheduler.start()
    log.info("Heartbeat scheduler started (check=30min, idle_threshold=90min, daily_limit=4, 24h operation)")

    # 各社員の自律ループ: 起動前に should_wake_employee で安く判定し、必要時だけLLM実行
    from .employee_autonomy import start_all_autonomy_loops
    start_all_autonomy_loops(main_client)
    log.info("Employee autonomy loops started (9社員、wake判定付き、24h operation)")

    # 初回限定: いくと依頼チャンネル開設の通知（フラグファイルで1回保証）
    asyncio.create_task(notify_owner_channel_once())

    # Architect (Claude) からの投稿要求を処理するループ（dispatcher 動作中でも投稿可能に）
    asyncio.create_task(process_architect_outbox_loop())
    log.info("Architect outbox loop started (10秒間隔でファイル監視)")

    # Architect (Claude) からの管理操作キュー（チャンネル作成・招待・権限変更を停止なしで）
    asyncio.create_task(process_admin_queue_loop())
    if _admin_queue_enabled():
        log.info("Architect admin queue loop started (10秒間隔でファイル監視)")
    else:
        log.info("Architect admin queue loop started but disabled (AI_NOWA_ADMIN_QUEUE_ENABLED=1 or dynamic_config admin_queue.enabled=true required)")

    # 自己改善ループ: 1時間ごとに4指標計測 → 閾値超でトリガー発火
    from .self_improvement_loop import improvement_loop
    asyncio.create_task(improvement_loop())
    log.info("Self-improvement loop started (1時間ごと: 認知/収益/効率/品質 監視)")

    if _cfg_bool("release_pressure.enabled", True):
        from .release_board import release_pressure_loop
        asyncio.create_task(release_pressure_loop())
        log.info("Release pressure loop started (未出荷在庫/人間待ちを監視)")

    # 会話ログローテ: 10分間隔で 100KB 超のログをアーカイブ
    from .log_rotator import log_rotation_loop
    asyncio.create_task(log_rotation_loop())
    log.info("Log rotation loop started (10分間隔, 100KB 超で archive/conversation_log_*.jsonl)")

    # 軽量 watcher 群（基本は Python のみ、LLMを呼ばない。Architect observer は異常時だけ呼ぶ）
    if _cfg_bool("dashboard_writer.enabled", True):
        from .dashboard_writer import dashboard_loop
        asyncio.create_task(dashboard_loop())
        log.info("Dashboard writer loop started")

    if _cfg_bool("architect_observer.enabled", True):
        from .architect_observer import observer_loop
        asyncio.create_task(observer_loop())
        log.info("Architect observer loop started")

    if _cfg_bool("task_health.enabled", True):
        from .task_health_watcher import daily_scan_loop
        asyncio.create_task(daily_scan_loop())
        log.info("Task health watcher loop started")

    if _cfg_bool("external_check.enabled", True):
        from .external_check import scan_loop as external_scan_loop
        asyncio.create_task(external_scan_loop())
        log.info("External URL checker loop started")

    if _cfg_bool("dependency_visualizer.enabled", True):
        from .dependency_visualizer import visualizer_loop
        asyncio.create_task(visualizer_loop())
        log.info("Dependency visualizer loop started")

    if _cfg_bool("outbox_organizer.enabled", False):
        from .outbox_organizer import organizer_loop
        asyncio.create_task(organizer_loop())
        log.info("Outbox organizer loop started")

    if _cfg_bool("auto_commit.enabled", False):
        from .auto_commit import commit_loop
        asyncio.create_task(commit_loop())
        log.info("Auto commit loop started")

    # owner_request_watcher: blocked依頼の自動代行 + 24h未応答の自動deprecate
    from .owner_request_watcher import scan_and_post_loop, deprecate_scan_loop
    asyncio.create_task(scan_and_post_loop())
    asyncio.create_task(deprecate_scan_loop())
    log.info("owner_request_watcher loops started (blocked代行=1min, deprecate確認=1h)")


@main_client.event
async def on_message(message: discord.Message) -> None:
    # メイン bot 自身の投稿は無視
    if message.author == main_client.user:
        return

    # 社員 bot の投稿は連鎖を dispatcher 経由で再起動しない（暴走防止）
    # ただし @設計者 メンションがあれば Architect が自動応答する（リアルタイム反応）
    if message.author.id in multi_client.all_employee_user_ids():
        raw_content = message.content.strip()
        # 自分への mention があれば、Architect ロールも検出対象
        if _has_architect_mention(raw_content) or (
            main_client.user is not None and main_client.user in message.mentions
        ):
            channel_name = getattr(message.channel, "name", "dm")
            emp_id = multi_client.get_emp_for_user_id(message.author.id)
            sender_label = f"社員（{message.author.display_name}）"
            decision = should_auto_architect_respond(raw_content, emp_id)
            if not decision.allowed:
                _record_architect_auto_skip(decision.reason, sender_label, raw_content)
                log.info(
                    "Architect AUTO-RESPONSE skipped: reason=%s emp=%s channel=%s",
                    decision.reason,
                    emp_id,
                    channel_name,
                )
                try:
                    await message.add_reaction("👀")
                except Exception:
                    pass
            elif _can_architect_auto_respond():
                log.info(f"Architect AUTO-RESPONSE: {sender_label} in #{channel_name}")
                try:
                    async with message.channel.typing():
                        response = await run_architect(
                            raw_content,
                            sender=sender_label,
                            channel=channel_name,
                            mode="auto",
                            use_resume=False,
                        )
                    await send_chunked(message.channel, "", response)
                except Exception:
                    log.exception("Architect auto-response failed")
            else:
                _record_architect_auto_skip("architect_auto_rate_limited", sender_label, raw_content)
                log.warning(
                    f"Architect auto-response rate limited (skipping in #{getattr(message.channel, 'name', 'dm')})"
                )
        return

    # 他の bot は無視
    if message.author.bot:
        return

    # オーナー（いくと）以外の人間からのメンション → Claude CLI 起動を完全スキップ
    # なりすまし耐性: user_id(snowflake) ベース。ニックネーム改名・display 偽装には無効化される。
    _owner_id_str = os.environ.get("DISCORD_OWNER_USER_ID", "0") or "0"
    try:
        _owner_user_id = int(_owner_id_str)
    except ValueError:
        _owner_user_id = 0
    if _owner_user_id and message.author.id != _owner_user_id:
        from .mention_rate_limiter import should_react_to_observer
        if should_react_to_observer(str(message.author.id)):
            try:
                await message.add_reaction("👀")
            except Exception:
                pass
            log.info(
                f"OBSERVER mention ignored (no Claude CLI): author={message.author} "
                f"(id={message.author.id}) in #{getattr(message.channel, 'name', 'dm')}"
            )
        else:
            log.warning(
                f"OBSERVER reaction throttled (1分10超過、reactionも付けず): "
                f"author={message.author} (id={message.author.id})"
            )
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
            await message.channel.send(_safe_architect_failure_text(e))
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
            response = _safe_architect_failure_text(e)
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
    initial_cap = int(dynamic_config.get("mention_chain.max_initial_targets", 6))
    if len(targets) > initial_cap:
        deferred_count = len(targets) - initial_cap
        for deferred in targets[initial_cap:]:
            enqueue_deferred_mention(
                deferred,
                text=raw,
                sender=sender,
                channel=channel_name,
                chain_id=None,
                depth=0,
                reason=f"initial_target_limit:{initial_cap}",
            )
        targets = targets[:initial_cap]
        log.warning("initial targets clipped to %d; deferred=%d", initial_cap, deferred_count)

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
