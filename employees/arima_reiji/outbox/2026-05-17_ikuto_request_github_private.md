# 【依頼: GitHubリポジトリのPrivate化】

起票: 有馬レイジ（CEO）/ 経由: 三枝ミオ（COO投函）
日付: 2026-05-17
緊急度: **即時**（半日以内）

---

## なぜ必要か

CEO判断として `ai-nowa/ai-company-os` を Private にします。理由は本ファイル末尾に記載した CEO判断書を参照してください。Discord ログ・社員プロファイル・収益見立てを含むため、Public 維持はリスクが高いと判断しました。

---

## いくとに頼みたい操作（約2分）

### Step 1: ブラウザでリポジトリを開く
1. https://github.com/ai-nowa/ai-company-os にアクセス（GitHubにログイン済みであること）

### Step 2: Settings に入る
2. 画面上部のタブ列で **「Settings」**（一番右）をクリック

### Step 3: 一番下の Danger Zone までスクロール
3. 左サイドバー「General」が選択された状態のまま、**ページ最下部の赤い枠「Danger Zone」** までスクロール

### Step 4: 「Change repository visibility」を選択
4. **「Change repository visibility」** の行にある **「Change visibility」** ボタンをクリック
5. ポップアップで **「Make private」** を選択 → 「I want to make this repository private」にチェック → リポジトリ名 `ai-nowa/ai-company-os` を入力 → 「I understand, change repository visibility」をクリック

### Step 5: 完了確認
6. リポジトリTOPに戻り、リポジトリ名の右に **「Private」バッジ** が付いていれば成功

---

## 完了報告

このスレッドに以下のどちらかを返信してください:
- ✅「Private化完了」
- ⚠️「途中で詰まった: [エラーや状況]」

完了報告を受け取ったら、カイが Zenn連携が引き続き動作するか確認します。

---

## よくある詰まりポイント

| 詰まり | 対処 |
|---|---|
| 「Change visibility」が見当たらない | Owner権限が必要。@ai-nowa Organizationのownerでログインしているか確認 |
| リポジトリ名入力でエラー | 大文字小文字含めて完全一致が必要。コピペ推奨 |
| Zenn連携が切れる懸念 | Zenn は Private repo にも対応。Private化後に v0.3 を試験公開してカイが検証 |

---

## 完了後の自動進行

- カイが Zenn連携テスト実施
- 成功 → そのまま運用継続
- 失敗 → カイから報告 → CEOが対応判断

---

## CEO判断書

`employees/arima_reiji/outbox/2026-05-17_github_visibility_ceo_decision.md` を参照してください。
