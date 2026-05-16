## 【依頼: gitleaks / trufflehog / pre-commit のインストール】

### なぜ必要か（1-2文）

明日のGitHubリポジトリ公開（G1: シークレットスキャン）の本スキャンに必要です。
簡易Pythonスキャン（検出ゼロ）では網羅できないエントロピーベース検出と独自ルール適用を、gitleaks + trufflehog で実施します。pre-commit hook によって今後のcommit時にも自動チェックが入ります。

### 詳細手順（番号付き、そのまま実行できる粒度）

1. ターミナルを開き、以下を順に実行：

   ```bash
   # gitleaks インストール（バイナリ直接、apt不要）
   GITLEAKS_VERSION="8.21.2"
   curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" -o /tmp/gitleaks.tar.gz
   sudo tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks
   sudo chmod +x /usr/local/bin/gitleaks

   # trufflehog インストール
   curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sudo sh -s -- -b /usr/local/bin

   # pre-commit インストール（既にpipが使える前提）
   pip install --user pre-commit
   ```

2. インストール確認：

   ```bash
   gitleaks version
   trufflehog --version
   pre-commit --version
   ```

3. 3つともバージョンが表示されれば完了。

### 期待される結果

- `gitleaks version` → 8.21.2 が表示される
- `trufflehog --version` → バージョン番号が表示される
- `pre-commit --version` → バージョン番号が表示される

### 完了時の報告先

`📥｜いくと依頼` チャンネル、または @三枝ミオ / @白瀬カイ に「インストール完了」と一言。即、本スキャン実行に入ります。

### 緊急度

[今日中]（明日朝のG1本スキャン作業に必要）

### 起票者

@白瀬カイ（shirase_kai）

---

### 補足（トラブル時）

- `sudo` でパスワードを求められたら入力してください
- インストールに失敗した場合は、エラー出力をそのまま @白瀬カイ に貼り付けてください。代替手順を即用意します
- WSL2 環境を想定しています。macOS の場合は `brew install gitleaks trufflesecurity/trufflehog/trufflehog pre-commit` で代替可能
