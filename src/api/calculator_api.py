"""
AWS Pricing Calculator APIモジュール

このモジュールはAWS Pricing CalculatorのAPIとの連携を担当します。
見積もりURLからデータを取得し、新しい見積もりURLを生成する機能を提供します。
"""

import requests
import json
import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


class CalculatorAPI:
    """AWS Pricing Calculator API操作クラス"""
    
    BASE_URL = "https://calculator.aws"
    ESTIMATE_PATH = "/#/estimate"
    
    def __init__(self):
        self.session = requests.Session()
        # 必要に応じてユーザーエージェントやヘッダーを設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
    
    def validate_calculator_url(self, url):
        """URLがAWS Pricing Calculatorのエクスポート形式か検証する"""
        if not url:
            return False
            
        pattern = r'^https://calculator\.aws/#/estimate\?id=[a-f0-9]+$'
        return bool(re.match(pattern, url))
    
    def extract_id_from_url(self, url):
        """URLから見積もりIDを抽出する"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.fragment.split('?')[1] if '?' in parsed_url.fragment else '')
        
        if 'id' in query_params and query_params['id']:
            return query_params['id'][0]
        return None
    
    def get_estimate_data(self, url):
        """見積もりURLからデータを取得する"""
        if not self.validate_calculator_url(url):
            raise ValueError(f"無効なAWS Pricing Calculator URL: {url}")
        
        # この部分はAWSのAPIがどのように動作するかによって異なります
        # 実際の実装では、AWS Pricing Calculatorから見積もりデータをどのように取得するかを
        # 詳細に調査する必要があります。
        # ここでは概念実装として、URLからデータを取得するアプローチを示します。
        
        try:
            # 見積もりIDの取得
            estimate_id = self.extract_id_from_url(url)
            if not estimate_id:
                raise ValueError(f"URLから見積もりIDを抽出できませんでした: {url}")
            
            # 実際の実装では、AWSのAPIエンドポイントにリクエストを送信してデータを取得
            # この部分はAWSの実際のAPIに合わせて調整が必要
            
            # 開発段階ではモックデータを返すことも考えられます
            # 実際の実装では、この部分をAWS Pricing Calculatorから実データを取得する処理に置き換えます
            mock_data = {
                "estimate_id": estimate_id,
                "name": f"見積もり {estimate_id[:8]}",
                "total_cost": {
                    "monthly": "100.00",
                    "upfront": "0.00",
                    "12_months": "1200.00"
                },
                "services": [
                    {
                        "name": "Amazon EC2",
                        "description": "テスト用EC2インスタンス",
                        "region": "ap-northeast-1",
                        "cost": {
                            "monthly": "50.00",
                            "upfront": "0.00",
                            "12_months": "600.00"
                        }
                    },
                    {
                        "name": "Amazon S3",
                        "description": "ストレージ",
                        "region": "ap-northeast-1",
                        "cost": {
                            "monthly": "50.00",
                            "upfront": "0.00",
                            "12_months": "600.00"
                        }
                    }
                ]
            }
            
            return mock_data
            
        except Exception as e:
            raise Exception(f"見積もりデータの取得に失敗しました: {str(e)}")
    
    def create_merged_estimate(self, merged_data):
        """合算されたデータから新しい見積もりURLを生成する"""
        # 実際の実装では、AWS Pricing CalculatorのAPIを使用して
        # 新しい見積もりを作成し、そのURLを取得します
        
        # この部分はAWSのAPIの仕様に応じて実装する必要があります
        # ここでは概念実装としてダミーのURLを生成します
        
        # 開発段階ではモックURLを返すことも考えられます
        mock_url = f"https://calculator.aws/#/estimate?id=merged{hash(json.dumps(merged_data))}"
        
        return mock_url
