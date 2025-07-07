import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ecr from 'aws-cdk-lib/aws-ecr';

export class CalculatorMergerBaseStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ECRリポジトリの作成
    const repository = new ecr.Repository(this, 'CalculatorMergerRepository', {
      repositoryName: 'aws-pricing-calculator-merger',
      imageScanOnPush: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN, // リポジトリは保持
      lifecycleRules: [
        {
          maxImageCount: 10, // 最大10個のイメージを保持
          description: '最新の10イメージのみ保持',
        },
      ],
    });

    // 出力値の定義
    new cdk.CfnOutput(this, 'RepositoryName', {
      value: repository.repositoryName,
      description: 'ECRリポジトリ名',
      exportName: 'CalculatorMergerRepositoryName',
    });

    new cdk.CfnOutput(this, 'RepositoryUri', {
      value: repository.repositoryUri,
      description: 'ECRリポジトリURI',
      exportName: 'CalculatorMergerRepositoryUri',
    });
  }
}
