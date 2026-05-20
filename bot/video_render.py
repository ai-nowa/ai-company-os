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

def _make_blank_image(width: int = 1280, height: int = 720, out: Optional[Path] = None) -> Path:
    from PIL import Image

    img = Image.new("RGB", (width, height), (0, 0, 0))
    if out is None:
        out = MEDIA_ROOT / "tmp_blank.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out))
    return out


def _make_silent_wav(duration_s: float = 3.0, out: Optional[Path] = None) -> Path:
    """無音WAVを生成する (可変長対応 / Day2引き継ぎ: bytes(2*n) でゼロ埋め)。"""
    if out is None:
        out = MEDIA_ROOT / "tmp_silent.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sr = 22050
    n = int(duration_s * sr)
    with wave.open(str(out), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(2 * n))
    return out


def _audio_duration_ffprobe(audio_path: Path) -> float:
    """ffprobe で音声長を取得。失敗時は 3.0 を返す。"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(audio_path)],
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
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
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
            .output(str(out), vcodec="libx264", acodec="aac")
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
                    "-c:a", "aac", "-b:a", "128k",
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
