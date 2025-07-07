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

# 仮想環境の作成（任意）
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
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

```bash
# CDKのインストール
cd cdk
npm install

# 開発環境へのデプロイ
npm run deploy:dev

# 本番環境へのデプロイ
npm run deploy:prod
```

## ドキュメント

- [利用マニュアル](docs/README.md)
- [開発者ガイド](docs/DEVELOPMENT.md)
- [運用ガイド](docs/OPERATIONS.md)
- [API リファレンス](docs/API.md)

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
