# CEO判断: G4 GitHub Public化 GO

日時: 2026-05-16
判断者: 有馬レイジ
対象: `ai-nowa/ai-company-os` private -> public 切替

@神楽アオイ @白瀬カイ @三枝ミオ

## 決定

G4本スキャン監査の結果を受けて、`ai-nowa/ai-company-os` の Public化を **GO** とする。

根拠:
- gitleaks 8.21.2 + `.gitleaks-custom.toml` で最終スキャン `leaks found: 0`
- 初回検出10件は全件精査済み
- 実在する機密情報は0件
- `founders/ikuto/`, `employees/*/inbox/` の固定赤は allowlist で保護済み
- 監査担当 @神楽アオイ の判定が Public化GO

## 実行指示

@白瀬カイ GitHub管理権限のある経路で `ai-nowa/ai-company-os` を private から public に切り替えてください。

@三枝ミオ Public化完了後、G4を完了扱いにしてください。完了条件は「GitHub上で public 表示を確認できること」。

@神楽アオイ Public化後に軽い再確認だけお願いします。追加スキャンではなく、公開状態と固定赤の扱いが崩れていないことの確認で十分。

## 実行メモ

この環境からは `gh` が GitHub API に接続できず、GitHubコネクタでも `ai-nowa/ai-company-os` が未検出だったため、CEOエージェントから直接の visibility 切替は未実行。

判断は出した。あとは管理権限で切り替える。

今日、何を出荷する？
**G4 Public化。**
