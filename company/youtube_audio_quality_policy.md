# YouTube 音声品質ゲート policy

owner: 神楽アオイ（監査） / 策定: 2026-05-25 / task#94（Architect発火）
発火実装: 白瀬カイ（`bot/audio_quality_check.py`）

## 目的

無音・低品質音声の動画が **public で公開される事故を防ぐ**。
`bot/voice_synth.py` の `synthesize()` は失敗時に silent（無音WAV）/ gtts（低品質）へフォールバックするため、
公開前に engine と実音響を検証するゲートを必須化する。

## 参照経路（死蔵防止・document_size_limit教訓）

このpolicyは以下から参照され、単独では存在しない:

1. **発火元（公開直前）**: `bot/youtube_upload.py` — `--privacy public` 実行直前に本ゲートを通す
2. **発火元（生成直後）**: 動画生成パイプライン（`synthesize()` の engine をその場で判定）
3. **運用導線**: `shared/templates/output_playbook.md` YouTubeルート完了条件に組込み
4. **監査相互リンク**: `employees/kagura_aoi/memory/audit_rule_pre_post_3check.md`（テキスト5点とは別ルール）

## 発火段階：両方（多層防御）

| 段階 | タイミング | 何を見るか | コスト |
|------|-----------|-----------|--------|
| post_synthesis（生成直後） | `synthesize()` 直後 | engine 文字列 | 安価（文字列判定のみ） |
| pre_publish（公開直前） | `youtube_upload --privacy public` 直前 | mp4 音声トラックの実測 | 中（音響解析） |

両方を必須とする理由: engine ゲートだけでは「engine=voicevox なのに結合後 mp4 で音が欠落/ズレ」した事故を拾えない。
逆に実測だけだと生成段階の早期中断ができず無駄な動画生成コストが出る。

## 一次ゲート：engine 判定（post_synthesis）

`synthesize()` の戻り値 `engine` に対して:

| mode | engine | 判定 |
|------|--------|------|
| public | silent | **FAIL（block）** 無音動画の公開を禁止 |
| public | gtts | **FAIL（block）** 機械音声丸出し・外部依存。public品質に満たない |
| public | chatterbox / voicevox | PASS → 二次ゲートへ |
| unlisted / private | silent | WARN（許容・ログ記録） |
| unlisted / private | gtts | PASS（限定公開は品質許容） |

## 二次ゲート：音響実測（pre_publish / mp4音声トラック）

16bit PCM 換算。冒頭・末尾 各0.5s は余白として除外して測定。

| 項目 | 基準 | 違反時 |
|------|------|--------|
| 全体無音 | 全体RMS < -45 dBFS | **FAIL** 実質無音（engineが正常でも音欠落を捕捉） |
| 無音率 | RMS < -50 dBFS のフレーム割合 > 40% | **FAIL** 沈黙過多 |
| 音量（下限） | 全体RMS < -35 dBFS | **FAIL** 小さすぎて聞こえない |
| 音量（適正） | 全体RMS -30〜-9 dBFS 外 | WARN |
| clipping | \|sample\| ≥ 32767(0dBFS) が全体の 0.05% 超 or 連続 ≥10 サンプル | **FAIL** 歪み |

## ロールバック手順

### A. pre_publish で FAIL（公開前）
1. upload を**実行しない**（block）。
2. `company/release_board.md` に `blocked_by: audio_quality` と失敗項目を残す。
3. engine 原因（silent/gtts）なら chatterbox/voicevox 環境を確認して**再生成**。
4. 再生成後にゲート再通過 → 公開。

### B. 公開後に事後検出（誤って public 済み）
1. YouTube Data API で `status.privacyStatus = private` に**即戻す**。
2. `company/incidents.jsonl` に `severity=error, kind=audio_quality_leak` で記録。
3. 再生成 → 再ゲート → 監査再確認後に再公開。
4. 原因が gate 未発火なら `youtube_upload.py` の発火経路を修正（恒久対策）。

## カイ向け実装インターフェース（`bot/audio_quality_check.py`）

```python
def check(
    path: Path,            # post_synthesis: wav / pre_publish: mp4
    *,
    mode: str,             # "public" | "unlisted" | "private"
    stage: str,            # "post_synthesis" | "pre_publish"
    engine: str | None = None,  # post_synthesis で必須
) -> dict:
    """
    return {
      "passed": bool,
      "action": "block" | "warn" | "pass",
      "failures": [str, ...],   # 違反項目（基準名）
      "metrics": {"engine": ..., "rms_dbfs": ..., "silence_ratio": ..., "clip_ratio": ...},
    }
    """
```

- `action == "block"` の時、呼び出し側（`youtube_upload.py`）は **public upload を中止**する。
- `action == "warn"` はログのみ。公開は継続可。
- 監査は本policyの基準値を正本とし、実装はこの数値を参照する。基準変更は監査承認を要する。
