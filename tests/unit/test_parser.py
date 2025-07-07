import unittest
from unittest.mock import patch, MagicMock
import json
from src.data.parser import EstimateParser

class TestEstimateParser(unittest.TestCase):
    def setUp(self):
        self.parser = EstimateParser()
        self.valid_url = "https://calculator.aws/#/estimate?id=123456abcdef"
        self.invalid_url = "https://example.com/calculator"
        self.valid_json = {
            'name': 'Test Estimate',
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
        self.invalid_json = {
            'name': 'Invalid Estimate',
            'currency': 'USD'
            # 'services' が存在しない
        }

    def test_parse_from_url_valid(self):
        result = self.parser.parse_from_url(self.valid_url)
        self.assertIsInstance(result, dict)
        self.assertIn('name', result)
        self.assertIn('services', result)
        self.assertIsInstance(result['services'], list)
        self.assertGreater(len(result['services']), 0)

    def test_parse_from_url_invalid(self):
        with self.assertRaises(ValueError):
            self.parser.parse_from_url(self.invalid_url)

    def test_parse_from_url_invalid_format(self):
        invalid_url = "https://calculator.aws/something"
        with self.assertRaises(ValueError):
            self.parser.parse_from_url(invalid_url)

    def test_parse_from_url_no_id(self):
        invalid_url = "https://calculator.aws/#/estimate"
        with self.assertRaises(ValueError):
            self.parser.parse_from_url(invalid_url)

    def test_parse_from_json_valid(self):
        result = self.parser.parse_from_json(self.valid_json)
        self.assertEqual(result['name'], 'Test Estimate')
        self.assertEqual(len(result['services']), 1)
        self.assertEqual(result['services'][0]['name'], 'Amazon EC2')

    def test_parse_from_json_invalid(self):
        with self.assertRaises(ValueError):
            self.parser.parse_from_json(self.invalid_json)

    def test_parse_from_json_not_dict(self):
        with self.assertRaises(ValueError):
            self.parser.parse_from_json("not a dict")

    def test_normalize_data_empty_name(self):
        data = {
            'services': [
                {'name': '', 'monthlyCost': 100}
            ]
        }
        result = self.parser._normalize_data(data)
        self.assertEqual(result['name'], 'Unnamed Estimate')
        self.assertEqual(result['services'][0]['name'], 'Unknown Service')

    def test_normalize_data_missing_region(self):
        data = {
            'name': 'Test',
            'services': [
                {'name': 'Service', 'monthlyCost': 100}
            ]
        }
        result = self.parser._normalize_data(data)
        self.assertEqual(result['services'][0]['region'], 'us-east-1')

    def test_normalize_data_cost_conversion(self):
        data = {
            'name': 'Test',
            'services': [
                {
                    'name': 'Service',
                    'monthlyCost': '$100.50',
                    'upfrontCost': '200.75 USD'
                }
            ]
        }
        result = self.parser._normalize_data(data)
        self.assertEqual(result['services'][0]['monthlyCost'], 100.5)
        self.assertEqual(result['services'][0]['upfrontCost'], 200.75)

    def test_normalize_data_missing_costs(self):
        data = {
            'name': 'Test',
            'services': [
                {'name': 'Service'}
            ]
        }
        result = self.parser._normalize_data(data)
        self.assertEqual(result['services'][0]['monthlyCost'], 0.0)
        self.assertEqual(result['services'][0]['upfrontCost'], 0.0)

    def test_create_mock_data(self):
        mock_data = self.parser._create_mock_data("123456abcdef")
        self.assertIn('name', mock_data)
        self.assertIn('currency', mock_data)
        self.assertIn('services', mock_data)
        self.assertGreater(len(mock_data['services']), 0)
        self.assertEqual(mock_data['currency'], 'USD')

if __name__ == '__main__':
    unittest.main()
