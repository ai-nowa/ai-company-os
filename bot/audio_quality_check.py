"""audio_quality_check.py — task#94 二次ゲート（mp4音響実測）。

無音・低品質音声の動画が public 公開される事故を防ぐ。
youtube_audio_quality_policy.md の二次ゲート基準を実測し、PASS/FAIL を返す。

public昇格パスへの強制配線（saegusa_mio 契約案 2026-05-25）:
  - analyze(mp4) で実測 → record(video_id, mp4, result) で PASS/FAIL を永続化
  - youtube_upload.set_privacy(..., "public") は is_passed(video_id) が真でなければ拒否
  - これで「誤爆・手動ミス・履歴漏れ」の3種をまとめて塞ぐ

CLI:
    python -m bot.audio_quality_check --video path/to.mp4
    python -m bot.audio_quality_check --video path/to.mp4 --video-id VIDEO_ID --record
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

JST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_PATH = BASE_DIR / "company" / "audio_gate_results.jsonl"

# task#94 二次ゲート閾値（16bit PCM 換算 / 冒頭末尾 0.5s 除外）
RMS_SILENT_DB = -45.0   # これ未満 = 実質無音 → FAIL
RMS_FLOOR_DB = -35.0    # これ未満 = 小さすぎ → FAIL
RMS_OK_LO_DB = -30.0    # 適正下限（外れると WARN）
RMS_OK_HI_DB = -9.0     # 適正上限（外れると WARN）
SILENCE_RATIO_MAX = 0.40  # RMS<-50dBFS 相当の無音割合がこれ超で FAIL
CLIP_PEAK_DB = -0.1     # peak がこれ以上 = クリッピング懸念 → FAIL


def _stderr(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True).stderr


def _duration(mp4: Path) -> float:
    info = _stderr(["ffmpeg", "-hide_banner", "-i", str(mp4)])
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info)
    if not m:
        return 0.0
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


def _has_audio(mp4: Path) -> bool:
    return "Audio:" in _stderr(["ffmpeg", "-hide_banner", "-i", str(mp4)])


def analyze(mp4: Path) -> dict[str, Any]:
    """mp4 の音声を実測し PASS/FAIL を判定する。"""
    mp4 = Path(mp4)
    if not mp4.exists():
        return {"passed": False, "warn": False, "reasons": [f"file_not_found:{mp4}"], "metrics": {}}
    if not _has_audio(mp4):
        return {"passed": False, "warn": False, "reasons": ["no_audio_stream"], "metrics": {}}

    dur = _duration(mp4)
    end = max(0.6, dur - 0.5)
    trim = f"atrim=start=0.5:end={end:.2f}"

    vd = _stderr(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", f"{trim},volumedetect", "-f", "null", "/dev/null"])
    rms_m = re.search(r"mean_volume:\s*(-?\d+\.?\d*)", vd)
    peak_m = re.search(r"max_volume:\s*(-?\d+\.?\d*)", vd)
    rms = float(rms_m.group(1)) if rms_m else -99.0
    peak = float(peak_m.group(1)) if peak_m else -99.0

    sd = _stderr(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af",
                  f"{trim},silencedetect=noise=-50dB:d=0.1", "-f", "null", "/dev/null"])
    silence_total = sum(float(x) for x in re.findall(r"silence_duration:\s*(\d+\.?\d*)", sd))
    measured = max(0.1, end - 0.5)
    silence_ratio = min(1.0, silence_total / measured)

    reasons: list[str] = []
    if rms < RMS_SILENT_DB:
        reasons.append(f"silent(rms={rms:.1f}dB<{RMS_SILENT_DB})")
    elif rms < RMS_FLOOR_DB:
        reasons.append(f"too_quiet(rms={rms:.1f}dB<{RMS_FLOOR_DB})")
    if silence_ratio > SILENCE_RATIO_MAX:
        reasons.append(f"silence_ratio({silence_ratio:.2f}>{SILENCE_RATIO_MAX})")
    if peak >= CLIP_PEAK_DB:
        reasons.append(f"clipping(peak={peak:.1f}dB)")

    warn = not (RMS_OK_LO_DB <= rms <= RMS_OK_HI_DB)
    return {
        "passed": len(reasons) == 0,
        "warn": warn,
        "reasons": reasons,
        "metrics": {
            "rms_db": round(rms, 1),
            "peak_db": round(peak, 1),
            "silence_ratio": round(silence_ratio, 3),
            "duration_s": round(dur, 1),
        },
    }


def record(video_id: str, mp4: Path, result: dict[str, Any]) -> dict[str, Any]:
    """PASS/FAIL を audio_gate_results.jsonl へ追記（video_id 紐付け・追記式で最新が有効）。"""
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(JST).isoformat(),
        "video_id": video_id,
        "source": str(mp4),
        "passed": bool(result.get("passed")),
        "warn": bool(result.get("warn")),
        "reasons": result.get("reasons", []),
        "metrics": result.get("metrics", {}),
    }
    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def is_passed(video_id: str) -> bool:
    """当該 video_id の最新 audio ゲート記録が PASS かどうか。記録が無ければ False。"""
    if not video_id or not RESULTS_PATH.exists():
        return False
    passed = False
    found = False
    for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("video_id") == video_id:
            passed = bool(e.get("passed"))
            found = True
    return found and passed


def main() -> None:
    p = argparse.ArgumentParser(description="task#94 音声品質ゲート（mp4音響実測）")
    p.add_argument("--video", type=Path, required=True, help="検査する mp4")
    p.add_argument("--video-id", help="PASS記録を紐付ける YouTube video_id")
    p.add_argument("--record", action="store_true", help="結果を audio_gate_results.jsonl へ記録")
    args = p.parse_args()

    result = analyze(args.video)
    verdict = "PASS" if result["passed"] else "FAIL"
    warn = " (WARN: 適正音量域外)" if result["passed"] and result["warn"] else ""
    print(f"{verdict}{warn} {result['metrics']}")
    if result["reasons"]:
        print("reasons: " + ", ".join(result["reasons"]))

    if args.record:
        if not args.video_id:
            p.error("--record には --video-id が必須です")
        entry = record(args.video_id, args.video, result)
        print(f"recorded -> {RESULTS_PATH} (video_id={entry['video_id']} passed={entry['passed']})")


if __name__ == "__main__":
    main()
