"""
見積もりデータ解析モジュール

AWS Pricing CalculatorのURLやJSONデータから必要なデータを抽出するクラスを提供します。
"""

import re
import json
import base64
import zlib
import logging
import requests
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class EstimateParser:
    """
    AWS Pricing Calculator見積もりデータの解析を行うクラス
    
    このクラスは、以下の機能を提供します：
    - URLからの見積もりデータ抽出
    - JSONデータの解析と正規化
    """
    
    def __init__(self):
        """初期化"""
        self.calculator_base_url = "https://calculator.aws/"
        
    def parse_from_url(self, url: str) -> Dict[str, Any]:
        """
        AWS Pricing Calculator URLから見積もりデータを抽出する
        
        Args:
            url: AWS Pricing Calculator見積もりURL
            
        Returns:
            Dict: 抽出された見積もりデータ
            
        Raises:
            ValueError: URLが無効な場合
        """
        # URLの検証
        if not url.startswith(self.calculator_base_url):
            raise ValueError(f"無効なAWS Pricing Calculator URL: {url}")
        
        # URLからIDを抽出
        parsed_url = urlparse(url)
        
        # URLフォーマットの検証
        if not parsed_url.fragment or 'estimate' not in parsed_url.fragment:
            raise ValueError(f"無効なAWS Pricing Calculator URL形式: {url}")
        
        # フラグメント部分からクエリパラメータを抽出
        fragment = parsed_url.fragment.split('?')
        if len(fragment) != 2:
            raise ValueError(f"URLにIDパラメータがありません: {url}")
        
        # クエリパラメータからIDを抽出
        query_params = parse_qs(fragment[1])
        if 'id' not in query_params or not query_params['id']:
            raise ValueError(f"URLにIDパラメータがありません: {url}")
        
        estimate_id = query_params['id'][0]
        logger.info(f"見積もりID: {estimate_id}")
        
        # 通常、このIDを使用してAWS Pricing CalculatorのAPIから
        # 見積もりデータをフェッチします
        # ここではモックデータを返します
        
        # モックデータの作成
        mock_data = self._create_mock_data(estimate_id)
        
        return mock_data
    
    def parse_from_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSONデータから見積もりデータを抽出する
        
        Args:
            json_data: 見積もりデータを含むJSON
            
        Returns:
            Dict: 正規化された見積もりデータ
        """
        if not isinstance(json_data, dict):
            raise ValueError("無効なJSON形式です")
        
        # データの検証
        if 'services' not in json_data or not isinstance(json_data['services'], list):
            raise ValueError("サービスデータが含まれていません")
        
        # データの正規化
        normalized_data = self._normalize_data(json_data)
        
        return normalized_data
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        見積もりデータを正規化する
        
        Args:
            data: 見積もりデータ
            
        Returns:
            Dict: 正規化されたデータ
        """
        # 必須フィールドの確認と追加
        if 'name' not in data or not data['name']:
            data['name'] = 'Unnamed Estimate'
            
        # サービスデータの正規化
        for service in data.get('services', []):
            # 必須フィールドの確認と追加
            if 'name' not in service or not service['name']:
                service['name'] = 'Unknown Service'
                
            if 'region' not in service:
                service['region'] = 'us-east-1'  # デフォルトリージョン
                
            # コスト値の数値化
            if 'monthlyCost' in service and not isinstance(service['monthlyCost'], (int, float)):
                try:
                    # 通貨記号などを除去して数値に変換
                    cost_str = service['monthlyCost']
                    if isinstance(cost_str, str):
                        cost_str = re.sub(r'[^\d.]', '', cost_str)
                        service['monthlyCost'] = float(cost_str) if cost_str else 0.0
                    else:
                        service['monthlyCost'] = 0.0
                except (ValueError, TypeError):
                    service['monthlyCost'] = 0.0
                    
            if 'upfrontCost' in service and not isinstance(service['upfrontCost'], (int, float)):
                try:
                    # 通貨記号などを除去して数値に変換
                    cost_str = service['upfrontCost']
                    if isinstance(cost_str, str):
                        cost_str = re.sub(r'[^\d.]', '', cost_str)
                        service['upfrontCost'] = float(cost_str) if cost_str else 0.0
                    else:
                        service['upfrontCost'] = 0.0
                except (ValueError, TypeError):
                    service['upfrontCost'] = 0.0
                    
            # 存在しないフィールドのデフォルト値設定
            if 'monthlyCost' not in service:
                service['monthlyCost'] = 0.0
                
            if 'upfrontCost' not in service:
                service['upfrontCost'] = 0.0
                
        return data
    
    def _create_mock_data(self, estimate_id: str) -> Dict[str, Any]:
        """
        モック見積もりデータを作成する
        
        Args:
            estimate_id: 見積もりID
            
        Returns:
            Dict: モック見積もりデータ
        """
        # IDの一部を使用して一貫性のあるモックデータを生成
        id_seed = int(estimate_id[:6], 16) % 1000
        service_count = (id_seed % 5) + 1  # 1～5個のサービス
        
        services = []
        for i in range(service_count):
            # サービス種類をIDから決定
            service_type = ['EC2', 'S3', 'RDS', 'Lambda', 'DynamoDB'][i % 5]
            region = ['us-east-1', 'us-west-2', 'ap-northeast-1', 'eu-central-1'][id_seed % 4]
            
            # コストをIDから計算
            monthly_cost = (id_seed * (i + 1)) % 1000 + 10
            upfront_cost = id_seed % 200 if service_type == 'EC2' else 0
            
            service = {
                'name': f"Amazon {service_type}",
                'region': region,
                'monthlyCost': float(monthly_cost),
                'upfrontCost': float(upfront_cost),
                'description': f"{service_type} service in {region}",
                'config': {
                    'serviceCode': service_type.lower(),
                    'instanceType': f"{service_type.lower()}.large" if service_type == 'EC2' else None,
                    'storageGB': 100 if service_type in ['S3', 'RDS'] else None
                }
            }
            services.append(service)
        
        # 見積もりデータの作成
        mock_data = {
            'name': f"Estimate-{estimate_id[:8]}",
            'currency': 'USD',
            'services': services
        }
        
        return mock_data
