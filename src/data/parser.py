"""
AWS Pricing Calculator データパーサーモジュール

このモジュールは、AWS Pricing Calculatorの見積もりデータを解析し、
構造化されたデータとして提供します。
"""

import json
import logging
import requests
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class EstimateParser:
    """AWS Pricing Calculator 見積もりデータパーサー"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
    
    def validate_calculator_url(self, url):
        """URLがAWS Pricing Calculatorのエクスポート形式か検証する"""
        if not url:
            return False
            
        pattern = r'^https://calculator\.aws/#/estimate\?id=[a-f0-9]+$'
        import re
        return bool(re.match(pattern, url))
    
    def extract_id_from_url(self, url):
        """URLから見積もりIDを抽出する"""
        parsed_url = urlparse(url)
        
        # fragmentを解析（#/estimate?id=xxx の部分）
        fragment = parsed_url.fragment
        if not fragment:
            return None
        
        # fragment内のクエリパラメータを解析
        query_part = fragment.split('?', 1)[1] if '?' in fragment else ''
        query_params = parse_qs(query_part)
        
        if 'id' in query_params and query_params['id']:
            return query_params['id'][0]
        return None
    
    def parse_estimate_url(self, url):
        """見積もりURLからデータを解析する"""
        try:
            if not self.validate_calculator_url(url):
                logger.error(f"無効なAWS Pricing Calculator URL: {url}")
                raise ValueError(f"無効なAWS Pricing Calculator URL: {url}")
                
            estimate_id = self.extract_id_from_url(url)
            if not estimate_id:
                logger.error(f"URLから見積もりIDを抽出できませんでした: {url}")
                raise ValueError(f"URLから見積もりIDを抽出できませんでした: {url}")
                
            # 実際の実装では、この部分でAWSから直接JSONデータを取得する必要があります
            # 現在のところ、JSONはエクスポート機能を使って手動で取得する必要があるようです
            
            # 開発段階では、サンプルJSONデータを使用
            with open('json_samples/My-Estimate.json', 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
            
            # データの検証と構造化
            return self._structure_estimate_data(raw_data)
            
        except Exception as e:
            logger.error(f"見積もりURLの解析に失敗しました: {url}, エラー: {str(e)}")
            raise
    
    def _structure_estimate_data(self, raw_data):
        """取得した生データを構造化する"""
        
        # メタデータから共有URLを取得
        share_url = raw_data.get("Metadata", {}).get("Share Url", "")
        
        structured_data = {
            "name": raw_data.get("Name", "無名の見積もり"),
            "share_url": share_url,
            "estimate_id": self.extract_id_from_url(share_url) if share_url else "",
            "total_cost": {
                "monthly": float(raw_data.get("Total Cost", {}).get("monthly", "0.0")),
                "upfront": float(raw_data.get("Total Cost", {}).get("upfront", "0.0")),
                "12_months": float(raw_data.get("Total Cost", {}).get("12 months", "0.0")),
            },
            "services": []
        }
        
        # サービスデータの構造化
        services = raw_data.get("Groups", {}).get("Services", [])
        for service in services:
            structured_service = {
                "name": service.get("Service Name", ""),
                "description": service.get("Description", "-"),
                "region": service.get("Region", ""),
                "cost": {
                    "monthly": float(service.get("Service Cost", {}).get("monthly", "0.0")),
                    "upfront": float(service.get("Service Cost", {}).get("upfront", "0.0")),
                    "12_months": float(service.get("Service Cost", {}).get("12 months", "0.0")),
                },
                "properties": service.get("Properties", {})
            }
            structured_data["services"].append(structured_service)
        
        return structured_data
