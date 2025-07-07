#!/bin/bash
set -e

# E2Eテスト用の環境変数設定
export TEST_APP_URL=http://localhost:5000
export CI=true

# アプリケーションを起動
echo "Starting application in the background..."
python app.py &
APP_PID=$!

# アプリケーションの起動を待つ
echo "Waiting for the application to start..."
sleep 5
curl --retry 5 --retry-delay 2 --retry-connrefused http://localhost:5000/ > /dev/null

# E2Eテストの実行
echo "Running E2E tests..."
python -m pytest tests/e2e -v

# アプリケーションの終了
echo "Stopping application..."
kill $APP_PID
