"""
統合テスト

EstimateParser, EstimateMerger, CalculatorAPIの連携を検証します。
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open
from src.data.parser import EstimateParser
from src.merger.cost_merger import EstimateMerger
from src.api.calculator_api import CalculatorAPI


class TestIntegration:
    """統合テスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        self.parser = EstimateParser()
        self.merger = EstimateMerger()
        self.api = CalculatorAPI()
        
        # テスト用のJSONデータ
        self.sample_data1 = {
            "name": "Estimate 1",
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
                        "description": "Lambda 1",
                        "config": {
                            "memory": 128,
                            "requests": 1000000
                        }
                    }
                ]
            }
        }
        
        self.sample_data2 = {
            "name": "Estimate 2",
            "totalUpfront": "50.00",
            "totalMonthly": "100.00",
            "totalAnnual": "1250.00",
            "currency": "USD",
            "created": "2023-01-02",
            "region": "ap-northeast-1",
            "shareUrl": "https://calculator.aws/#/estimate?id=67890",
            "groups": {
                "services": [
                    {
                        "name": "AWS Lambda",
                        "region": "ap-northeast-1",
                        "upfrontCost": "0.00",
                        "monthlyCost": "25.00",
                        "description": "Lambda 2",
                        "config": {
                            "memory": 256,
                            "requests": 500000
                        }
                    },
                    {
                        "name": "Amazon S3",
                        "region": "ap-northeast-1",
                        "upfrontCost": "0.00",
                        "monthlyCost": "10.00",
                        "description": "Storage",
                        "config": {
                            "storage": "10GB"
                        }
                    }
                ]
            }
        }
    
    def test_end_to_end_flow(self):
        """Parser -> Merger -> API の統合フローをテスト"""
        # EstimateParserを使用してデータを構造化
        data1 = self.parser._structure_estimate_data(self.sample_data1)
        data2 = self.parser._structure_estimate_data(self.sample_data2)
        
        # データの構造化が正しく行われていることを確認
        assert data1["name"] == "Estimate 1"
        assert data2["name"] == "Estimate 2"
        
        # EstimateMergerを使用してデータを合算
        merged_data = self.merger.merge_estimates([data1, data2])
        
        # 合算が正しく行われていることを確認
        assert "Merged:" in merged_data["name"]
        assert len(merged_data["services"]) == 2  # Lambda (合算済) + S3
        
        lambda_service = next(s for s in merged_data["services"] if s["service_name"] == "AWS Lambda")
        assert float(lambda_service["monthly_cost"].replace(",", "")) == 75.0  # 50.00 + 25.00
        
        # CalculatorAPIを使用してAWS Pricing Calculator形式に変換
        with patch("uuid.uuid4") as mock_uuid, patch("builtins.open", mock_open()) as mock_file:
            mock_uuid.return_value.hex = "abcdef1234567890"
            
            result = self.api.create_merged_estimate(merged_data)
            
            # 変換が正しく行われていることを確認
            assert "url" in result
            assert result["url"].startswith("https://calculator.aws/#/estimate?id=")
            assert "instructions" in result
            assert "filename" in result
    
    def test_parser_merger_integration(self):
        """ParserとMergerの連携をテスト"""
        # EstimateParserを使用してデータを構造化
        data1 = self.parser._structure_estimate_data(self.sample_data1)
        data2 = self.parser._structure_estimate_data(self.sample_data2)
        
        # EstimateMergerを使用してデータを合算
        merged_data = self.merger.merge_estimates([data1, data2])
        
        # 合算が正しく行われていることを確認
        assert merged_data["total_cost"]["monthly"] == "85.00"  # 50.00 + 25.00 + 10.00
        assert len(merged_data["services"]) == 2  # Lambda (合算済) + S3
        
        # AWS Lambdaサービスが合算されていることを確認
        lambda_service = next(s for s in merged_data["services"] if s["service_name"] == "AWS Lambda")
        assert "Lambda 1" in lambda_service["description"]
        assert "Lambda 2" in lambda_service["description"]
        assert lambda_service["config"]["memory"] == [128, 256]
        
        # Amazon S3サービスがそのまま含まれていることを確認
        s3_service = next(s for s in merged_data["services"] if s["service_name"] == "Amazon S3")
        assert s3_service["description"] == "Storage"
        assert s3_service["config"]["storage"] == "10GB"
