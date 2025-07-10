# AWS Pricing Calculator Merger デプロイガイド

このドキュメントでは、AWS Pricing Calculator Merger アプリケーションをデプロイする手順について説明します。

## 前提条件

- AWS CLI がインストールされ、設定されていること
- Docker がインストールされていること
- Node.js と npm がインストールされていること
- AWS CDK がインストールされていること (`npm install -g aws-cdk`)

## デプロイ手順

デプロイは次の3つのステップで行います：
1. ベースインフラストラクチャのデプロイ (ECRリポジトリなど)
2. Dockerイメージのビルドとプッシュ
3. アプリケーションスタックのデプロイ (ECS Fargateなど)

### 1. ベースインフラストラクチャのデプロイ

```bash
# cdk ディレクトリに移動
cd cdk

# 依存関係のインストール
npm install

# ベーススタックのデプロイ
npm run deploy:base
```

このコマンドは `CalculatorMergerBaseStack` をデプロイし、ECRリポジトリを作成します。

### 2. Dockerイメージのビルドとプッシュ

```bash
# プロジェクトのルートディレクトリに移動
cd ..

# AWS ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com

# プラットフォームを指定してDockerイメージをビルド
docker build --platform linux/amd64 -t aws-pricing-calculator-merger .

# ECRリポジトリURIの取得
export REPO_URI=$(aws ecr describe-repositories --repository-names aws-pricing-calculator-merger --query 'repositories[0].repositoryUri' --output text)

# イメージにタグ付け
docker tag aws-pricing-calculator-merger:latest $REPO_URI:latest

# ECRへイメージをプッシュ
docker push $REPO_URI:latest
```

### 3. アプリケーションスタックのデプロイ

```bash
# cdk ディレクトリに移動
cd cdk

# 開発環境のデプロイ
npm run deploy:dev

# または本番環境のデプロイ
# npm run deploy:prod
```

## トラブルシューティング

### ECRイメージが見つからないエラー

以下のようなエラーが発生した場合：

```
CannotPullContainerError: pull image manifest has been retried 1 time(s): failed to resolve ref 596006113359.dkr.ecr.ap-northeast-1.amazonaws.com/aws-pricing-calculator-merger:latest: not found
```

これは、ECRリポジトリにイメージがプッシュされていないことを示しています。上記の「2. Dockerイメージのビルドとプッシュ」の手順を実行してください。

### exec format error

以下のようなエラーがECSタスクのログに表示される場合：

```
exec /usr/local/bin/python: exec format error
```

これは、Dockerイメージのアーキテクチャとターゲットの実行環境のアーキテクチャが一致していないことを示しています。このエラーは通常、ARM向けのイメージをx86_64のインスタンスで実行しようとした場合（またはその逆）に発生します。

解決策:
1. Dockerfileに`--platform=linux/amd64`フラグを追加する
2. Dockerイメージのビルド時に`--platform linux/amd64`フラグを使用する

```bash
# 正しいプラットフォームを指定してビルド
docker build --platform linux/amd64 -t aws-pricing-calculator-merger .
```

### イメージプッシュ時のアクセス拒否エラー

```
denied: User: arn:aws:iam::123456789012:user/username is not authorized to perform: ecr:PutImage
```

このエラーが発生した場合、AWSアカウントに対して適切な権限が設定されていません。IAMユーザーまたはロールに以下の権限が必要です：

- ecr:GetAuthorizationToken
- ecr:BatchCheckLayerAvailability
- ecr:PutImage
- ecr:InitiateLayerUpload
- ecr:UploadLayerPart
- ecr:CompleteLayerUpload

## デプロイの確認

デプロイが完了したら、AWS Management Consoleでリソースを確認できます：

1. ECRリポジトリ - AWS ECR コンソールでイメージを確認
2. ECSサービス - AWS ECS コンソールでサービスとタスク状態を確認
3. ALB - AWS EC2 コンソールでロードバランサーのDNS名を確認

ロードバランサーのDNS名にアクセスして、アプリケーションが正常に動作していることを確認してください。