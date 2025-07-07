"""
CalculatorAPIクラスの単体テスト
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open
from src.api.calculator_api import CalculatorAPI


class TestCalculatorAPI:
    """CalculatorAPIクラスのテスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        self.api = CalculatorAPI()
        
        # テスト用のデータ
        self.merged_data = {
            "name": "Merged Estimate",
            "total_cost": {
                "upfront": "50.00",
                "monthly": "100.00",
                "12_months": "1250.00"
            },
            "metadata": {
                "currency": "USD",
                "created_on": "2023-01-01",
                "region": "ap-northeast-1",
                "share_url": "https://calculator.aws/#/estimate?id=12345"
            },
            "services": [
                {
                    "service_name": "AWS Lambda",
                    "region": "ap-northeast-1",
                    "upfront_cost": "0.00",
                    "monthly_cost": "50.00",
                    "yearly_cost": "600.00",
                    "description": "Lambda Service",
                    "config": {
                        "memory": 128,
                        "requests": 1000000
                    }
                }
            ]
        }
    
    @patch("uuid.uuid4")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_merged_estimate(self, mock_file, mock_uuid):
        """合算された見積もりデータからAWS Pricing Calculator形式のデータが生成されることを確認"""
        # UUIDをモック
        mock_uuid.return_value.hex = "abcdef1234567890"
        
        result = self.api.create_merged_estimate(self.merged_data)
        
        # ファイル書き込みの確認
        mock_file.assert_called_once()
        file_handle = mock_file.return_value.__enter__.return_value
        
        # write()への呼び出しがあることを確認
        assert file_handle.write.called
        
        # 返値の確認
        assert "url" in result
        assert "instructions" in result
        assert "filename" in result
        
        # URLが正しい形式であることを確認
        assert result["url"].startswith("https://calculator.aws/#/estimate?id=")
        
        # インポート手順が含まれていることを確認
        assert "JSONファイルをダウンロード" in result["instructions"]
        assert "AWS Pricing Calculator" in result["instructions"]
    
    def test_convert_to_calculator_format(self):
        """内部形式のデータがAWS Pricing Calculator形式に正しく変換されることを確認"""
        result = self.api._convert_to_calculator_format(self.merged_data)
        
        # 基本情報の確認
        assert result["name"] == "Merged Estimate"
        assert result["currency"] == "USD"
        assert result["created"] == "2023-01-01"
        assert result["totalUpfront"] == "50.00"
        assert result["totalMonthly"] == "100.00"
        assert result["totalAnnual"] == "1250.00"
        
        # サービス情報の確認
        assert "groups" in result
        assert "services" in result["groups"]
        assert len(result["groups"]["services"]) == 1
        
        service = result["groups"]["services"][0]
        assert service["name"] == "AWS Lambda"
        assert service["region"] == "ap-northeast-1"
        assert service["upfrontCost"] == "0.00"
        assert service["monthlyCost"] == "50.00"
        assert service["description"] == "Lambda Service"
        assert service["config"]["memory"] == 128
        assert service["config"]["requests"] == 1000000
