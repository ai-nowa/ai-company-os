"""9社員 bot client の起動・管理（Phase 2.7 マルチクライアント版）。

メイン dispatcher は AI NOWA bot として動き、メンション解析・連鎖管理を担当。
各社員 client は「その社員として投稿する」代理として使う。

起動フロー:
  1. メイン dispatcher が on_ready 時に start_all() を呼ぶ
  2. 各 BOT_TOKEN_{EMP_ID} 環境変数から token を読んで client.start() を非同期実行
  3. 全 client の wait_until_ready() を待つ
  4. user_id -> emp_id の逆引きマップを構築
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import discord

from .config import EMPLOYEES

log = logging.getLogger("multi_client")

# 起動した社員 client（emp_id -> client）
_clients: dict[str, discord.Client] = {}
# bot user_id -> emp_id 逆引き（user mention 解決用）
_user_id_to_emp: dict[int, str] = {}
# managed role_id -> emp_id 逆引き（Discord の bot 招待時に自動生成されるマネージドロール用）
_role_id_to_emp: dict[int, str] = {}


def get_clients() -> dict[str, discord.Client]:
    return dict(_clients)


def get_client(emp_id: str) -> Optional[discord.Client]:
    return _clients.get(emp_id)


def get_emp_for_user_id(user_id: int) -> Optional[str]:
    return _user_id_to_emp.get(user_id)


def get_emp_for_role_id(role_id: int) -> Optional[str]:
    return _role_id_to_emp.get(role_id)


def get_role_id_for_emp(emp_id: str) -> Optional[int]:
    """社員IDから対応する Discord マネージドロール ID（投稿時の本物メンション変換用）"""
    for role_id, eid in _role_id_to_emp.items():
        if eid == emp_id:
            return role_id
    return None


def all_employee_user_ids() -> set[int]:
    return set(_user_id_to_emp.keys())


def all_employee_role_ids() -> set[int]:
    return set(_role_id_to_emp.keys())


async def build_role_map_from(main_client: discord.Client) -> dict[str, list[str]]:
    """メイン client から全 guild の bot-managed ロールを scan し、社員 ID と紐付ける"""
    result: dict[str, list[str]] = {}
    for guild in main_client.guilds:
        for role in guild.roles:
            tags = getattr(role, "tags", None)
            if tags is None:
                continue
            bot_id = getattr(tags, "bot_id", None)
            if bot_id is None:
                continue
            emp_id = _user_id_to_emp.get(bot_id)
            if emp_id:
                _role_id_to_emp[role.id] = emp_id
                result.setdefault(emp_id, []).append(f"{role.name}#{role.id}")
    return result


def get_channel_for_employee(emp_id: str, channel_id: int) -> Optional[discord.abc.Messageable]:
    """指定社員 client から、指定 channel_id のチャンネル取得"""
    client = _clients.get(emp_id)
    if not client:
        return None
    return client.get_channel(channel_id)


async def start_all(intents: discord.Intents, ready_timeout: float = 30.0) -> dict[str, str]:
    """全社員 client を非同期で起動。
    Returns: emp_id -> ステータス
    """
    status: dict[str, str] = {}
    pending: list[tuple[str, discord.Client]] = []

    for emp_id in EMPLOYEES.keys():
        token = os.environ.get(f"BOT_TOKEN_{emp_id.upper()}")
        if not token:
            status[emp_id] = "no_token"
            continue
        client = discord.Client(intents=intents)
        _clients[emp_id] = client
        # 起動を非同期 task として開始（completing しない、常駐）
        asyncio.create_task(client.start(token))
        pending.append((emp_id, client))

    for emp_id, client in pending:
        try:
            await asyncio.wait_for(client.wait_until_ready(), timeout=ready_timeout)
            if client.user:
                _user_id_to_emp[client.user.id] = emp_id
                status[emp_id] = f"ready ({client.user})"
                log.info(f"Employee client ready: {emp_id} = {client.user} ({client.user.id})")
            else:
                status[emp_id] = "ready_no_user"
        except asyncio.TimeoutError:
            status[emp_id] = "timeout"
            log.warning(f"Employee client timeout: {emp_id}")
        except Exception as e:
            status[emp_id] = f"error: {type(e).__name__}"
            log.exception(f"Employee client error: {emp_id}")

    return status


async def stop_all() -> None:
    for emp_id, client in list(_clients.items()):
        try:
            await client.close()
        except Exception:
            log.exception(f"Close failed: {emp_id}")
    _clients.clear()
    _user_id_to_emp.clear()


async def send_as_employee(emp_id: str, channel_id: int, content: str) -> bool:
    """指定社員 bot として channel に投稿。成功すれば True"""
    ch = get_channel_for_employee(emp_id, channel_id)
    if ch is None:
        log.warning(f"Channel {channel_id} not visible to {emp_id}")
        return False
    if not content:
        content = "(空応答)"
    chunks = [content[i:i + 1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        await ch.send(chunk)
    return True


async def find_channel_for_employee(emp_id: str, needle: str) -> Optional[discord.abc.Messageable]:
    """指定社員 client の view から、名前マッチするチャンネルを探す"""
    client = _clients.get(emp_id)
    if not client:
        return None
    for guild in client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None
