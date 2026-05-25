"""voice_synth.py - 社員ごとの音声合成 + Whisper字幕

優先順位: Chatterbox (GPU/CPU) → VOICEVOX (ローカルAPI) → silent WAV fallback
"""
from __future__ import annotations

import json
import logging
import re
import struct
import time
import wave
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MEDIA_ROOT = Path(__file__).parent.parent / "shared" / "media"
VOICE_SAMPLES = MEDIA_ROOT / "voice_samples"
VOICE_SAMPLES.mkdir(parents=True, exist_ok=True)

# 社員ごとの音声パラメータ
EMPLOYEE_VOICES: dict[str, dict] = {
    "arima_reiji":  {"speed": 1.1, "voicevox_speaker": 3},   # ずんだもん（ノーマル）
    "saegusa_mio":  {"speed": 1.0, "voicevox_speaker": 2},   # 四国めたん（ノーマル）
    "shirase_kai":  {"speed": 1.05, "voicevox_speaker": 1},  # ずんだもん（あまあま）
    "asakura_noa":  {"speed": 0.95, "voicevox_speaker": 0},  # 四国めたん（あまあま）
    "hoshino_ritsu": {"speed": 1.0, "voicevox_speaker": 8},
    "kuroba_yuu":   {"speed": 1.1, "voicevox_speaker": 14},
    "kagura_aoi":   {"speed": 0.95, "voicevox_speaker": 10},
    "morinaga_haru": {"speed": 0.95, "voicevox_speaker": 4},
    "hinata_nagi":  {"speed": 1.0, "voicevox_speaker": 6},
}


# 読み上げ発音辞書（固有名詞・略語・社員名）。長いキーから順に置換する。
PRONUNCIATION_DICT: dict[str, str] = {
    "AI NOWA OS": "エーアイノワ オーエス",
    "AI NOWA": "エーアイノワ",
    "Claude Code": "クロードコード",
    "Claude": "クロード",
    "Discord": "ディスコード",
    "YouTube": "ユーチューブ",
    "Bluesky": "ブルースカイ",
    "Cloudflare": "クラウドフレア",
    "GA4": "ジーエーフォー",
    "Polar": "ポーラー",
    "CTO": "シーティーオー",
    "CEO": "シーイーオー",
    "COO": "シーオーオー",
    "PM": "ピーエム",
    "OS": "オーエス",
    "URL": "ユーアールエル",
    "AI": "エーアイ",
    "白瀬カイ": "しらせカイ",
    "有馬レイジ": "ありまレイジ",
    "三枝ミオ": "さえぐさミオ",
    "朝倉ノア": "あさくらノア",
    "星野リツ": "ほしのリツ",
    "黒羽ユウ": "くろばユウ",
    "神楽アオイ": "かぐらアオイ",
    "森永ハル": "もりながハル",
    "日向ナギ": "ひなたナギ",
}

_URL_RE = re.compile(r"https?://[^\s]+")


def normalize_text(text: str) -> str:
    """読み上げ用にテキストを正規化する。

    - URL は読み上げに不向きなので「リンク」へ置換
    - 固有名詞・英字略語・社員名を発音辞書でカタカナ/かな読みへ
    - 長いキーから順に置換し、部分一致の取りこぼし（AI NOWA より先に AI が当たる等）を防ぐ
    """
    text = _URL_RE.sub("、リンク、", text)
    for key in sorted(PRONUNCIATION_DICT, key=len, reverse=True):
        text = text.replace(key, PRONUNCIATION_DICT[key])
    return text


def _ref_audio(employee_id: str) -> Optional[Path]:
    ref = VOICE_SAMPLES / f"{employee_id}_ref.wav"
    return ref if ref.exists() else None


def _synthesize_chatterbox(text: str, employee_id: str, out: Path) -> bool:
    try:
        from chatterbox.tts import ChatterboxTTS  # type: ignore
        import torch
        import torchaudio

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = ChatterboxTTS.from_pretrained(device=device)
        ref = _ref_audio(employee_id)
        wav = model.generate(
            text=text,
            audio_prompt_path=str(ref) if ref else None,
            exaggeration=0.5,
            cfg_weight=0.5,
        )
        torchaudio.save(str(out), wav, model.sr)
        logger.info(f"chatterbox → {out}")
        return True
    except ImportError:
        logger.debug("chatterbox-tts not installed")
        return False
    except Exception as e:
        logger.warning(f"chatterbox failed: {e}")
        return False


