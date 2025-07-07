"""
AWS Pricing Calculator データパーサーモジュール

このモジュールは、AWS Pricing Calculatorの見積もりデータを解析し、
構造化されたデータとして提供します。
"""

import json
import logging
from src.api.calculator_api import CalculatorAPI

logger = logging.getLogger(__name__)

class EstimateParser:
    """AWS Pricing Calculator 見積もりデータパーサー"""
    
    def __init__(self):
        self.calculator_api = CalculatorAPI()
    
    def parse_estimate_url(self, url):
        """見積もりURLからデータを解析する"""
        try:
            # APIを使用して見積もりデータを取得
            raw_data = self.calculator_api.get_estimate_data(url)
            
            # データの検証と構造化
            return self._structure_estimate_data(raw_data)
        
        except Exception as e:
            logger.error(f"見積もりURLの解析に失敗しました: {url}, エラー: {str(e)}")
            raise
    
    def _structure_estimate_data(self, raw_data):
        """取得した生データを構造化する"""
        # この関数は、APIから取得した生データを
        # アプリケーション内で使いやすい形式に変換します
        
        structured_data = {
            "estimate_id": raw_data.get("estimate_id", ""),
            "name": raw_data.get("name", "無名の見積もり"),
            "total_cost": {
                "monthly": float(raw_data.get("total_cost", {}).get("monthly", "0.0")),
                "upfront": float(raw_data.get("total_cost", {}).get("upfront", "0.0")),
                "12_months": float(raw_data.get("total_cost", {}).get("12_months", "0.0")),
            },
            "services": []
        }
        
        # サービスデータの構造化
        for service in raw_data.get("services", []):
            structured_service = {
                "name": service.get("name", ""),
                "description": service.get("description", ""),
                "region": service.get("region", ""),
                "cost": {
                    "monthly": float(service.get("cost", {}).get("monthly", "0.0")),
                    "upfront": float(service.get("cost", {}).get("upfront", "0.0")),
                    "12_months": float(service.get("cost", {}).get("12_months", "0.0")),
                }
            }
            structured_data["services"].append(structured_service)
        
        return structured_data
