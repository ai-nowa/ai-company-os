"""三角コミュニケーション制御。
重要意思決定の検知、トライアド構成メンバー取得、衝突時の仲介者検索。
Phase 2 ではキーワード検知ベースのスタブ。
"""
from __future__ import annotations

from typing import Optional

import yaml

from .config import RELATIONSHIPS_DIR

_triads_cache: Optional[dict] = None
_relations_cache: Optional[dict] = None


def _load_triads() -> dict:
    global _triads_cache
    if _triads_cache is None:
        path = RELATIONSHIPS_DIR / "triads.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        _triads_cache = data.get("triads", {})
    return _triads_cache


def _load_relations() -> dict:
    global _relations_cache
    if _relations_cache is None:
        path = RELATIONSHIPS_DIR / "relationship_graph.yaml"
        _relations_cache = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _relations_cache


DECISION_KEYWORDS = [
    "[decision]", "意思決定", "公開可否", "リリース", "公開する",
    "P0", "正式版", "本番投入", "決めたい", "GoかNoGo",
]

DOMAIN_HINTS = {
    "youtube":  ["動画", "YouTube", "サムネ", "タイトル", "Shorts", "台本", "編集"],
    "product":  ["実装", "技術", "リファクタ", "デプロイ", "API", "バグ", "監査", "リスク", "公開"],
    "business": ["方針", "優先順位", "ロードマップ", "MVP", "リソース"],
    "culture":  ["空気", "ふりかえり", "心理的安全性", "雑談", "孤立"],
}


def detect_decision_signal(text: str) -> Optional[str]:
    """メッセージから意思決定の必要性とトライアド領域を検知"""
    lower = text.lower()
    if not any(kw.lower() in lower for kw in DECISION_KEYWORDS):
        return None
    for triad, hints in DOMAIN_HINTS.items():
        if any(h in text for h in hints):
            return triad
    return "business"  # 領域不明なら事業判断トライアド


def get_triad_members(triad_name: str) -> list[str]:
    triads = _load_triads()
    return triads.get(triad_name, {}).get("members", [])


def get_triad_chair(triad_name: str) -> Optional[str]:
    triads = _load_triads()
    return triads.get(triad_name, {}).get("chair")


def find_conflict_mediator(from_id: str, to_id: str) -> Optional[str]:
    rels = _load_relations()
    target = {from_id, to_id}
    for entry in rels.get("conflict_routing", []):
        if set(entry.get("pair", [])) == target:
            return entry.get("mediator")
    return None


def describe_triad(triad_name: str) -> str:
    triads = _load_triads()
    t = triads.get(triad_name, {})
    members = t.get("members", [])
    role = t.get("role", [])
    return f"トライアド「{t.get('name', triad_name)}」(chair: {t.get('chair')}, members: {', '.join(members)}, 役割: {' / '.join(role)})"
