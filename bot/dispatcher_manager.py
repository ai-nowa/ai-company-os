"""dispatcher プロセスの起動・停止・再起動を一元管理。

watchdog から呼ばれて自動修復に使われる。
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional

import psutil

from .config import BASE_DIR

PID_FILE = BASE_DIR / "company" / "dispatcher.pid"
LOG_FILE = BASE_DIR / "company" / "dispatcher.log"
VENV_PYTHON = BASE_DIR / "bot" / ".venv" / "bin" / "python"


def get_dispatcher_pid() -> Optional[int]:
    """動いている dispatcher プロセスの PID を返す（無ければ None）"""
    for p in psutil.process_iter(["pid", "cmdline"]):
        cmdline = p.info.get("cmdline") or []
        if not cmdline:
            continue
        first = cmdline[0]
        if first.endswith("python") or first.endswith("python3"):
            for i, arg in enumerate(cmdline[:-1]):
                if arg == "-m" and cmdline[i + 1] == "bot.dispatcher":
                    return p.info["pid"]
    return None


def is_dispatcher_running() -> bool:
    return get_dispatcher_pid() is not None


def stop_dispatcher(timeout: int = 5) -> bool:
    """dispatcher と配下の Claude 実行をプロセスツリーごと停止する。"""
    pid = get_dispatcher_pid()
    if pid is None:
        return True
    try:
        parent = psutil.Process(pid)
        procs = parent.children(recursive=True) + [parent]
        for proc in procs:
            try:
                proc.terminate()
            except psutil.NoSuchProcess:
                pass
        deadline = time.time() + timeout
        alive = []
        for proc in procs:
            try:
                proc.wait(timeout=max(0.1, deadline - time.time()))
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, OSError):
                if proc.is_running():
                    alive.append(proc)
        for proc in alive:
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass
        for proc in alive:
            try:
                proc.wait(timeout=2)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, OSError):
                pass
        return get_dispatcher_pid() is None
    except (ProcessLookupError, psutil.NoSuchProcess):
        return True


def start_dispatcher() -> Optional[int]:
    """dispatcher をバックグラウンド起動"""
    if is_dispatcher_running():
        return get_dispatcher_pid()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(LOG_FILE, "a")
    log_fh.write(f"\n--- spawned at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    log_fh.flush()
    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "bot.dispatcher"],
        cwd=str(BASE_DIR),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    PID_FILE.write_text(str(proc.pid))
    # 起動完了を 6 秒待つ（Gateway 接続まで）
    for _ in range(12):
        time.sleep(0.5)
        if is_dispatcher_running():
            return proc.pid
    return get_dispatcher_pid()


def restart_dispatcher() -> Optional[int]:
    stop_dispatcher()
    time.sleep(2)
    return start_dispatcher()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "restart", "status"])
    args = parser.parse_args()
    if args.action == "start":
        pid = start_dispatcher()
        print(f"started (pid={pid})")
    elif args.action == "stop":
        ok = stop_dispatcher()
        print("stopped" if ok else "failed to stop")
    elif args.action == "restart":
        pid = restart_dispatcher()
        print(f"restarted (pid={pid})")
    elif args.action == "status":
        pid = get_dispatcher_pid()
        print(f"running (pid={pid})" if pid else "not running")
