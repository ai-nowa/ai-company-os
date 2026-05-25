"""EXP-003 Garasugoshi #1: render scene.html via Playwright and compose mp4.

Usage:
    python render.py [--fps 30] [--out garasugoshi_01.mp4]
"""
import argparse
import asyncio
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_SCENE = HERE / "scene.html"
FRAMES_DIR = HERE / "frames"


async def render_frames(fps: int, scene_path: Path) -> int:
    from playwright.async_api import async_playwright

    FRAMES_DIR.mkdir(exist_ok=True)
    for f in FRAMES_DIR.glob("*.png"):
        f.unlink()

    async with async_playwright() as p:
        chromium_path = Path.home() / ".cache/ms-playwright/chromium-1217/chrome-linux64/chrome"
        browser = await p.chromium.launch(executable_path=str(chromium_path))
        ctx = await browser.new_context(viewport={"width": 1080, "height": 1920})
        page = await ctx.new_page()
        await page.goto(scene_path.as_uri())
        total_ms = await page.evaluate("window.totalDuration")
        frame_step_ms = 1000 // fps
        frame_count = int(total_ms // frame_step_ms)
        for i in range(frame_count):
            ms = i * frame_step_ms
            await page.evaluate(f"window.setT({ms})")
            await page.screenshot(path=str(FRAMES_DIR / f"f_{i:05d}.png"))
        await browser.close()
        return frame_count


def generate_ambient(out_wav: Path, duration_s: float) -> None:
    """ガラス越し音声方針v1.1: ナレ無し・環境音のみ（lo-fi BGM/パッドは撤回）。

    「観察」の生っぽさ・静けさを優先し、楽音パッドは載せない（編集長判断 2026-05-25）。
    低いブラウンノイズ＋かすかなサーバーハム音のみ。
    完全無音禁止(task#93)を満たすため compose 前に必ず生成する。
    RMS -22dBFS前後 / クリッピング無しを狙い、音声品質ゲートを通す。"""
    dur = duration_s + 1.0
    fade_out_start = max(0.0, duration_s - 3.0)
    filt = (
        f"anoisesrc=color=brown:sample_rate=44100:duration={dur}:amplitude=0.5,"
        f"highpass=f=40,lowpass=f=900,volume=0.20[air];"
        f"sine=frequency=60:sample_rate=44100:duration={dur},volume=0.06[hum];"
        f"sine=frequency=120:sample_rate=44100:duration={dur},volume=0.03[hum2];"
        f"[air][hum][hum2]amix=inputs=3:normalize=0,afade=t=in:d=2.5,"
        f"afade=t=out:st={fade_out_start:.1f}:d=3,volume=16dB[mix]"
    )
    cmd = [
        "ffmpeg", "-y", "-filter_complex", filt,
        "-map", "[mix]", "-ac", "2", "-ar", "44100", str(out_wav),
    ]
    subprocess.run(cmd, check=True)


def compose_video(fps: int, out_path: Path, audio_path: Path | None = None) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(FRAMES_DIR / "f_%05d.png"),
    ]
    if audio_path is not None:
        cmd += ["-i", str(audio_path)]
    cmd += [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920",
        "-movflags", "+faststart",
    ]
    if audio_path is not None:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd.append(str(out_path))
    subprocess.run(cmd, check=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--out", type=str, default="garasugoshi_01.mp4")
    parser.add_argument("--scene", type=str, default=str(DEFAULT_SCENE))
    args = parser.parse_args()
    out_path = HERE / args.out
    scene_path = Path(args.scene)
    if not scene_path.is_absolute():
        scene_path = HERE / scene_path

    frame_count = await render_frames(args.fps, scene_path)
    print(f"rendered {frame_count} frames at {args.fps}fps from {scene_path.name}")
    duration_s = frame_count / args.fps
    audio_path = HERE / f"ambient_{out_path.stem}.wav"
    generate_ambient(audio_path, duration_s)
    print(f"generated ambient ({duration_s:.1f}s) -> {audio_path.name}")
    compose_video(args.fps, out_path, audio_path)
    print(f"composed -> {out_path}")
    shutil.rmtree(FRAMES_DIR)


if __name__ == "__main__":
    asyncio.run(main())