def _synthesize_voicevox(
    text: str, employee_id: str, out: Path, base_url: str = "http://localhost:50021"
) -> bool:
    try:
        import requests  # type: ignore

        cfg = EMPLOYEE_VOICES.get(employee_id, {})
        speaker = cfg.get("voicevox_speaker", 0)
        speed = cfg.get("speed", 1.0)

        q = requests.post(
            f"{base_url}/audio_query",
            params={"text": text, "speaker": speaker},
            timeout=30,
        )
        q.raise_for_status()
        query = q.json()
        query["speedScale"] = speed

        r = requests.post(
            f"{base_url}/synthesis",
            params={"speaker": speaker},
            json=query,
            timeout=60,
        )
        r.raise_for_status()
        out.write_bytes(r.content)
        logger.info(f"voicevox → {out}")
        return True
    except ImportError:
        logger.debug("requests not available")
        return False
    except Exception as e:
        logger.debug(f"voicevox unavailable: {e}")
        return False


def _synthesize_gtts(text: str, out: Path) -> bool:
    try:
        import subprocess
        import tempfile
        from gtts import gTTS  # type: ignore

        tts = gTTS(text=text, lang="ja", slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        tts.save(str(tmp_path))
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp_path), "-ar", "22050", "-ac", "1", str(out)],
            capture_output=True, timeout=60,
        )
        tmp_path.unlink(missing_ok=True)
        if result.returncode == 0:
            logger.info(f"gtts → {out}")
            return True
        logger.warning(f"gtts ffmpeg conversion failed: {result.stderr.decode()[:200]}")
        return False
    except ImportError:
        logger.debug("gTTS not installed")
        return False
    except Exception as e:
        logger.warning(f"gtts failed: {e}")
        return False


def _write_silent_wav(path: Path, duration_s: float = 3.0, sr: int = 22050) -> None:
    n = int(duration_s * sr)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{n}h", *([0] * n)))


def _subtitles_whisper(audio_path: Path) -> list[dict]:
    try:
        import whisper  # type: ignore

        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), language="ja", word_timestamps=True)
        return [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in result.get("segments", [])
        ]
    except ImportError:
        logger.debug("openai-whisper not installed, skipping subtitles")
        return []
    except Exception as e:
        logger.warning(f"whisper error: {e}")
        return []


def synthesize(
    text: str,
    employee_id: str,
    output_path: Optional[Path] = None,
    with_subtitles: bool = True,
) -> dict:
    """
    テキストを音声に変換。

    Returns:
        {
            "audio": Path,
            "subtitles": [{"start": float, "end": float, "text": str}, ...],
            "engine": "chatterbox" | "voicevox" | "silent",
        }
    """
    text = normalize_text(text)
    if output_path is None:
        ts = int(time.time())
        output_path = VOICE_SAMPLES / f"{employee_id}_{ts}.wav"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if _synthesize_chatterbox(text, employee_id, output_path):
        engine = "chatterbox"
    elif _synthesize_voicevox(text, employee_id, output_path):
        engine = "voicevox"
    elif _synthesize_gtts(text, output_path):
        engine = "gtts"
    else:
        logger.warning(f"all TTS engines failed for {employee_id}, writing silent wav")
        _write_silent_wav(output_path)
        engine = "silent"

    subtitles: list[dict] = []
    if with_subtitles and engine != "silent":
        subtitles = _subtitles_whisper(output_path)

    return {"audio": output_path, "subtitles": subtitles, "engine": engine}


def main() -> None:
    import sys

    logging.basicConfig(level=logging.INFO)
    text = sys.argv[1] if len(sys.argv) > 1 else "こんにちは。AI NOWAのCTO、白瀬カイです。"
    employee = sys.argv[2] if len(sys.argv) > 2 else "shirase_kai"
    result = synthesize(text, employee)
    print(json.dumps(
        {"audio": str(result["audio"]), "engine": result["engine"], "subtitles": result["subtitles"][:3]},
        ensure_ascii=False, indent=2,
    ))


if __name__ == "__main__":
    main()
