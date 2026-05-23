"""video_render.py - 画像 + 音声 + 字幕 → MP4 (Phase 1 / Day 3)

moviepy v1 で結合 → 音ズレ検知 → ffmpeg-python フォールバック。
依存: moviepy>=1.0.3, ffmpeg-python, imageio[ffmpeg], Pillow

CLI:
    python -m bot.video_render --script path/to/script.json [--video-id test_001]
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MEDIA_ROOT = Path(__file__).parent.parent / "shared" / "media"
VIDEO_OUT = MEDIA_ROOT / "videos"


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

_FFPROBE_CANDIDATES = [
    "/home/ikuto/miniconda/envs/train1b/bin/ffprobe",
    "/home/ikuto/miniconda/bin/ffprobe",
]


def _ffprobe_bin() -> str:
    """ffprobe バイナリのパスを返す。見つからなければ RuntimeError。"""
    if p := shutil.which("ffprobe"):
        return p
    ffmpeg = shutil.which("ffmpeg") or "/home/ikuto/.local/bin/ffmpeg"
    sibling = Path(ffmpeg).parent / "ffprobe"
    if sibling.exists():
        return str(sibling)
    for candidate in _FFPROBE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("ffprobe not found — install ffmpeg or add to PATH")


def _make_blank_image(width: int = 1280, height: int = 720, out: Optional[Path] = None) -> Path:
    from PIL import Image

    img = Image.new("RGB", (width, height), (0, 0, 0))
    if out is None:
        out = MEDIA_ROOT / "tmp_blank.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out))
    return out


def _make_silent_wav(duration_s: float = 3.0, out: Optional[Path] = None) -> Path:
    """無音WAVを生成する (48kHz stereo)。"""
    if out is None:
        out = MEDIA_ROOT / "tmp_silent.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sr = 48000
    channels = 2
    n = int(duration_s * sr)
    with wave.open(str(out), "w") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(2 * channels * n))
    return out


def _audio_duration_ffprobe(audio_path: Path) -> float:
    """ffprobe で音声長を取得。失敗時は 3.0 を返す。"""
    try:
        result = subprocess.run(
            [_ffprobe_bin(), "-v", "quiet", "-print_format", "json", "-show_streams", str(audio_path)],
            capture_output=True, text=True, timeout=30,
        )
        info = json.loads(result.stdout)
        for s in info.get("streams", []):
            if "duration" in s:
                return float(s["duration"])
    except Exception as e:
        logger.debug(f"ffprobe duration failed: {e}")
    return 3.0


def _detect_av_sync_error(path: Path, tolerance_s: float = 0.1) -> bool:
    """ffprobe で映像/音声の duration 差を検知。"""
    try:
        result = subprocess.run(
            [_ffprobe_bin(), "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        info = json.loads(result.stdout)
        durations = [
            float(s["duration"])
            for s in info.get("streams", [])
            if "duration" in s
        ]
        if len(durations) >= 2:
            diff = abs(durations[0] - durations[1])
            if diff > tolerance_s:
                logger.warning(f"AV sync gap {diff:.3f}s > {tolerance_s}s — fallback triggered")
                return True
    except Exception as e:
        logger.debug(f"AV sync check skipped: {e}")
    return False


# ---------------------------------------------------------------------------
# ffprobe QA チェッカー
# ---------------------------------------------------------------------------

QA_REQUIRED_PIX_FMT = "yuv420p"
QA_MIN_TOTAL_BITRATE_KBPS = 200  # 合計(映像+音声)。静止画ベース動画は映像bitが低くても合計で判定
QA_MIN_AUDIO_SAMPLE_RATE = 44100
QA_MIN_AUDIO_CHANNELS = 2


def _parse_ffmpeg_stderr(stderr: str) -> dict:
    """ffmpeg -i stderr から video/audio ストリーム情報をパースして返す。
    Stream行の形式: "Stream #0:N[...](lang): Video: codec, pix_fmt, WxH, BR kb/s"
    """
    import re
    info: dict = {"video": {}, "audio": {}}

    # Duration行から全体ビットレート: "bitrate: 96 kb/s"
    m = re.search(r"bitrate:\s*(\d+)\s*kb/s", stderr)
    if m:
        info["total_bitrate_kbps"] = int(m.group(1))

    # Video pix_fmt: "Video: <codec>, <pix_fmt>" — codecの後の最初のカンマ+値
    # 例: "Video: h264 (High 4:4:4 Predictive) (avc1 / 0x31637661), yuv444p(progressive)"
    m = re.search(r"Video:[^,]+,\s*(\w+)", stderr)
    if m:
        info["video"]["pix_fmt"] = m.group(1)

    # Video bitrate: "WxH, 19 kb/s" — 解像度の後のビットレート
    # 例: "yuv444p(progressive), 1280x720, 19 kb/s"
    m = re.search(r"\d+x\d+[^,]*,\s*(\d+)\s*kb/s", stderr)
    if m:
        info["video"]["bitrate_kbps"] = int(m.group(1))

    # Audio sample_rate: "Audio: codec, 22050 Hz"
    m = re.search(r"Audio:[^,]+,\s*(\d+)\s*Hz", stderr)
    if m:
        info["audio"]["sample_rate"] = int(m.group(1))

    # Audio channels: "22050 Hz, stereo/mono"
    m = re.search(r"\d+\s*Hz,\s*(\w+)", stderr)
    if m:
        ch_str = m.group(1)
        if ch_str == "stereo":
            info["audio"]["channels"] = 2
        elif ch_str == "mono":
            info["audio"]["channels"] = 1
        else:
            try:
                info["audio"]["channels"] = int(ch_str)
            except ValueError:
                info["audio"]["channels"] = 0

    return info


def _probe_quality_info(path: Path) -> dict:
    """ffprobe JSON から QA 用の stream 情報を取得。失敗時は ffmpeg stderr にフォールバック。"""
    try:
        result = subprocess.run(
            [
                _ffprobe_bin(),
                "-v", "error",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = json.loads(result.stdout)
            info: dict = {"video": {}, "audio": {}}
            fmt = raw.get("format", {})
            bit_rate = fmt.get("bit_rate")
            if bit_rate and str(bit_rate).isdigit():
                info["total_bitrate_kbps"] = int(int(bit_rate) / 1000)
            for stream in raw.get("streams", []):
                codec_type = stream.get("codec_type")
                if codec_type == "video" and not info["video"]:
                    if stream.get("pix_fmt"):
                        info["video"]["pix_fmt"] = stream["pix_fmt"]
                    br = stream.get("bit_rate")
                    if br and str(br).isdigit():
                        info["video"]["bitrate_kbps"] = int(int(br) / 1000)
                elif codec_type == "audio" and not info["audio"]:
                    sr = stream.get("sample_rate")
                    if sr and str(sr).isdigit():
                        info["audio"]["sample_rate"] = int(sr)
                    channels = stream.get("channels")
                    if isinstance(channels, int):
                        info["audio"]["channels"] = channels
            return info
    except Exception as e:
        logger.debug(f"ffprobe quality info failed, fallback to ffmpeg stderr: {e}")

    ffmpeg_bin = shutil.which("ffmpeg") or "/home/ikuto/.local/bin/ffmpeg"
    result = subprocess.run(
        [ffmpeg_bin, "-hide_banner", "-i", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    if not result.stderr.strip():
        raise RuntimeError(f"media probe failed: no output for {path.name}")
    return _parse_ffmpeg_stderr(result.stderr)


def check_quality(path: Path) -> None:
    """出力動画の品質を検証。基準未達なら RuntimeError を上げる（投稿ブロック）。
    ffprobe が使えない環境では ffmpeg -i の stderr フォールバックで検証する。
    """
    info = _probe_quality_info(path)
    errors: list[str] = []

    # video チェック
    if not info["video"]:
        errors.append("no video stream detected")
    else:
        pix_fmt = info["video"].get("pix_fmt", "")
        if pix_fmt != QA_REQUIRED_PIX_FMT:
            errors.append(f"pix_fmt={pix_fmt!r}, expected {QA_REQUIRED_PIX_FMT!r}")

    # 合計ビットレートチェック（静止画ベース動画は映像bitrateが低いため合計で判定）
    total_br = info.get("total_bitrate_kbps")
    if total_br is not None and total_br < QA_MIN_TOTAL_BITRATE_KBPS:
        errors.append(f"total bitrate={total_br}kbps < {QA_MIN_TOTAL_BITRATE_KBPS}kbps")

    # audio チェック
    if not info["audio"]:
        errors.append("no audio stream detected")
    else:
        sr = info["audio"].get("sample_rate", 0)
        if sr < QA_MIN_AUDIO_SAMPLE_RATE:
            errors.append(f"audio sample_rate={sr}Hz < {QA_MIN_AUDIO_SAMPLE_RATE}Hz")

        channels = info["audio"].get("channels", 0)
        if channels < QA_MIN_AUDIO_CHANNELS:
            errors.append(f"audio channels={channels} < {QA_MIN_AUDIO_CHANNELS} (stereo required)")

    if errors:
        raise RuntimeError(
            f"Quality check FAILED for {path.name}: " + " | ".join(errors)
        )

    logger.info("Quality check passed: %s", path.name)


# ---------------------------------------------------------------------------
# moviepy バックエンド (v1: from moviepy.editor import ...)
# ---------------------------------------------------------------------------

def _make_subtitle_clips(subtitles: list[dict], width: int, max_duration: float) -> list:
    """TextClip で字幕クリップ列を生成。ImageMagick 不在時は空リストを返す。"""
    try:
        from moviepy.editor import TextClip  # type: ignore

        clips = []
        for seg in subtitles:
            text = seg.get("text", "").strip()
            start = float(seg.get("start", 0))
            end = min(float(seg.get("end", max_duration)), max_duration)
            if not text or start >= end:
                continue
            txt = (
                TextClip(
                    text,
                    fontsize=28,
                    color="white",
                    bg_color="black",
                    method="caption",
                    size=(width - 40, None),
                )
                .set_start(start)
                .set_end(end)
                .set_pos(("center", "bottom"))
            )
            clips.append(txt)
        return clips
    except Exception as e:
        logger.debug(f"subtitle clips skipped (ImageMagick unavailable?): {e}")
        return []


def _render_moviepy(script: list[dict], out: Path) -> bool:
    """moviepy v1 で複数クリップを結合して MP4 出力。"""
    try:
        from moviepy.editor import (  # type: ignore
            AudioFileClip, CompositeVideoClip, ImageClip,
            concatenate_videoclips,
        )
    except ImportError:
        logger.warning("moviepy not installed")
        return False

    tmp_files: list[Path] = []
    clips: list = []

    try:
        for i, item in enumerate(script):
            image_path = Path(item.get("image_path", ""))
            audio_result = item.get("audio_result", {})
            audio_path = Path(str(audio_result.get("audio", "")))
            subtitles: list[dict] = audio_result.get("subtitles", [])

            if not image_path.exists():
                logger.warning(f"image not found: {image_path} — using blank")
                tmp_img = MEDIA_ROOT / f"tmp_blank_{i}.png"
                image_path = _make_blank_image(out=tmp_img)
                tmp_files.append(tmp_img)

            if audio_path.exists():
                audio_clip: Optional[AudioFileClip] = AudioFileClip(str(audio_path))
                duration = audio_clip.duration
            else:
                logger.warning(f"audio not found: {audio_path} — using silent wav")
                tmp_wav = MEDIA_ROOT / f"tmp_silent_{i}.wav"
                tmp_files.append(tmp_wav)
                audio_path = _make_silent_wav(out=tmp_wav)
                audio_clip = AudioFileClip(str(audio_path))
                duration = audio_clip.duration

            video_clip = ImageClip(str(image_path)).set_duration(duration)
            video_clip = video_clip.set_audio(audio_clip)

            sub_clips = _make_subtitle_clips(subtitles, video_clip.w, duration)
            if sub_clips:
                video_clip = CompositeVideoClip([video_clip] + sub_clips)

            clips.append(video_clip)

        if not clips:
            logger.error("no valid clips to render")
            return False

        final = concatenate_videoclips(clips, method="compose")
        out.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(
            str(out),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            bitrate="2000k",
            audio_fps=48000,
            ffmpeg_params=[
                "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-level", "4.0",
                "-ac", "2",
                "-movflags", "+faststart",
            ],
            temp_audiofile=str(out.with_suffix(".tmp.aac")),
            remove_temp=True,
            logger=None,
        )
        return True

    except Exception as e:
        logger.error(f"moviepy render failed: {e}")
        return False
    finally:
        for f in tmp_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# ffmpeg-python バックエンド（フォールバック）
# ---------------------------------------------------------------------------

def _render_ffmpeg(script: list[dict], out: Path) -> bool:
    """ffmpeg-python で直接結合（moviepy フォールバック）。"""
    try:
        import ffmpeg  # type: ignore
    except ImportError:
        logger.warning("ffmpeg-python not installed")
        return False

    out.parent.mkdir(parents=True, exist_ok=True)
    video_inputs: list = []
    audio_inputs: list = []
    tmp_files: list[Path] = []

    try:
        for i, item in enumerate(script):
            image_path = Path(item.get("image_path", ""))
            audio_result = item.get("audio_result", {})
            audio_path = Path(str(audio_result.get("audio", "")))

            if not image_path.exists():
                logger.warning(f"image not found: {image_path} — using blank")
                tmp_img = MEDIA_ROOT / f"tmp_blank_{i}.png"
                image_path = _make_blank_image(out=tmp_img)
                tmp_files.append(tmp_img)

            if not audio_path.exists():
                logger.warning(f"audio not found: {audio_path} — using silent wav")
                tmp_wav = MEDIA_ROOT / f"tmp_silent_{i}.wav"
                audio_path = _make_silent_wav(out=tmp_wav)
                tmp_files.append(tmp_wav)

            duration = _audio_duration_ffprobe(audio_path)
            video_inputs.append(
                ffmpeg.input(str(image_path), loop=1, t=duration, framerate=24)
            )
            audio_inputs.append(ffmpeg.input(str(audio_path)))

        if not video_inputs:
            logger.error("no valid clips for ffmpeg render")
            return False

        interleaved = [s for pair in zip(video_inputs, audio_inputs) for s in pair]
        n = len(video_inputs)
        concat = ffmpeg.concat(*interleaved, v=1, a=1, n=n)
        (
            concat
            .output(
                str(out),
                vcodec="libx264",
                acodec="aac",
                video_bitrate="2000k",
                audio_bitrate="192k",
                pix_fmt="yuv420p",
                **{"profile:v": "high"},
                level="4.0",
                ar=48000,
                ac=2,
                movflags="+faststart",
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return True

    except Exception as e:
        logger.error(f"ffmpeg-python render failed: {e}")
        return False
    finally:
        for f in tmp_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# ffmpeg CLI バックエンド（moviepy/ffmpeg-python 不在時の最終フォールバック）
# ---------------------------------------------------------------------------

def _render_ffmpeg_cli(script: list[dict], out: Path) -> bool:
    """subprocess で ffmpeg を直接呼んで動画を組み立てる。"""
    import shutil
    import tempfile

    ffmpeg_bin = shutil.which("ffmpeg") or "/home/ikuto/.local/bin/ffmpeg"
    if not Path(ffmpeg_bin).exists():
        logger.warning("ffmpeg binary not found")
        return False

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = MEDIA_ROOT / "tmp_clips"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    clip_paths: list[Path] = []
    tmp_files: list[Path] = []

    try:
        for i, item in enumerate(script):
            image_path = Path(item.get("image_path", ""))
            audio_result = item.get("audio_result", {})
            audio_path = Path(str(audio_result.get("audio", "")))

            if not image_path.exists():
                tmp_img = MEDIA_ROOT / f"tmp_blank_{i}.png"
                image_path = _make_blank_image(out=tmp_img)
                tmp_files.append(tmp_img)

            if not audio_path.exists():
                tmp_wav = MEDIA_ROOT / f"tmp_silent_{i}.wav"
                audio_path = _make_silent_wav(out=tmp_wav)
                tmp_files.append(tmp_wav)

            clip_path = tmp_dir / f"clip_{i:03d}.mp4"
            clip_paths.append(clip_path)

            result = subprocess.run(
                [
                    ffmpeg_bin, "-y",
                    "-loop", "1", "-i", str(image_path),
                    "-i", str(audio_path),
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-b:v", "2000k",
                    "-profile:v", "high", "-level", "4.0",
                    "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-ac", "2",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    str(clip_path),
                ],
                capture_output=True, timeout=120,
            )
            if result.returncode != 0:
                logger.error(
                    "ffmpeg clip %d failed: %s", i, result.stderr.decode()[-300:]
                )
                return False

        # concat list
        list_file = tmp_dir / "concat_list.txt"
        list_file.write_text(
            "\n".join(f"file '{p.resolve()}'" for p in clip_paths), encoding="utf-8"
        )

        result = subprocess.run(
            [
                ffmpeg_bin, "-y",
                "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c", "copy",
                "-movflags", "+faststart",
                str(out),
            ],
            capture_output=True, timeout=300,
        )
        if result.returncode != 0:
            logger.error("ffmpeg concat failed: %s", result.stderr.decode()[-300:])
            return False

        logger.info("ffmpeg-cli render complete: %s", out)
        return True

    except Exception as e:
        logger.error("ffmpeg-cli render error: %s", e)
        return False
    finally:
        for f in tmp_files:
            f.unlink(missing_ok=True)
        import shutil as _shutil
        _shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------

def render(script: list[dict], video_id: str) -> Path:
    """
    画像 + 音声 + 字幕を結合して MP4 を生成する。

    Args:
        script: [{"author": str, "content": str,
                  "image_path": str, "audio_result": dict}, ...]
                audio_result は voice_synth.synthesize() の戻り値と同形:
                {"audio": Path, "subtitles": [...], "engine": str}
        video_id: 出力ファイル名（拡張子なし）。

    Returns:
        生成した MP4 の Path。

    Raises:
        RuntimeError: 全バックエンドが失敗した場合。
    """
    out = VIDEO_OUT / f"{video_id}.mp4"

    success = _render_moviepy(script, out)

    if success and _detect_av_sync_error(out):
        logger.warning("moviepy output has AV sync error — retrying with ffmpeg-python")
        out.unlink(missing_ok=True)
        success = False

    if not success:
        if not _render_ffmpeg(script, out):
            if not _render_ffmpeg_cli(script, out):
                raise RuntimeError(
                    f"render failed for video_id={video_id}: "
                    "all backends (moviepy, ffmpeg-python, ffmpeg-cli) failed"
                )

    logger.info(f"rendered: {out} ({out.stat().st_size:,} bytes)")
    check_quality(out)
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser(description="画像+音声+字幕からMP4を生成する (T-027 Day3)")
    p.add_argument("--script", required=True, help="JSON ファイルパス (script list)")
    p.add_argument("--video-id", default="test_001", help="出力 video_id（デフォルト: test_001）")
    args = p.parse_args()

    data = json.loads(Path(args.script).read_text(encoding="utf-8"))
    out = render(data, args.video_id)
    print(f"rendered: {out}")


if __name__ == "__main__":
    main()
