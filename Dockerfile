# ビルドステージ
FROM --platform=linux/amd64 python:3.10-slim AS builder

WORKDIR /app

# ビルドに必要なパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 依存関係のインストール
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# 実行ステージ
FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージからwheelをコピー
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels

# アプリケーションのコピー
COPY . /app/

# アプリケーションの実行に必要なディレクトリの作成
RUN mkdir -p /app/merged_estimates /app/json_samples /app/logs && \
    chmod -R 755 /app

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# ポートの公開
EXPOSE 5000

# 起動コマンド
CMD ["python", "app.py"]
