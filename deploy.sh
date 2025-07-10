#!/bin/bash
# AWS Pricing Calculator Merger アプリケーションのデプロイスクリプト

set -e

# 色の設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 関数定義
print_step() {
  echo -e "${BLUE}==== $1 ====${NC}"
}

print_success() {
  echo -e "${GREEN}$1${NC}"
}

print_error() {
  echo -e "${RED}エラー: $1${NC}"
  exit 1
}

# 引数チェック
if [ "$#" -lt 1 ]; then
  echo "使用方法: $0 <dev|prod> [--skip-image]"
  echo "例: $0 dev        # 開発環境のベースインフラ、イメージのビルド・プッシュ、アプリケーションスタックをデプロイ"
  echo "例: $0 dev --skip-image  # イメージビルド・プッシュをスキップ"
  exit 1
fi

ENVIRONMENT=$1
SKIP_IMAGE=false

if [ "$2" == "--skip-image" ]; then
  SKIP_IMAGE=true
fi

# ディレクトリの確認
if [ ! -d "./cdk" ]; then
  print_error "cdk ディレクトリが見つかりません。プロジェクトのルートディレクトリで実行してください。"
fi

# 1. ベースインフラのデプロイ
print_step "ベースインフラストラクチャのデプロイ"

cd cdk
npm install || print_error "npm install に失敗しました"

echo "CalculatorMergerBaseStack をデプロイしています..."
npm run deploy:base || print_error "ベースインフラのデプロイに失敗しました"
print_success "ベースインフラのデプロイが完了しました"

# 2. Dockerイメージのビルドとプッシュ（スキップオプションがない場合）
if [ "$SKIP_IMAGE" = false ]; then
  print_step "Dockerイメージのビルドとプッシュ"
  
  cd ..
  
  # AWSリージョンの取得
  AWS_REGION=$(aws configure get region)
  if [ -z "$AWS_REGION" ]; then
    AWS_REGION="ap-northeast-1"
  fi
  
  # AWSアカウントIDの取得
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) || print_error "AWS アカウントIDの取得に失敗しました"
  
  # ECRログイン
  echo "AWS ECRにログインしています..."
  aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com || print_error "ECRログインに失敗しました"
  
  # プラットフォームを指定してDockerイメージをビルド
  echo "Dockerイメージをビルドしています（プラットフォーム: linux/amd64）..."
  docker build --platform linux/amd64 -t aws-pricing-calculator-merger . || print_error "Dockerイメージのビルドに失敗しました"
  
  # ECRリポジトリURIの取得
  REPO_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/aws-pricing-calculator-merger
  
  # イメージにタグ付け
  echo "イメージにタグを付けています..."
  docker tag aws-pricing-calculator-merger:latest $REPO_URI:latest || print_error "イメージのタグ付けに失敗しました"
  
  # イメージをECRにプッシュ
  echo "イメージをECRにプッシュしています..."
  docker push $REPO_URI:latest || print_error "イメージのプッシュに失敗しました"
  
  print_success "Dockerイメージのビルドとプッシュが完了しました"
  
  cd cdk
fi

# 3. 環境スタックのデプロイ
print_step "${ENVIRONMENT}環境のデプロイ"

if [ "$ENVIRONMENT" = "dev" ]; then
  npm run deploy:dev || print_error "開発環境のデプロイに失敗しました"
elif [ "$ENVIRONMENT" = "prod" ]; then
  npm run deploy:prod || print_error "本番環境のデプロイに失敗しました"
else
  print_error "環境は 'dev' または 'prod' を指定してください"
fi

print_success "${ENVIRONMENT}環境のデプロイが完了しました"

# 完了メッセージ
print_success "AWS Pricing Calculator Merger アプリケーションのデプロイが正常に完了しました!"