import unittest
from unittest.mock import patch, MagicMock
import json
import os
from src.api.calculator_api import CalculatorAPI

class TestCalculatorAPI(unittest.TestCase):
    def setUp(self):
        self.calculator_api = CalculatorAPI()
        self.test_data = {
            'name': 'Test Estimate',
            'currency': 'USD',
            'services': [
                {
                    'name': 'Amazon EC2',
                    'region': 'us-east-1',
                    'monthlyCost': 100.0,
                    'upfrontCost': 0.0,
                    'description': 'EC2 instances'
                },
                {
                    'name': 'Amazon S3',
                    'region': 'us-east-1',
                    'monthlyCost': 50.0,
                    'upfrontCost': 0.0,
                    'description': 'S3 storage'
                }
            ]
        }

    def test_generate_calculator_url(self):
        url = self.calculator_api.generate_calculator_url(self.test_data)
        self.assertTrue(url.startswith('https://calculator.aws/#/estimate?id='))
        self.assertGreater(len(url), len('https://calculator.aws/#/estimate?id='))

    def test_calculate_total_cost(self):
        total_cost = self.calculator_api.calculate_total_cost(self.test_data)
        self.assertEqual(total_cost['monthly'], '150.00 USD')
        self.assertEqual(total_cost['upfront'], '0.00 USD')
        self.assertEqual(total_cost['12_months'], '1,800.00 USD')

    def test_calculate_total_cost_empty_services(self):
        data = {'services': []}
        total_cost = self.calculator_api.calculate_total_cost(data)
        self.assertEqual(total_cost['monthly'], '0.00 USD')
        self.assertEqual(total_cost['upfront'], '0.00 USD')
        self.assertEqual(total_cost['12_months'], '0.00 USD')

    def test_calculate_total_cost_error(self):
        with patch.object(self.calculator_api, 'calculate_total_cost', side_effect=Exception('Test error')):
            total_cost = self.calculator_api.calculate_total_cost({})
            self.assertEqual(total_cost['monthly'], '0.00 USD')
            self.assertEqual(total_cost['upfront'], '0.00 USD')
            self.assertEqual(total_cost['12_months'], '0.00 USD')

    def test_extract_services(self):
        services = self.calculator_api.extract_services(self.test_data)
        self.assertEqual(len(services), 2)
        self.assertEqual(services[0]['service_name'], 'Amazon EC2')
        self.assertEqual(services[0]['region'], 'us-east-1')
        self.assertEqual(services[0]['monthly_cost'], '100.00 USD')
        self.assertEqual(services[0]['upfront_cost'], '0.00 USD')

    def test_extract_services_empty(self):
        services = self.calculator_api.extract_services({})
        self.assertEqual(services, [])

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_export_to_csv(self, mock_open):
        result = self.calculator_api.export_to_csv(self.test_data, 'test-id', '/tmp')
        self.assertEqual(result, '/tmp/test-id.csv')
        mock_open.assert_called_once_with('/tmp/test-id.csv', 'w', newline='')

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('src.api.calculator_api.CalculatorAPI.extract_services', side_effect=Exception('Test error'))
    def test_export_to_csv_error(self, mock_extract, mock_open):
        result = self.calculator_api.export_to_csv(self.test_data, 'test-id', '/tmp')
        self.assertEqual(result, '/tmp/test-id.csv')
        mock_open.assert_called()

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_export_to_pdf(self, mock_open):
        result = self.calculator_api.export_to_pdf(self.test_data, 'test-id', '/tmp')
        self.assertEqual(result, '/tmp/test-id.pdf')
        mock_open.assert_called_once_with('/tmp/test-id.pdf', 'w', newline='')

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('src.api.calculator_api.CalculatorAPI.extract_services', side_effect=Exception('Test error'))
    def test_export_to_pdf_error(self, mock_extract, mock_open):
        result = self.calculator_api.export_to_pdf(self.test_data, 'test-id', '/tmp')
        self.assertEqual(result, '/tmp/test-id.pdf')
        mock_open.assert_called()


if __name__ == '__main__':
    unittest.main()
