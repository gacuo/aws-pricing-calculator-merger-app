"""
EstimateMergerクラスの単体テスト
"""

import pytest
from src.merger.cost_merger import EstimateMerger


class TestEstimateMerger:
    """EstimateMergerクラスのテスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        self.merger = EstimateMerger()
        
        # テスト用のデータ
        self.estimate1 = {
            "name": "Estimate 1",
            "total_cost": {
                "upfront": "100.00",
                "monthly": "200.00",
                "12_months": "2500.00"
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
                    "description": "Test Lambda",
                    "config": {
                        "memory": 128,
                        "requests": 1000000
                    }
                },
                {
                    "service_name": "Amazon S3",
                    "region": "ap-northeast-1",
                    "upfront_cost": "0.00",
                    "monthly_cost": "30.00",
                    "yearly_cost": "360.00",
                    "description": "Storage",
                    "config": {
                        "storage": "100GB"
                    }
                }
            ]
        }
        
        self.estimate2 = {
            "name": "Estimate 2",
            "total_cost": {
                "upfront": "50.00",
                "monthly": "100.00",
                "12_months": "1250.00"
            },
            "metadata": {
                "currency": "USD",
                "created_on": "2023-01-02",
                "region": "ap-northeast-1",
                "share_url": "https://calculator.aws/#/estimate?id=67890"
            },
            "services": [
                {
                    "service_name": "AWS Lambda",
                    "region": "ap-northeast-1",
                    "upfront_cost": "0.00",
                    "monthly_cost": "25.00",
                    "yearly_cost": "300.00",
                    "description": "Another Lambda",
                    "config": {
                        "memory": 256,
                        "requests": 500000
                    }
                },
                {
                    "service_name": "Amazon EC2",
                    "region": "ap-northeast-1",
                    "upfront_cost": "50.00",
                    "monthly_cost": "75.00",
                    "yearly_cost": "950.00",
                    "description": "Compute",
                    "config": {
                        "instance_type": "t3.micro"
                    }
                }
            ]
        }
    
    def test_merge_estimates_empty_list(self):
        """空のリストを渡すとValueErrorが発生することを確認"""
        with pytest.raises(ValueError):
            self.merger.merge_estimates([])
    
    def test_merge_estimates_single_estimate(self):
        """単一の見積もりを渡すと、そのまま返されることを確認"""
        result = self.merger.merge_estimates([self.estimate1])
        assert result == self.estimate1
    
    def test_merge_estimates_multiple(self):
        """複数の見積もりが正しく合算されることを確認"""
        result = self.merger.merge_estimates([self.estimate1, self.estimate2])
        
        # 見積もり名の確認
        assert "Merged:" in result["name"]
        assert "Estimate 1" in result["name"]
        assert "Estimate 2" in result["name"]
        
        # メタデータは最初の見積もりのものが使用されることを確認
        assert result["metadata"]["created_on"] == "2023-01-01"
        assert result["metadata"]["share_url"] == "https://calculator.aws/#/estimate?id=12345"
        
        # サービス数の確認 (AWS Lambda, Amazon S3, Amazon EC2)
        assert len(result["services"]) == 3
        
        # AWS Lambdaのコストが合算されていることを確認
        lambda_service = next(s for s in result["services"] if s["service_name"] == "AWS Lambda")
        assert float(lambda_service["monthly_cost"].replace(",", "")) == 75.0  # 50.00 + 25.00
        
        # 説明が統合されていることを確認
        assert "Test Lambda" in lambda_service["description"]
        assert "Another Lambda" in lambda_service["description"]
        
        # 設定が統合されていることを確認
        assert lambda_service["config"]["memory"] == [128, 256]
        assert lambda_service["config"]["requests"] == [1000000, 500000]
        
        # 合計コストの確認
        assert float(result["total_cost"]["upfront"].replace(",", "")) == 50.0  # 0.00 + 50.00
        assert float(result["total_cost"]["monthly"].replace(",", "")) == 180.0  # 50.00 + 30.00 + 25.00 + 75.00
    
    def test_merge_services(self):
        """同一サービスのデータが正しく合算されることを確認"""
        service1 = {
            "service_name": "AWS Lambda",
            "region": "ap-northeast-1",
            "upfront_cost": "10.00",
            "monthly_cost": "20.00",
            "yearly_cost": "250.00",
            "description": "Service 1",
            "config": {"key1": "value1", "common": "common1"}
        }
        
        service2 = {
            "service_name": "AWS Lambda",
            "region": "ap-northeast-1",
            "upfront_cost": "5.00",
            "monthly_cost": "15.00",
            "yearly_cost": "185.00",
            "description": "Service 2",
            "config": {"key2": "value2", "common": "common2"}
        }
        
        result = self.merger._merge_services([service1, service2])
        
        # コストの合算を確認
        assert float(result["upfront_cost"].replace(",", "")) == 15.0  # 10.00 + 5.00
        assert float(result["monthly_cost"].replace(",", "")) == 35.0  # 20.00 + 15.00
        assert float(result["yearly_cost"].replace(",", "")) == 435.0  # 250.00 + 185.00
        
        # 説明の統合を確認
        assert "Service 1, Service 2" in result["description"] or "Service 2, Service 1" in result["description"]
        
        # 設定の統合を確認
        assert result["config"]["key1"] == "value1"
        assert result["config"]["key2"] == "value2"
        assert result["config"]["common"] == ["common1", "common2"]
