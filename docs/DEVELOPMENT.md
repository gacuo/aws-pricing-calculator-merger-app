# 開発者ガイド

このドキュメントは、AWS Pricing Calculator 見積もり合算ツールの開発に参加する方向けのガイドです。

## 目次

1. [開発環境のセットアップ](#開発環境のセットアップ)
2. [コーディング規約](#コーディング規約)
3. [テスト](#テスト)
4. [デバッグ](#デバッグ)
5. [Pull Requestフロー](#pull-requestフロー)
6. [CI/CD](#cicd)
7. [リリースプロセス](#リリースプロセス)

## 開発環境のセットアップ

### 前提条件

- Python 3.10以上
- Git
- Docker (オプション)
- AWS CLI (インフラ開発用)
- Node.js 16以上 (CDK開発用)

### ローカル環境のセットアップ

1. リポジトリのクローン

```bash
git clone https://github.com/gacuo/aws-pricing-calculator-merger.git
cd aws-pricing-calculator-merger
```

2. 仮想環境の作成と有効化

```bash
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

3. 開発用依存パッケージのインストール

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. pre-commitフックのインストール

```bash
pre-commit install
```

5. アプリケーションの実行

```bash
python app.py
```

### Docker開発環境

Docker Composeを使用した開発環境も利用できます：

```bash
docker-compose -f docker-compose.dev.yml up
```

## コーディング規約

このプロジェクトでは以下のコーディング規約を採用しています：

1. **PEP 8** - Pythonコードスタイルガイド
2. **型アノテーション** - すべての関数とメソッドに型アノテーションを追加
3. **ドキュメンテーション** - 関数、クラス、メソッドにはdocstringを追加
4. **テスト駆動開発** - 新機能の実装前にテストを作成

### 自動フォーマットとリンター

コードの品質を確保するために以下のツールを使用しています：

```bash
# コードフォーマット
black src tests

# リンティング
flake8 src tests

# 型チェック
mypy src

# セキュリティチェック
bandit -r src
```

## テスト

### テスト実行

```bash
# 全テスト実行
pytest

# テストタイプごとの実行
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# カバレッジレポート生成
pytest --cov=src tests/
```

### テストの種類

1. **単体テスト** (`tests/unit/`)
   - 個々のクラスとメソッドの機能をテスト
   - 依存関係はモックを使用

2. **統合テスト** (`tests/integration/`)
   - コンポーネント間の連携をテスト
   - 実際のクラス間の連携を検証

3. **E2Eテスト** (`tests/e2e/`)
   - Seleniumを使用したブラウザテスト
   - 実際のユーザーフローを検証

### テストの書き方

新しい機能を実装する場合は、以下の手順でTDDを実践してください：

1. 新機能のテストを作成
2. テストが失敗することを確認
3. 機能を実装
4. テストが成功することを確認
5. コードをリファクタリング

## デバッグ

### ローカルデバッグ

Flaskのデバッグモードを使用してローカルでデバッグを行えます：

```bash
# デバッグモードで実行
FLASK_ENV=development FLASK_DEBUG=1 python app.py
```

### ロギング

アプリケーションは構造化ロギングを使用しています：

```python
import logging
logger = logging.getLogger(__name__)

# ログの出力
logger.debug("デバッグ情報", extra={"context": "追加情報"})
logger.info("情報ログ")
logger.warning("警告")
logger.error("エラー", exc_info=True)  # 例外情報を含める
```

## Pull Requestフロー

### ブランチ戦略

- `main`: リリース用ブランチ
- `develop`: 開発用ブランチ
- `feature/xxx`: 機能開発用ブランチ
- `bugfix/xxx`: バグ修正用ブランチ

### PRの作成手順

1. 新しいブランチを作成

```bash
git checkout -b feature/new-feature develop
```

2. 変更を実装してコミット

```bash
git add .
git commit -m "機能の説明"
```

3. テストが通ることを確認

```bash
pytest
```

4. プッシュしてPRを作成

```bash
git push origin feature/new-feature
```

5. GitHub上でPRを作成

### コードレビュー基準

- すべてのテストがパスしていること
- コーディング規約に従っていること
- 適切なドキュメンテーションがあること
- 新機能のテストが追加されていること

## CI/CD

### GitHub Actionsワークフロー

1. **Pull Request時**
   - コードリント
   - 単体テスト・統合テスト
   - コードカバレッジレポート

2. **developブランチへのマージ**
   - E2Eテスト
   - Dockerイメージビルド
   - 開発環境へのデプロイ

3. **mainブランチへのマージ**
   - 本番環境へのデプロイ

### 環境変数

CI/CDパイプラインでは以下の環境変数を設定しています：

- `AWS_ACCESS_KEY_ID`: AWSアクセスキー
- `AWS_SECRET_ACCESS_KEY`: AWSシークレットキー
- `ECR_REGISTRY`: ECRレジストリURL
- `DOCKER_USERNAME`: Dockerレジストリユーザー名（オプション）
- `DOCKER_PASSWORD`: Dockerレジストリパスワード（オプション）

## リリースプロセス

### バージョニング

このプロジェクトはセマンティックバージョニングを使用しています：

- **メジャーバージョン**: 互換性のない変更
- **マイナーバージョン**: 後方互換性のある機能追加
- **パッチバージョン**: バグ修正

### リリース手順

1. バージョン番号の更新

```bash
# バージョン情報の更新
vi VERSION
```

2. リリースノートの作成

```bash
vi CHANGELOG.md
```

3. リリースブランチの作成

```bash
git checkout -b release/vX.Y.Z develop
git add VERSION CHANGELOG.md
git commit -m "Release vX.Y.Z"
```

4. mainブランチへのマージ

```bash
git checkout main
git merge --no-ff release/vX.Y.Z
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

5. developブランチへのマージ

```bash
git checkout develop
git merge --no-ff release/vX.Y.Z
```

6. タグとブランチのプッシュ

```bash
git push origin main develop --tags
```
