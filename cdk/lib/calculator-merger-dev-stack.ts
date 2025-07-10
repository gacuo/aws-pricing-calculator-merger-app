import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

interface CalculatorMergerDevStackProps extends cdk.StackProps {
  stageName: string;
}

export class CalculatorMergerDevStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: CalculatorMergerDevStackProps) {
    super(scope, id, props);

    const stageName = props.stageName;

    // VPCの作成
    const vpc = new ec2.Vpc(this, 'CalculatorMergerVPC', {
      maxAzs: 2,
      natGateways: 1,
      vpcName: `calculator-merger-${stageName}-vpc`,
    });

    // ECSクラスターの作成
    const cluster = new ecs.Cluster(this, 'CalculatorMergerCluster', {
      vpc: vpc,
      clusterName: `aws-calculator-merger-${stageName}-cluster`,
      containerInsights: true,
    });

    // ECRリポジトリの参照
    const repository = ecr.Repository.fromRepositoryName(
      this,
      'CalculatorMergerRepo',
      'aws-pricing-calculator-merger'
    );

    // タスク実行ロールの作成
    const executionRole = new iam.Role(this, 'TaskExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
      ],
    });

    // タスクロールの作成
    const taskRole = new iam.Role(this, 'TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    // CloudWatchログ設定
    const logGroup = new logs.LogGroup(this, 'CalculatorMergerLogs', {
      logGroupName: `/ecs/aws-calculator-merger-${stageName}`,
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // FargateタスクDefinitionの作成
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'CalculatorMergerTask', {
      family: `aws-calculator-merger-${stageName}`,
      memoryLimitMiB: 512,
      cpu: 256,
      executionRole: executionRole,
      taskRole: taskRole,
    });

    // コンテナの追加
    taskDefinition.addContainer('CalculatorMergerContainer', {
      containerName: 'aws-calculator-merger-container',
      image: ecs.ContainerImage.fromEcrRepository(repository),
      essential: true,
      portMappings: [{ containerPort: 5000 }],
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'calculator-merger',
        logGroup: logGroup,
      }),
      environment: {
        'FLASK_ENV': stageName === 'prod' ? 'production' : 'development',
        'STAGE': stageName,
      },
    });

    // ALBの作成
    const lb = new elbv2.ApplicationLoadBalancer(this, 'CalculatorMergerLB', {
      vpc,
      internetFacing: true,
      loadBalancerName: `calculator-merger-${stageName}-lb`,
    });

    // リスナーとターゲットグループの作成
    const listener = lb.addListener('Listener', { port: 80 });
    
    // セキュリティグループの作成とルール追加
    const lbSecurityGroup = new ec2.SecurityGroup(this, 'LBSecurityGroup', {
      vpc,
      allowAllOutbound: true,
      securityGroupName: `calculator-merger-${stageName}-lb-sg`,
    });
    
    lbSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow HTTP traffic from anywhere'
    );
    
    // サービスのセキュリティグループを作成
    const serviceSecurityGroup = new ec2.SecurityGroup(this, 'ServiceSecurityGroup', {
      vpc,
      allowAllOutbound: true,
      securityGroupName: `calculator-merger-${stageName}-service-sg`,
    });
    
    // LBからのトラフィックを許可
    serviceSecurityGroup.addIngressRule(
      lbSecurityGroup,
      ec2.Port.tcp(80),
      'Allow traffic from ALB'
    );
    
    // ターゲットグループを先に作成
    const targetGroup = listener.addTargets('CalculatorMergerTarget', {
      port: 80,
      targets: [],  // 後でサービスを追加
      healthCheck: {
        path: '/',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyHttpCodes: '200',
      },
    });
    
    // ECS Fargateサービスの作成
    const service = new ecs.FargateService(this, 'CalculatorMergerService', {
      cluster,
      taskDefinition,
      serviceName: `aws-calculator-merger-${stageName}-service`,
      desiredCount: 1,
      assignPublicIp: false,
      healthCheckGracePeriod: cdk.Duration.seconds(60),
      securityGroups: [serviceSecurityGroup],
    });
    
    // サービスをターゲットグループに登録
    targetGroup.addTarget(service);
    
    // Auto Scaling設定
    const scalableTarget = service.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 4,
    });
    
    // CPU使用率によるスケーリング
    scalableTarget.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.seconds(60),
      scaleOutCooldown: cdk.Duration.seconds(60),
    });
    
    // リクエスト数によるスケーリング
    scalableTarget.scaleOnRequestCount('RequestScaling', {
      requestsPerTarget: 1000,
      targetGroup: targetGroup,
    });
    
    // CloudWatchアラームの作成
    const cpuAlarm = new cloudwatch.Alarm(this, 'CpuUtilizationAlarm', {
      metric: service.metricCpuUtilization(),
      threshold: 85,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      alarmDescription: 'CPU utilization is too high',
      alarmName: `calculator-merger-${stageName}-cpu-alarm`,
    });
    
    // 出力値の定義
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: lb.loadBalancerDnsName,
      description: 'アプリケーションのURL',
      exportName: `CalculatorMerger${stageName.charAt(0).toUpperCase() + stageName.slice(1)}LbDns`,
    });
    
    new cdk.CfnOutput(this, 'ServiceName', {
      value: service.serviceName,
      description: 'ECS サービス名',
      exportName: `CalculatorMerger${stageName.charAt(0).toUpperCase() + stageName.slice(1)}ServiceName`,
    });
  }
}
