import unittest
from src.merger.estimate_merger import EstimateMerger

class TestEstimateMerger(unittest.TestCase):
    def setUp(self):
        self.merger = EstimateMerger()
        self.estimate1 = {
            'name': 'Estimate 1',
            'currency': 'USD',
            'services': [
                {
                    'name': 'Amazon EC2',
                    'region': 'us-east-1',
                    'monthlyCost': 100.0,
                    'upfrontCost': 50.0,
                    'description': 'EC2 instances',
                    'config': {
                        'instanceType': 't3.large',
                        'count': 2
                    }
                },
                {
                    'name': 'Amazon S3',
                    'region': 'us-east-1',
                    'monthlyCost': 30.0,
                    'upfrontCost': 0.0,
                    'description': 'S3 storage',
                    'config': {
                        'storage': {
                            'totalGB': 100,
                            'standardGB': 100
                        }
                    }
                }
            ]
        }
        self.estimate2 = {
            'name': 'Estimate 2',
            'currency': 'USD',
            'services': [
                {
                    'name': 'Amazon EC2',
                    'region': 'us-east-1',
                    'monthlyCost': 200.0,
                    'upfrontCost': 100.0,
                    'description': 'EC2 instances',
                    'config': {
                        'instanceType': 't3.xlarge',
                        'count': 1
                    }
                },
                {
                    'name': 'Amazon RDS',
                    'region': 'us-east-1',
                    'monthlyCost': 150.0,
                    'upfrontCost': 0.0,
                    'description': 'RDS instances',
                    'config': {
                        'instanceType': 'db.t3.large',
                        'count': 1,
                        'storageGB': 100
                    }
                }
            ]
        }

    def test_merge_estimates_empty(self):
        with self.assertRaises(ValueError):
            self.merger.merge_estimates([])

    def test_merge_estimates_single(self):
        result = self.merger.merge_estimates([self.estimate1])
        self.assertEqual(result, self.estimate1)

    def test_merge_estimates_multiple(self):
        result = self.merger.merge_estimates([self.estimate1, self.estimate2])
        self.assertIn('name', result)
        self.assertIn('currency', result)
        self.assertIn('services', result)
        
        # 合算後のサービス数の確認（EC2は統合されるので3つ）
        self.assertEqual(len(result['services']), 3)
        
        # サービス名によるグループ化の確認
        service_names = [s['name'] for s in result['services']]
        self.assertIn('Amazon EC2', service_names)
        self.assertIn('Amazon S3', service_names)
        self.assertIn('Amazon RDS', service_names)

    def test_generate_merged_name(self):
        name = self.merger._generate_merged_name([self.estimate1, self.estimate2])
        self.assertEqual(name, "Merged: Estimate 1 + Estimate 2")
        
        # 3つ以上の場合
        name = self.merger._generate_merged_name([self.estimate1, self.estimate2, {'name': 'Estimate 3'}])
        self.assertEqual(name, "Merged: Estimate 1 + 2 others")

    def test_get_common_currency(self):
        currency = self.merger._get_common_currency([self.estimate1, self.estimate2])
        self.assertEqual(currency, "USD")
        
        # 複数の通貨がある場合
        estimate3 = {'currency': 'JPY'}
        currency = self.merger._get_common_currency([self.estimate1, estimate3])
        self.assertEqual(currency, "USD")  # デフォルトはUSD

    def test_merge_services(self):
        services = self.merger._merge_services([self.estimate1, self.estimate2])
        self.assertEqual(len(services), 3)
        
        # EC2サービスのコストが合算されているか確認
        ec2_service = next((s for s in services if s['name'] == 'Amazon EC2'), None)
        self.assertIsNotNone(ec2_service)
        self.assertEqual(ec2_service['monthlyCost'], 300.0)  # 100 + 200
        self.assertEqual(ec2_service['upfrontCost'], 150.0)  # 50 + 100

    def test_merge_service_group(self):
        services = [
            {
                'name': 'Amazon EC2',
                'region': 'us-east-1',
                'monthlyCost': 100.0,
                'upfrontCost': 50.0,
                'description': 'EC2 instances',
            },
            {
                'name': 'Amazon EC2',
                'region': 'us-east-1',
                'monthlyCost': 200.0,
                'upfrontCost': 100.0,
                'description': 'More EC2 instances',
            }
        ]
        
        result = self.merger._merge_service_group(services)
        self.assertEqual(result['name'], 'Amazon EC2')
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['monthlyCost'], 300.0)
        self.assertEqual(result['upfrontCost'], 150.0)
        self.assertIn('Combined:', result['description'])

    def test_merge_configs(self):
        # EC2設定のマージ
        ec2_configs = [
            {
                'instanceType': 't3.large',
                'count': 2
            },
            {
                'instanceType': 't3.xlarge',
                'count': 1
            }
        ]
        
        merged = self.merger._merge_configs(ec2_configs, 'Amazon EC2')
        self.assertEqual(merged['serviceCode'], 'ec2')
        self.assertIn('t3.large', merged['instances'])
        self.assertIn('t3.xlarge', merged['instances'])
        self.assertEqual(merged['instances']['t3.large']['count'], 2)
        self.assertEqual(merged['instances']['t3.xlarge']['count'], 1)
        
        # S3設定のマージ
        s3_configs = [
            {
                'storage': {
                    'totalGB': 100,
                    'standardGB': 100
                }
            },
            {
                'storage': {
                    'totalGB': 200,
                    'glacierGB': 100
                }
            }
        ]
        
        merged = self.merger._merge_configs(s3_configs, 'Amazon S3')
        self.assertEqual(merged['serviceCode'], 's3')
        self.assertEqual(merged['storage']['totalGB'], 300)
        self.assertEqual(merged['storage']['standardGB'], 100)
        self.assertEqual(merged['storage']['glacierGB'], 100)

if __name__ == '__main__':
    unittest.main()
