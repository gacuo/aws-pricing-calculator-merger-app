import unittest
import json
import tempfile
import os
from src.data.parser import EstimateParser
from src.merger.estimate_merger import EstimateMerger
from src.api.calculator_api import CalculatorAPI

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = EstimateParser()
        self.merger = EstimateMerger()
        self.calculator_api = CalculatorAPI()
        
        # テスト用のダミーデータファイル
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data1 = {
            'name': 'Sample 1',
            'currency': 'USD',
            'services': [
                {
                    'name': 'Amazon EC2',
                    'region': 'us-east-1',
                    'monthlyCost': 100.0,
                    'upfrontCost': 0.0,
                    'description': 'EC2 instances'
                }
            ]
        }
        
        self.sample_data2 = {
            'name': 'Sample 2',
            'currency': 'USD',
            'services': [
                {
                    'name': 'Amazon S3',
                    'region': 'us-east-1',
                    'monthlyCost': 50.0,
                    'upfrontCost': 0.0,
                    'description': 'S3 storage'
                }
            ]
        }
        
        # サンプルファイル作成
        self.sample_file1 = os.path.join(self.temp_dir, 'sample1.json')
        with open(self.sample_file1, 'w') as f:
            json.dump(self.sample_data1, f)
            
        self.sample_file2 = os.path.join(self.temp_dir, 'sample2.json')
        with open(self.sample_file2, 'w') as f:
            json.dump(self.sample_data2, f)

    def tearDown(self):
        # テストファイルの削除
        if os.path.exists(self.sample_file1):
            os.remove(self.sample_file1)
        if os.path.exists(self.sample_file2):
            os.remove(self.sample_file2)
        os.rmdir(self.temp_dir)

    def test_full_integration_flow(self):
        """
        完全な統合テスト: パース → マージ → URL生成 → コスト計算
        """
        # 1. パーサーでJSONからデータを抽出
        estimate_data1 = self.parser.parse_from_json(self.sample_data1)
        estimate_data2 = self.parser.parse_from_json(self.sample_data2)
        
        # データが正しく抽出されていることを確認
        self.assertEqual(estimate_data1['name'], 'Sample 1')
        self.assertEqual(estimate_data2['name'], 'Sample 2')
        
        # 2. データをマージ
        merged_data = self.merger.merge_estimates([estimate_data1, estimate_data2])
        
        # マージ結果の確認
        self.assertIn('name', merged_data)
        self.assertIn('services', merged_data)
        self.assertEqual(len(merged_data['services']), 2)
        
        service_names = [s['name'] for s in merged_data['services']]
        self.assertIn('Amazon EC2', service_names)
        self.assertIn('Amazon S3', service_names)
        
        # 3. マージされたデータからURL生成
        merged_url = self.calculator_api.generate_calculator_url(merged_data)
        self.assertTrue(merged_url.startswith('https://calculator.aws/#/estimate?id='))
        
        # 4. コスト計算
        total_cost = self.calculator_api.calculate_total_cost(merged_data)
        self.assertEqual(total_cost['monthly'], '150.00 USD')  # 100 + 50
        self.assertEqual(total_cost['upfront'], '0.00 USD')
        self.assertEqual(total_cost['12_months'], '1,800.00 USD')  # 150 * 12
        
        # 5. エクスポート
        csv_path = self.calculator_api.export_to_csv(merged_data, 'test-export', self.temp_dir)
        self.assertTrue(os.path.exists(csv_path))
        
        # ファイル削除
        os.remove(csv_path)

    def test_url_to_merged_estimate_flow(self):
        """
        URLからデータを取得し、マージするフロー
        """
        # 1. URLからデータを抽出（モック機能を使用）
        estimate_data1 = self.parser.parse_from_url('https://calculator.aws/#/estimate?id=123456abcdef')
        estimate_data2 = self.parser.parse_from_url('https://calculator.aws/#/estimate?id=fedcba654321')
        
        # データが正しく抽出されていることを確認
        self.assertIsInstance(estimate_data1, dict)
        self.assertIsInstance(estimate_data2, dict)
        self.assertIn('services', estimate_data1)
        self.assertIn('services', estimate_data2)
        
        # 2. データをマージ
        merged_data = self.merger.merge_estimates([estimate_data1, estimate_data2])
        
        # マージ結果の確認
        self.assertIn('name', merged_data)
        self.assertIn('services', merged_data)
        
        # 3. マージされたデータからURL生成
        merged_url = self.calculator_api.generate_calculator_url(merged_data)
        self.assertTrue(merged_url.startswith('https://calculator.aws/#/estimate?id='))
        
        # 4. コスト計算
        total_cost = self.calculator_api.calculate_total_cost(merged_data)
        self.assertIn('monthly', total_cost)
        self.assertIn('upfront', total_cost)
        self.assertIn('12_months', total_cost)

if __name__ == '__main__':
    unittest.main()
