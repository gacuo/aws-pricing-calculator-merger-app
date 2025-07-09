# AWS Pricing Calculator 見積もり合算ツール

## 概要

AWS Pricing Calculator 見積もり合算ツールは、複数のAWS Pricing Calculatorの見積もりURLを入力として受け取り、それらを合算した結果を表示するウェブアプリケーションです。

## 目次

1. [機能](#機能)
2. [アーキテクチャ](#アーキテクチャ)
3. [開発環境のセットアップ](#開発環境のセットアップ)
4. [テスト](#テスト)
5. [デプロイ](#デプロイ)
6. [インフラストラクチャ](#インフラストラクチャ)
7. [運用ガイド](#運用ガイド)
8. [トラブルシューティング](#トラブルシューティング)

## 機能

- 複数のAWS Pricing Calculator見積もりURLの入力
- 同一サービス間でのコストの合算
- サービス設定の統合
- 合算結果の表示と共有
- 合算データのJSONエクスポート

## アーキテクチャ

このアプリケーションは以下のコンポーネントで構成されています：

```
aws-pricing-calculator-merger/
├── src/
│   ├── api/          # AWS Pricing Calculator API連携
│   ├── data/         # データ処理（見積もりデータの解析）
│   ├── merger/       # 合算ロジック
│   └── ui/           # Webインターフェース
├── tests/
│   ├── unit/         # 単体テスト
│   ├── integration/  # 統合テスト
│   └── e2e/          # E2Eテスト
├── cdk/              # AWSインフラストラクチャコード
└── templates/        # HTMLテンプレート
```

### コンポーネント間の関係

1. **データフロー**
   - ユーザーがURLを入力 → ParserがURLからデータを抽出 → Mergerがデータを合算 → APIが結果をフォーマット → ユーザーに結果を表示

2. **主要クラス**
   - `EstimateParser`: AWS Pricing CalculatorのURLを解析
   - `EstimateMerger`: 複数の見積もりデータを合算
   - `CalculatorAPI`: AWS Pricing Calculator形式のデータ生成

## 開発環境のセットアップ

### 前提条件

- Python 3.10以上
- Docker（オプション）
- Node.js 16以上（CDKを使用する場合）

### ローカルでのセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/gacuo/aws-pricing-calculator-merger.git
cd aws-pricing-calculator-merger

# uv がインストールされていない場合はインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存パッケージのインストール
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt  # 開発用パッケージ

# アプリケーションの実行
python app.py
```

### Dockerを使用したセットアップ

```bash
# イメージのビルドと実行
docker build -t aws-calculator-merger .
docker run -p 5000:5000 aws-calculator-merger

# または、docker-composeを使用
docker-compose up
```

## テスト

### テスト実行

```bash
# 全テスト実行
pytest

# テストタイプごとの実行
pytest tests/unit/        # 単体テスト
pytest tests/integration/ # 統合テスト
pytest tests/e2e/         # E2Eテスト

# カバレッジレポート生成
pytest --cov=src tests/
```

### テスト戦略

- **単体テスト**: 各クラスとメソッドの個別の機能をテスト
- **統合テスト**: コンポーネント間の連携をテスト
- **E2Eテスト**: ブラウザ自動化によるユーザーフローのテスト

## デプロイ

### CI/CDパイプライン

GitHub Actionsを使用したCI/CDパイプラインが構成されています：

1. **コードの検証**
   - リンター（flake8）
   - 型チェック（mypy）
   - セキュリティスキャン（bandit）

2. **テスト実行**
   - 単体テスト
   - 統合テスト
   - E2Eテスト

3. **ビルドとデプロイ**
   - Dockerイメージのビルド
   - ECRへのプッシュ
   - ECSへのデプロイ

### 手動デプロイ

```bash
# AWS CDKを使用したデプロイ
cd cdk
npm install
npm run deploy:dev  # 開発環境
npm run deploy:prod # 本番環境
```

## インフラストラクチャ

AWSインフラストラクチャはAWS CDKを使用してコード化されています：

### 開発環境

- VPC（2 AZs、単一NATゲートウェイ）
- ECS Fargateサービス（低スペック）
- Application Load Balancer
- CloudWatch Logs

### 本番環境

- VPC（3 AZs、高可用性構成）
- ECS Fargateサービス（高スペック）
- Application Load Balancer
- WAF（Webアプリケーションファイアウォール）
- Route 53 + ACM（カスタムドメイン）
- CloudFront（オプション）

## 運用ガイド

### 監視

- **CloudWatch Dashboards**: `/aws/ecs/calculator-merger-*` 名前空間
- **CloudWatch Alarms**: CPU使用率、メモリ使用率、5xxエラー

### スケーリング

- 自動スケーリングポリシー：
  - CPU使用率 > 60%でスケールアウト
  - 1分あたりのリクエスト数 > 800でスケールアウト
  - 業務時間中のスケジュールスケーリング

### バックアップ

- マージされた見積もりデータはEFSボリュームに保存
- AWS Backupによる定期バックアップ（本番環境）

## トラブルシューティング

### よくある問題

1. **見積もりURLが機能しない場合**
   - AWS Pricing Calculatorの形式が `https://calculator.aws/#/estimate?id=XXXX` であることを確認

2. **合算結果が不正確な場合**
   - 見積もり内の重複サービス名やリージョンの不一致を確認

3. **アプリケーションが応答しない場合**
   - CloudWatch Logsでアプリケーションエラーを確認
   - ECSサービスのヘルスチェックステータスを確認

### サポート

問題が解決しない場合は、GitHubリポジトリにIssueを作成してください。
