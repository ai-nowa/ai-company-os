"""メンション抽出 + 連鎖制御。

応答テキストから @表示名・名前・英語IDを抽出し、次の社員を呼び出すための ID リストを返す。
並列メンションは1深さ。連鎖深さ100で安全弁。
メタタグ部分（<!-- META: ... -->）は抽出前に除去する。
"""
from __future__ import annotations

import re
from typing import Optional

from .config import EMPLOYEES

MAX_DEPTH = 30  # 安全弁（usage 暴走防止）。通常はメンションが尽きて自然終了

META_RE = re.compile(r"<!--\s*META:\s*([^>]+?)\s*-->", re.DOTALL | re.IGNORECASE)


def strip_meta_tag(text: str) -> str:
    """応答からメタタグを除去（Discord 投稿用）"""
    return META_RE.sub("", text).strip()


def extract_meta_tag(text: str) -> Optional[str]:
    """応答からメタタグ本体（key=value, ... 部分）を抽出"""
    m = META_RE.search(text)
    return m.group(1) if m else None


def parse_meta_tag(raw: str) -> dict:
    """key1="v1", key2=true, key3="a, b" を {key: value} に変換"""
    result: dict = {}
    # key="..." / key=true / key=false / key=val
    pattern = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|(\[[^\]]*\])|(true|false)|([^,\s]+))')
    for m in pattern.finditer(raw):
        key = m.group(1)
        if m.group(2) is not None:
            value: object = m.group(2)
        elif m.group(3) is not None:
            inner = m.group(3).strip("[]")
            value = [v.strip().strip('"') for v in inner.split(",") if v.strip()]
        elif m.group(4) is not None:
            value = m.group(4).lower() == "true"
        else:
            value = m.group(5)
        result[key] = value
    # invite が文字列なら配列化（カンマ区切り）
    if "invite" in result and isinstance(result["invite"], str):
        result["invite"] = [s.strip() for s in result["invite"].split(",") if s.strip()]
    return result


def _split_display(display: str) -> tuple[str, str]:
    """display を (family, given) に分割。'有馬レイジ' → ('有馬', 'レイジ')"""
    for sep in ["・", " ", "　"]:
        if sep in display:
            parts = display.split(sep, 1)
            return parts[0], parts[1]
    m = re.match(r"^([一-鿿々ヶ]+)(.+)$", display)
    if m:
        return m.group(1), m.group(2)
    return display, display


def _candidate_patterns(employee_id: str) -> list[str]:
    """検出に使う `@プレフィックス必須` のパターン群。
    これは社員に「呼びたければ @ を付ける」文化を強制するための設計。
    自然な日本語の呼びかけ（『ミオさん、』『カイに任せる』）は意図的に拾わない。
    """
    info = EMPLOYEES.get(employee_id, {})
    display = info.get("display", "")
    family, given = _split_display(display)
    patterns: list[str] = []
    # 英語ID
    patterns.append(f"@{employee_id}")
    # フルネーム
    if display:
        patterns.append(f"@{display}")
    # 名・名字（2文字以上）
    for token in {given, family}:
        if token and len(token) >= 2:
            patterns.append(f"@{token}")
    return patterns


def extract_mentions(text: str, exclude: Optional[set[str]] = None) -> list[str]:
    """応答テキストから、次に呼ぶべき社員IDのリストを返す（重複排除、出現順保持）。

    検出対象:
    - `@<英語ID>` / `@<フルネーム>` / `@<名>` / `@<名字>` のテキスト記述
    - `<@user_id>` Discord ユーザーメンション (bot)
    - `<@&role_id>` Discord ロールメンション (bot-managed role)

    自然な日本語呼びかけ（「ミオさん」「カイに」）は **意図的に検出しない**。
    """
    exclude = exclude or set()
    text_clean = strip_meta_tag(text)

    # multi_client 側のマップを参照（循環 import 回避のため遅延 import）
    from . import multi_client

    found_positions: dict[str, int] = {}

    # 1. Discord user mention <@user_id> または <@!user_id>
    for m in re.finditer(r"<@!?(\d+)>", text_clean):
        try:
            user_id = int(m.group(1))
        except ValueError:
            continue
        emp_id = multi_client.get_emp_for_user_id(user_id)
        if emp_id and emp_id not in exclude and emp_id not in found_positions:
            found_positions[emp_id] = m.start()

    # 2. Discord role mention <@&role_id>
    for m in re.finditer(r"<@&(\d+)>", text_clean):
        try:
            role_id = int(m.group(1))
        except ValueError:
            continue
        emp_id = multi_client.get_emp_for_role_id(role_id)
        if emp_id and emp_id not in exclude and emp_id not in found_positions:
            found_positions[emp_id] = m.start()

    # 2. テキスト @ プレフィックス
    for emp_id in EMPLOYEES.keys():
        if emp_id in exclude or emp_id in found_positions:
            continue
        best_pos = -1
        for pat in _candidate_patterns(emp_id):
            idx = text_clean.find(pat)
            if idx >= 0 and (best_pos < 0 or idx < best_pos):
                best_pos = idx
        if best_pos >= 0:
            found_positions[emp_id] = best_pos

    return [eid for eid, _ in sorted(found_positions.items(), key=lambda x: x[1])]


# テスト用
if __name__ == "__main__":
    samples = [
        ("ミオさん、ノアさん、よろしく", []),  # @ なし → 検出しない
        ("白瀬カイに任せます", []),  # @ なし → 検出しない
        ("@有馬レイジ よろしく", ["arima_reiji"]),
        ("@ミオ @ノア @カイ 議論しよう", ["saegusa_mio", "asakura_noa", "shirase_kai"]),
        ("@arima_reiji 承認お願い", ["arima_reiji"]),
        ("全員でアイデア出してください。@三枝ミオ @朝倉ノア @神楽アオイ",
         ["saegusa_mio", "asakura_noa", "kagura_aoi"]),
        ("誰もメンションしない普通の応答", []),
        ("レイジさんに任せます", []),  # @ なし → 検出しない
    ]
    ok = 0
    for text, expected in samples:
        got = extract_mentions(text)
        status = "✓" if got == expected else "✗"
        print(f"{status} {text!r}")
        print(f"  expected: {expected}")
        print(f"  got:      {got}")
        if got == expected:
            ok += 1
    print(f"\n{ok}/{len(samples)} pass")
