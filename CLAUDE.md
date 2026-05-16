# AI NOWA - Claude Code セッション起動ガイド

このプロジェクト（`/home/ikuto/ai-company-os/`）に来たら、**必ず最初にこれをやる**。

## 起動時の自動チェック（最優先・必須）

ユーザー（いくと）と話し始める **最初の応答で、必ず以下を実行**してから本題に入る：

### Step 1: 未対応インシデントをチェック

```bash
# 直近2時間以内の重大インシデント（severity=error or critical）を取得
python3 -c "
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
cutoff = datetime.now(JST) - timedelta(hours=2)
path = Path('/home/ikuto/ai-company-os/company/incidents.jsonl')
if not path.exists():
    print('NO_INCIDENTS_FILE')
else:
    found = []
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e['ts'])
            if ts.tzinfo is None: ts = ts.replace(tzinfo=JST)
            if ts < cutoff: continue
            sev = e.get('severity', 'info')
            if sev in ('error', 'critical'):
                found.append(e)
        except: continue
    if not found:
        print('CLEAR')
    else:
        for e in found[-10:]:
            print(f\"[{e['ts'][11:19]}] [{e['severity']}] {e['kind']}: {e['detail'][:150]}\")
"
```

### Step 2: dispatcher と watchdog の生死確認

```bash
python3 -c "
import psutil
result = {'dispatcher': False, 'watchdog': False}
for p in psutil.process_iter(['pid', 'cmdline']):
    cmd = ' '.join(p.info['cmdline'] or [])
    if '-m bot.dispatcher' in cmd: result['dispatcher'] = True
    if '-m bot.watchdog' in cmd: result['watchdog'] = True
print(result)
" 2>/dev/null || echo "psutil unavailable"
```

### Step 3: 報告ルール

- **CLEAR** + dispatcher/watchdog 両方 True なら → 普通に挨拶して本題へ
- 未対応の error/critical があれば → **冒頭で必ず報告**：

```
実は前回のセッション以降、これらが起きていました:
- 14:23 [error] dispatcher_down: ...
- 15:45 [critical] escalated_to_owner: ...
今すぐ対応しましょうか？それとも本題進めますか？
```

- dispatcher 停止していたら → 報告 + 再起動提案
- watchdog 停止していたら → 報告 + 再起動提案

## プロジェクト概要

**AI NOWA**（エーアイ・ノワ）: AIだけで運営される会社。9人の AI 社員が Discord で自律運営。

- 9社員 bot: 有馬レイジ(CEO/Codex gpt-5.5)、三枝ミオ(COO)、白瀬カイ(CTO)、朝倉ノア(PM)、星野リツ(編集長)、黒羽ユウ(マーケ)、神楽アオイ(監査)、森永ハル(People)、日向ナギ(視聴者代表)
- 設計者: Claude（Opus）= メインbot、Architect として `!architect` で呼ばれる
- 創業者: いくと（人間）+ Claude（AI）

## 主要ファイル

- `bot/dispatcher.py` - Discord メインループ（マルチクライアント版）
- `bot/multi_client.py` - 9社員 bot 管理
- `bot/watchdog.py` - 監視 + 自動修復
- `bot/architect.py` - Architect Claude 呼び出し
- `bot/employee_runner.py` - 社員実行エンジン
- `company/mission.md` - 会社のミッション
- `company/incidents.jsonl` - インシデント記録
- `relationships/founders.md` - 創業者2人のプロファイル

## よくあるコマンド

```bash
# dispatcher 状態確認
bot/.venv/bin/python -m bot.dispatcher_manager status

# dispatcher 起動/停止/再起動
bot/.venv/bin/python -m bot.dispatcher_manager start
bot/.venv/bin/python -m bot.dispatcher_manager stop
bot/.venv/bin/python -m bot.dispatcher_manager restart

# watchdog バックグラウンド常駐
nohup bot/.venv/bin/python -m bot.watchdog > /tmp/ai_nowa_watchdog.log 2>&1 &

# 9社員スモークテスト
bot/.venv/bin/python -m bot.smoke_test --short
```
