#!/bin/bash
# DiffMovie 起動スクリプト
# ダブルクリックでアプリを起動し、Chromeで開きます

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

echo "================================"
echo "  DiffMovie - 動画比較ツール"
echo "================================"
echo ""

# 仮想環境があれば有効化
if [ -d "venv" ]; then
    echo "[INFO] 仮想環境を有効化中..."
    source venv/bin/activate
fi

# 依存関係のインストール確認
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "[INFO] 依存パッケージをインストール中..."
    pip3 install -r requirements.txt
fi

# アプリを起動
echo "[INFO] アプリを起動中..."
python3 app.py &
APP_PID=$!

# サーバーが起動するまで待機
echo "[INFO] サーバーの起動を待機中..."
sleep 3

# Chromeで開く
echo "[INFO] Chromeでアプリを開きます..."
open -a "Google Chrome" "http://127.0.0.1:7860"

echo ""
echo "[INFO] アプリが起動しました"
echo "[INFO] 終了するにはこのウィンドウを閉じるか、Ctrl+C を押してください"
echo ""

# プロセスを待機
wait $APP_PID

