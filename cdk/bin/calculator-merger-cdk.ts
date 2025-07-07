#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CalculatorMergerDevStack } from '../lib/calculator-merger-dev-stack';
import { CalculatorMergerProdStack } from '../lib/calculator-merger-prod-stack';
import { CalculatorMergerBaseStack } from '../lib/calculator-merger-base-stack';

const app = new cdk.App();

// 共通インフラ（ECRリポジトリなど）
new CalculatorMergerBaseStack(app, 'CalculatorMergerBaseStack', {
  env: { 
    account: process.env.CDK_DEFAULT_ACCOUNT, 
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1'
  },
});

// 開発環境スタック
new CalculatorMergerDevStack(app, 'CalculatorMergerDevStack', {
  env: { 
    account: process.env.CDK_DEFAULT_ACCOUNT, 
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1'
  },
  stageName: 'dev',
});

// 本番環境スタック
new CalculatorMergerProdStack(app, 'CalculatorMergerProdStack', {
  env: { 
    account: process.env.CDK_DEFAULT_ACCOUNT, 
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1'
  },
  stageName: 'prod',
  domainName: 'calculator-merger.example.com',
});
