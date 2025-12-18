#!/bin/bash
# DiffMovie GitHubアップロードスクリプト
# ダブルクリックでGitHubにプッシュします
# 使用アカウント: hiroki-abe-58 (個人用)

set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

echo "================================"
echo "  DiffMovie - GitHub Upload"
echo "================================"
echo ""
echo "[INFO] 使用アカウント: hiroki-abe-58 (個人用)"
echo "[INFO] リポジトリ: git@github.com:hiroki-abe-58/DiffMovie.git"
echo ""

# Git設定を確認・設定（ローカルリポジトリ用）
echo "[INFO] Git設定を確認中..."
git config user.name "hiroki-abe-58"
git config user.email "hiroki-abe-58@users.noreply.github.com"

# 現在の設定を表示
echo "[INFO] 現在のGit設定:"
echo "  user.name: $(git config user.name)"
echo "  user.email: $(git config user.email)"
echo ""

# Gitリポジトリの初期化（まだの場合）
if [ ! -d ".git" ]; then
    echo "[INFO] Gitリポジトリを初期化中..."
    git init
    
    # リモートを追加（github.comホストを使用 = 個人用アカウント）
    git remote add origin git@github.com:hiroki-abe-58/DiffMovie.git
    echo "[INFO] リモートリポジトリを設定しました"
fi

# リモートURLを確認・修正
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
EXPECTED_REMOTE="git@github.com:hiroki-abe-58/DiffMovie.git"

if [ "$CURRENT_REMOTE" != "$EXPECTED_REMOTE" ]; then
    echo "[WARN] リモートURLが異なります。修正します..."
    git remote set-url origin "$EXPECTED_REMOTE"
fi

echo "[INFO] リモートURL: $(git remote get-url origin)"
echo ""

# SSH接続テスト
echo "[INFO] GitHub SSH接続をテスト中..."
ssh -T git@github.com 2>&1 | head -1 || true
echo ""

# ステータス確認
echo "[INFO] 変更されたファイル:"
git status --short
echo ""

# 変更をステージング
echo "[INFO] 変更をステージング中..."
git add -A

# コミットメッセージを入力
echo ""
read -p "コミットメッセージを入力してください (空欄でデフォルト): " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Update $(date '+%Y-%m-%d %H:%M:%S')"
fi

# コミット
echo "[INFO] コミット中..."
git commit -m "$COMMIT_MSG" || echo "[INFO] コミットする変更がありません"

# プッシュ
echo ""
echo "[INFO] GitHubにプッシュ中..."
git push -u origin main 2>/dev/null || git push -u origin master 2>/dev/null || {
    echo "[INFO] 初回プッシュのため、mainブランチを作成します..."
    git branch -M main
    git push -u origin main
}

echo ""
echo "================================"
echo "  アップロード完了"
echo "================================"
echo ""
echo "[INFO] リポジトリURL: https://github.com/hiroki-abe-58/DiffMovie"
echo ""

# ブラウザでリポジトリを開く
read -p "ブラウザでリポジトリを開きますか？ (y/N): " OPEN_BROWSER
if [ "$OPEN_BROWSER" = "y" ] || [ "$OPEN_BROWSER" = "Y" ]; then
    open "https://github.com/hiroki-abe-58/DiffMovie"
fi

echo ""
echo "このウィンドウを閉じるにはEnterキーを押してください..."
read


