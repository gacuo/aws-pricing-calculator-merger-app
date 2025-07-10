import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import * as appscaling from 'aws-cdk-lib/aws-applicationautoscaling';
import * as s3 from 'aws-cdk-lib/aws-s3';

interface CalculatorMergerProdStackProps extends cdk.StackProps {
  stageName: string;
  domainName?: string;
}

export class CalculatorMergerProdStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: CalculatorMergerProdStackProps) {
    super(scope, id, props);

    const stageName = props.stageName;
    const domainName = props.domainName;

    // VPCの作成
    const vpc = new ec2.Vpc(this, 'CalculatorMergerVPC', {
      maxAzs: 3,  // 本番環境では3つのAZを使用
      natGateways: 3,  // 各AZにNATゲートウェイを配置
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
      retention: logs.RetentionDays.THREE_MONTHS,  // 本番環境は3ヶ月保持
      removalPolicy: cdk.RemovalPolicy.RETAIN,  // 本番環境のログは保持
    });

    // FargateタスクDefinitionの作成
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'CalculatorMergerTask', {
      family: `aws-calculator-merger-${stageName}`,
      memoryLimitMiB: 1024,  // 本番環境は高めのスペック
      cpu: 512,
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
        'FLASK_ENV': 'production',
        'STAGE': stageName,
      },
      healthCheck: {
        command: ["CMD-SHELL", "curl -f http://localhost:5000/ || exit 1"],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });

    // ALBの作成
    const lb = new elbv2.ApplicationLoadBalancer(this, 'CalculatorMergerLB', {
      vpc,
      internetFacing: true,
      loadBalancerName: `calculator-merger-${stageName}-lb`,
      idleTimeout: cdk.Duration.seconds(60),
    });

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
    
    lbSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      'Allow HTTPS traffic from anywhere'
    );
    
    lb.addSecurityGroup(lbSecurityGroup);

    // リスナーとターゲットグループの作成
    let httpsListener;
    
    if (domainName) {
      // ドメイン名が指定されている場合はカスタムドメイン設定
      const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
        domainName: domainName.split('.').slice(-2).join('.'),  // 親ドメイン名を取得
      });
      
      // SSL証明書の作成
      const alb_certificate = new acm.Certificate(this, 'Certificate', {
        domainName: domainName,
        validation: acm.CertificateValidation.fromDns(hostedZone),
      });
      
      // HTTPSリスナーの追加
      httpsListener = lb.addListener('HttpsListener', {
        port: 443,
        certificates: [alb_certificate],
        protocol: elbv2.ApplicationProtocol.HTTPS,
        sslPolicy: elbv2.SslPolicy.RECOMMENDED,
      });
      
      // HTTPからHTTPSへのリダイレクト
      lb.addListener('HttpListener', {
        port: 80,
        protocol: elbv2.ApplicationProtocol.HTTP,
        defaultAction: elbv2.ListenerAction.redirect({
          protocol: 'HTTPS',
          port: '443',
          permanent: true,
        }),
      });
      
      // Route 53にAレコードを追加
      new route53.ARecord(this, 'AliasRecord', {
        zone: hostedZone,
        recordName: domainName,
        target: route53.RecordTarget.fromAlias(new targets.LoadBalancerTarget(lb)),
        ttl: cdk.Duration.minutes(5),
      });
    } else {
      // ドメイン名が指定されていない場合は通常のHTTPリスナー
      httpsListener = lb.addListener('HttpListener', { port: 80 });
    }

    // ECS Fargateサービスの作成
    const service = new ecs.FargateService(this, 'CalculatorMergerService', {
      cluster,
      taskDefinition,
      serviceName: `aws-calculator-merger-${stageName}-service`,
      desiredCount: 2,  // 本番環境では最低2インスタンス
      assignPublicIp: false,
      healthCheckGracePeriod: cdk.Duration.seconds(120),
      securityGroups: [
        new ec2.SecurityGroup(this, 'ServiceSecurityGroup', {
          vpc,
          allowAllOutbound: true,
          securityGroupName: `calculator-merger-${stageName}-service-sg`,
        })
      ],
      deploymentController: {
        type: ecs.DeploymentControllerType.ECS,  // ローリングデプロイ
      },
      circuitBreaker: { rollback: true },  // デプロイ失敗時に自動ロールバック
    });
    
    // サービスにALBを紐付け
    httpsListener.addTargets('CalculatorMergerTarget', {
      port: 80,
      targets: [service],
      healthCheck: {
        path: '/',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
        healthyHttpCodes: '200',
      },
      deregistrationDelay: cdk.Duration.seconds(30),
    });
    
    // Auto Scaling設定
    const scalableTarget = service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 10,  // 本番環境はより高いキャパシティ
    });
    
    // CPU使用率によるスケーリング
    scalableTarget.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 60,  // 本番環境では余裕を持たせる
      scaleInCooldown: cdk.Duration.seconds(300),
      scaleOutCooldown: cdk.Duration.seconds(60),
    });
    
    // リクエスト数によるスケーリング
    scalableTarget.scaleOnRequestCount('RequestScaling', {
      requestsPerTarget: 800,
      targetGroup: httpsListener.addTargets('AutoScalingTarget', {
        port: 80,
        targets: [service],
      }),
    });
    
    // スケジュールによるスケーリング（業務時間中は高めの容量）
    scalableTarget.scaleOnSchedule('BusinessHoursScaling', {
      schedule: appscaling.Schedule.cron({ hour: '8', minute: '0' }),
      minCapacity: 4,
    });
    
    scalableTarget.scaleOnSchedule('AfterHoursScaling', {
      schedule: appscaling.Schedule.cron({ hour: '18', minute: '0' }),
      minCapacity: 2,
    });
    
    // CloudWatchアラームの作成
    // CPU使用率アラーム
    const cpuAlarm = new cloudwatch.Alarm(this, 'CpuUtilizationAlarm', {
      metric: service.metricCpuUtilization(),
      threshold: 80,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      alarmDescription: 'CPU utilization is too high',
      alarmName: `calculator-merger-${stageName}-cpu-alarm`,
    });
    
    // メモリ使用率アラーム
    const memoryAlarm = new cloudwatch.Alarm(this, 'MemoryUtilizationAlarm', {
      metric: service.metricMemoryUtilization(),
      threshold: 80,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      alarmDescription: 'Memory utilization is too high',
      alarmName: `calculator-merger-${stageName}-memory-alarm`,
    });
    
    // ALB 5xxエラーアラーム
    const error5xxAlarm = new cloudwatch.Alarm(this, 'Http5xxAlarm', {
      metric: lb.metricHttpCodeTarget(elbv2.HttpCodeTarget.TARGET_5XX_COUNT),
      threshold: 10,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      alarmDescription: 'Too many 5XX errors',
      alarmName: `calculator-merger-${stageName}-5xx-alarm`,
    });

    // WAF設定（本番環境のみ）
    const webAcl = new wafv2.CfnWebACL(this, 'WebACL', {
      name: `calculator-merger-${stageName}-waf`,
      defaultAction: { allow: {} },
      scope: 'REGIONAL',
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: `calculator-merger-${stageName}-waf`,
        sampledRequestsEnabled: true,
      },
      rules: [
        // レートベースのルール
        {
          name: 'RateLimitRule',
          priority: 1,
          action: { block: {} },
          statement: {
            rateBasedStatement: {
              limit: 1000,
              aggregateKeyType: 'IP',
            },
          },
          visibilityConfig: {
            cloudWatchMetricsEnabled: true,
            metricName: 'RateLimitRule',
            sampledRequestsEnabled: true,
          },
        },
        // AWS管理ルール - SQLインジェクション対策
        {
          name: 'AWSManagedRulesSQLiRuleSet',
          priority: 10,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesSQLiRuleSet',
            },
          },
          visibilityConfig: {
            cloudWatchMetricsEnabled: true,
            metricName: 'AWSManagedRulesSQLiRuleSet',
            sampledRequestsEnabled: true,
          },
        },
      ],
    });
    
    // WAFとALBの関連付け
    new wafv2.CfnWebACLAssociation(this, 'WebACLAssociation', {
      resourceArn: lb.loadBalancerArn,
      webAclArn: webAcl.attrArn,
    });
    
    // CloudFrontディストリビューションの作成（オプション）
    if (domainName) {
      // CloudFront用の証明書を作成
      const cloudfront_certificate = new acm.DnsValidatedCertificate(
        this, 
        'CloudFrontCertificate',
        {
          domainName: domainName,
          hostedZone: route53.HostedZone.fromLookup(this, 'HostedZoneForCloudFront', {
            domainName: domainName.split('.').slice(-2).join('.'), // 親ドメイン名を取得
          }),
          region: 'us-east-1', // CloudFrontは米国東部(バージニア北部)リージョンの証明書を要求
        }
      );
      
      const distribution = new cloudfront.Distribution(this, 'Distribution', {
        defaultBehavior: {
          origin: new origins.LoadBalancerV2Origin(lb, {
            protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
        domainNames: [domainName],
        certificate: cloudfront_certificate,
        enableLogging: true,
        logBucket: new s3.Bucket(this, 'CloudFrontLogsBucket', {
          removalPolicy: cdk.RemovalPolicy.RETAIN,
        }),
        logFilePrefix: 'cloudfront-logs/',
      });
    }
    
    // 出力値の定義
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: lb.loadBalancerDnsName,
      description: 'アプリケーションのロードバランサーDNS',
      exportName: `CalculatorMerger${stageName.charAt(0).toUpperCase() + stageName.slice(1)}LbDns`,
    });
    
    if (domainName) {
      new cdk.CfnOutput(this, 'ApplicationURL', {
        value: `https://${domainName}`,
        description: 'アプリケーションのURL',
        exportName: `CalculatorMerger${stageName.charAt(0).toUpperCase() + stageName.slice(1)}URL`,
      });
    }
    
    new cdk.CfnOutput(this, 'ServiceName', {
      value: service.serviceName,
      description: 'ECS サービス名',
      exportName: `CalculatorMerger${stageName.charAt(0).toUpperCase() + stageName.slice(1)}ServiceName`,
    });
  }
}


