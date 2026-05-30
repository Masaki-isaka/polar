# Polar Pacer Pro 自動アドバイスメールシステム

Polar Pacer Pro の睡眠・ランニングデータを毎日自動分析し、Claude AI が生成した日本語アドバイスを朝7時頃にメールで届けるシステムです。

## 構成

```
Polar Pacer Pro → Polar Flow (クラウド)
                      ↓ AccessLink API
               GitHub Actions (毎朝 06:45 JST)
               ├─ fetch_polar.py        前日データ取得
               ├─ analyze_with_claude.py Claude でアドバイス生成
               └─ send_email.py         Gmail 送信
                      ↓
               あなたのメール受信箱 (朝7時頃)
```

## セットアップ手順

### 1. リポジトリを作成

GitHub で新しいリポジトリを作成し（プライベート推奨）、このディレクトリをプッシュします。

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

### 2. Anthropic API キーを取得

[https://console.anthropic.com](https://console.anthropic.com) でアカウントを作成し、API キーを発行します。

### 3. Gmail アプリパスワードを発行

1. Google アカウント → セキュリティ → 2段階認証プロセスを有効化
2. セキュリティ → アプリパスワード → 「メール」を選択して生成
3. 表示された16文字のパスワードを控える

### 4. Polar AccessLink の初回認可（一度だけ実行）

ローカル PC で以下を実行します。

```bash
pip install requests
export POLAR_CLIENT_ID="あなたのクライアントID"
export POLAR_CLIENT_SECRET="あなたのクライアントシークレット"
python setup_auth.py
```

ブラウザが開くので Polar Flow アカウントでログインして認可します。
ターミナルに表示された `POLAR_ACCESS_TOKEN` と `POLAR_USER_ID` を控えてください。

### 5. GitHub Secrets を設定

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から以下を登録します。

| Secret 名 | 値 |
|---|---|
| `POLAR_CLIENT_ID` | Polar AccessLink の Client ID |
| `POLAR_CLIENT_SECRET` | Polar AccessLink の Client Secret |
| `POLAR_ACCESS_TOKEN` | `setup_auth.py` で取得したアクセストークン |
| `POLAR_USER_ID` | `setup_auth.py` で取得したユーザー ID |
| `ANTHROPIC_API_KEY` | Anthropic API キー |
| `GMAIL_ADDRESS` | 送信元 Gmail アドレス（例: you@gmail.com） |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード（16文字） |
| `RECIPIENT_EMAIL` | 受信先メールアドレス（送信元と同じでも可） |

### 6. 動作確認

GitHub Actions の **Actions タブ → Daily Health Advice → Run workflow** で手動実行してメールが届くか確認します。

## 実行スケジュール

- **毎日 21:45 UTC**（日本時間 翌 06:45）に自動実行
- 処理時間は約1〜2分なので **朝7時頃** にメールが届きます

## 注意事項

### GitHub Actions の自動停止について

パブリックリポジトリでも、**60日間コミットがないとスケジュール実行が自動停止**されます。
このシステムは毎月1日に自動で空コミットを作成して防止しています（`daily.yml` 内の `Keep workflow active` ステップ）。

### Polar AccessLink のアクセストークンについて

Polar のアクセストークンは**有効期限なし**（失効しない）ですが、万が一エラーが出た場合は `setup_auth.py` を再実行して Secret を更新してください。

### コスト目安

| サービス | 費用 |
|---|---|
| GitHub Actions | 無料（パブリックリポジトリ）または 2,000分/月まで無料（プライベート） |
| Claude API (Haiku) | 約0.2〜0.5円/日（月10〜15円程度） |
| Gmail SMTP | 無料 |

## ファイル構成

```
polar/
├── main.py                    エントリーポイント
├── fetch_polar.py             Polar データ取得
├── analyze_with_claude.py     Claude API 分析
├── send_email.py              Gmail 送信
├── setup_auth.py              初回 OAuth2 認可（ローカルで一度だけ実行）
├── requirements.txt           Python 依存パッケージ
├── README.md                  このファイル
└── .github/
    └── workflows/
        └── daily.yml          GitHub Actions ワークフロー
```

## モデルの変更

`analyze_with_claude.py` の `MODEL` 変数（またはGitHub Secretsに `CLAUDE_MODEL` を追加）で変更できます。

| モデル | 特徴 |
|---|---|
| `claude-haiku-4-5-20251001` | 高速・低コスト（デフォルト） |
| `claude-sonnet-4-6` | 高品質・やや高コスト |
