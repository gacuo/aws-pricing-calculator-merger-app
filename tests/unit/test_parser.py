"""
EstimateParserクラスの単体テスト
"""

import pytest
import json
from unittest.mock import mock_open, patch
from src.data.parser import EstimateParser


class TestEstimateParser:
    """EstimateParserクラスのテスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        self.parser = EstimateParser()
        
        # テスト用のJSONデータ
        self.sample_data = {
            "name": "Test Estimate",
            "totalUpfront": "100.00",
            "totalMonthly": "200.00",
            "totalAnnual": "2500.00",
            "currency": "USD",
            "created": "2023-01-01",
            "region": "ap-northeast-1",
            "shareUrl": "https://calculator.aws/#/estimate?id=12345",
            "groups": {
                "services": [
                    {
                        "name": "AWS Lambda",
                        "region": "ap-northeast-1",
                        "upfrontCost": "0.00",
                        "monthlyCost": "50.00",
                        "description": "Test Lambda",
                        "config": {
                            "memory": 128,
                            "requests": 1000000
                        }
                    }
                ]
            }
        }
        
    def test_validate_calculator_url_valid(self):
        """有効なURLを検証できることを確認"""
        valid_url = "https://calculator.aws/#/estimate?id=12345abcdef"
        assert self.parser.validate_calculator_url(valid_url) is True
    
    def test_validate_calculator_url_invalid(self):
        """無効なURLを検証できることを確認"""
        invalid_urls = [
            "https://example.com",
            "https://calculator.aws/",
            "https://calculator.aws/#/",
            "https://calculator.aws/#/estimate",
            "https://calculator.aws/#/estimate?",
            "https://calculator.aws/#/estimate?id=",
        ]
        
        for url in invalid_urls:
            assert self.parser.validate_calculator_url(url) is False
    
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"name": "Test"}))
    def test_parse_estimate_url_invalid_url(self, mock_file):
        """無効なURLを渡すとValueErrorが発生することを確認"""
        with pytest.raises(ValueError):
            self.parser.parse_estimate_url("https://invalid.url")
    
    @patch("builtins.open")
    def test_structure_estimate_data(self, mock_file):
        """JSONデータから必要な情報を正しく抽出できることを確認"""
        structured_data = self.parser._structure_estimate_data(self.sample_data)
        
        assert structured_data["name"] == "Test Estimate"
        assert structured_data["total_cost"]["upfront"] == "100.00"
        assert structured_data["total_cost"]["monthly"] == "200.00"
        assert structured_data["total_cost"]["12_months"] == "2500.00"
        assert structured_data["metadata"]["currency"] == "USD"
        assert structured_data["metadata"]["created_on"] == "2023-01-01"
        assert structured_data["metadata"]["region"] == "ap-northeast-1"
        assert structured_data["metadata"]["share_url"] == "https://calculator.aws/#/estimate?id=12345"
        
        assert len(structured_data["services"]) == 1
        service = structured_data["services"][0]
        assert service["service_name"] == "AWS Lambda"
        assert service["region"] == "ap-northeast-1"
        assert service["upfront_cost"] == "0.00"
        assert service["monthly_cost"] == "50.00"
        assert service["description"] == "Test Lambda"
        assert service["config"]["memory"] == 128
        assert service["config"]["requests"] == 1000000
