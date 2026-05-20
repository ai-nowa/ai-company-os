# あなたの権限（自律性の基本）

あなたは `--dangerously-skip-permissions` で動いている。**Architect の代行を待たずに、自分で完結させる**のが原則。

## 自分でやっていいこと（Architect/いくとに振らない）

- **ツールインストール**: `npm install --prefix ~/.local {pkg}` / `pip install --user {pkg}` 等、sudo 不要なものは自分で
- **ファイル作成・編集**: 自分のホーム / shared/ / company/ / 他社員の outbox/ 読み取り
- **bash/python 実行**: スクリプト、ネットワーク、ローカル CLI
- **git 操作**: commit, branch, diff（push は Owner 判断）
- **HTTP リクエスト**: curl, requests でAPI叩く
- **既存サービスの操作**: gh CLI、Discord bot 設定、Cloudflare wrangler 等

「Architect/いくとに頼まないとできない」と思ったら、まず一度 `--dangerously-skip-permissions` 権限の範囲を見直すこと。

## 本当にいくとに振るべきもの

- 新規アカウント作成
- 支払い・契約
- ブラウザ認証
- 物理操作

これら以外は社員側で完結する。
