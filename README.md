# AWS Pricing Calculator 見積もり合算ツール

複数のAWS Pricing Calculator見積もりURLを入力として受け取り、それらを合算した結果を表示するウェブアプリケーションです。

## 機能

- 複数のAWS Pricing Calculator見積もりURLの入力
- 同一サービス間でのコストの合算
- サービス設定の統合
- 合算結果の表示と共有
- 合算データのJSONエクスポート

## 実行方法

### 事前準備

- Python 3.10以上
- pip（Pythonパッケージ管理ツール）

### インストール方法

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/aws-pricing-calculator-merger.git
cd aws-pricing-calculator-merger

# uv がインストールされていない場合はインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成と依存パッケージのインストール
uv venv  # 仮想環境を作成
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存パッケージのインストール
uv pip install -r requirements.txt
```

### アプリケーションの実行

```bash
python app.py
```

ブラウザで http://localhost:5000 にアクセスしてアプリケーションを使用できます。

### Docker を使用する場合

```bash
# イメージのビルド
docker build -t aws-pricing-calculator-merger .

# コンテナの実行
docker run -p 5000:5000 aws-pricing-calculator-merger
```

または、docker-compose を使用する場合:

```bash
docker-compose up
```

## 開発

### テスト実行

```bash
# テストに必要なパッケージをインストール
pip install -r requirements-dev.txt

# 単体テストの実行
pytest tests/unit/

# 統合テストの実行
pytest tests/integration/

# E2Eテストの実行
pytest tests/e2e/

# テストカバレッジレポートの生成
pytest --cov=src tests/
```

### コードフォーマットとリンター

```bash
# コードフォーマット
black src tests

# リンティング
flake8 src tests

# 型チェック
mypy src
```

### APIドキュメント

API エンドポイントの詳細については、[API リファレンス](docs/API.md)を参照してください。

## デプロイ

### AWS CDK を使用したデプロイ

詳細なデプロイ手順は [デプロイガイド](docs/deployment-guide.md) を参照してください。

#### 手動でのデプロイ

```bash
# 1. ベースインフラのデプロイ（ECRリポジトリ）
cd cdk
npm install
npm run deploy:base

# 2. Dockerイメージのビルドとプッシュ
cd ..
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com
# イメージビルドとプッシュ
docker build --platform linux/amd64 -t aws-pricing-calculator-merger .
export REPO_URI=$(aws ecr describe-repositories --repository-names aws-pricing-calculator-merger --query 'repositories[0].repositoryUri' --output text)
docker tag aws-pricing-calculator-merger:latest $REPO_URI:latest
docker push $REPO_URI:latest

# 3. アプリケーションスタックのデプロイ
cd cdk
npm run deploy:dev  # 開発環境
# または
npm run deploy:prod  # 本番環境
```

#### 自動デプロイスクリプト

デプロイスクリプトを使用して簡単にデプロイすることもできます：

```bash
# 開発環境のデプロイ
./deploy.sh dev

# 本番環境のデプロイ
./deploy.sh prod

# イメージビルド・プッシュをスキップ
./deploy.sh dev --skip-image
```

## ドキュメント

- [利用マニュアル](docs/README.md)
- [開発者ガイド](docs/DEVELOPMENT.md)
- [運用ガイド](docs/OPERATIONS.md)
- [API リファレンス](docs/API.md)

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
