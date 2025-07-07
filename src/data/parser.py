"""
AWS Pricing Calculator データ解析モジュール

AWS Pricing Calculatorの見積もりURLやJSONデータを解析します。
"""

import re
import json
import requests
from typing import Dict, List, Any, Union, Optional


class EstimateParser:
    """AWS Pricing Calculator見積もりデータの解析を行うクラス"""
    
    def __init__(self):
        """初期化"""
        # AWS Pricing Calculator URLの正規表現パターン
        self.calculator_url_pattern = re.compile(
            r"https://calculator\.aws/#/estimate\?id=[a-zA-Z0-9]+"
        )
        
    def validate_calculator_url(self, url: str) -> bool:
        """
        AWS Pricing CalculatorのURLが有効かどうかを検証します
        
        Args:
            url: 検証するURL
            
        Returns:
            bool: URLが有効な形式の場合はTrue、そうでない場合はFalse
        """
        return bool(self.calculator_url_pattern.match(url))
    
    def parse_estimate_url(self, url: str) -> Dict[str, Any]:
        """
        AWS Pricing Calculator見積もりURLからデータを取得して構造化します
        
        Args:
            url: AWS Pricing Calculator見積もりURL
            
        Returns:
            Dict: 構造化された見積もりデータ
            
        Raises:
            ValueError: URLが無効な場合
            ConnectionError: データの取得に失敗した場合
        """
        # URLを検証
        if not self.validate_calculator_url(url):
            raise ValueError(f"無効なAWS Pricing Calculator URL: {url}")
        
        # URLからIDを抽出
        estimate_id = url.split("id=")[1]
        
        # 見積もりデータを取得
        # 注: 実際のAWS Pricing CalculatorのAPIは公開されていないため、
        # ここではサンプルデータを読み込む実装としています
        try:
            # サンプル実装: 本来はAPIからデータを取得
            # 実際の実装では、AWS Pricing CalculatorのAPIを使用することになります
            with open("json_samples/sample1.json", "r", encoding="utf-8") as file:
                raw_data = json.load(file)
            
            # データを構造化
            return self._structure_estimate_data(raw_data)
            
        except Exception as e:
            raise ConnectionError(f"見積もりデータの取得に失敗しました: {str(e)}")
    
    def _structure_estimate_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生のJSONデータから必要な情報を抽出して構造化します
        
        Args:
            raw_data: AWS Pricing Calculatorから取得した生のJSONデータ
            
        Returns:
            Dict: 構造化された見積もりデータ
        """
        # 見積もり名
        name = raw_data.get("name", "Untitled Estimate")
        
        # 合計コスト
        total_cost = {
            "upfront": raw_data.get("totalUpfront", "0.00"),
            "monthly": raw_data.get("totalMonthly", "0.00"),
            "12_months": raw_data.get("totalAnnual", "0.00")
        }
        
        # メタデータ
        metadata = {
            "currency": raw_data.get("currency", "USD"),
            "created_on": raw_data.get("created", ""),
            "region": raw_data.get("region", ""),
            "share_url": raw_data.get("shareUrl", "")
        }
        
        # サービス
        services = []
        groups = raw_data.get("groups", {})
        services_list = groups.get("services", [])
        
        for service in services_list:
            service_data = {
                "service_name": service.get("name", ""),
                "region": service.get("region", ""),
                "upfront_cost": service.get("upfrontCost", "0.00"),
                "monthly_cost": service.get("monthlyCost", "0.00"),
                "yearly_cost": service.get("yearlyCost", "0.00"),
                "description": service.get("description", ""),
                "config": service.get("config", {})
            }
            services.append(service_data)
        
        # 構造化されたデータを返す
        return {
            "name": name,
            "total_cost": total_cost,
            "metadata": metadata,
            "services": services
        }
