"""
AWS Pricing Calculator APIモジュール

このモジュールはAWS Pricing CalculatorのAPIとの連携を担当します。
見積もりURLからデータを取得し、新しい見積もりURLを生成する機能を提供します。
"""

import json
import logging
import re
import uuid
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class CalculatorAPI:
    """AWS Pricing Calculator API操作クラス"""
    
    BASE_URL = "https://calculator.aws"
    ESTIMATE_PATH = "#/estimate"
    
    def __init__(self):
        pass
    
    def validate_calculator_url(self, url):
        """URLがAWS Pricing Calculatorのエクスポート形式か検証する"""
        if not url:
            return False
            
        pattern = r'^https://calculator\.aws/#/estimate\?id=[a-f0-9]+$'
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
    
    def create_merged_estimate(self, merged_data):
        """合算されたデータから新しい見積もりURLを生成する"""
        
        # 実際のAWS Pricing CalculatorのAPI実装
        # この部分は実際のAWS APIの仕様に合わせて更新する必要があります
        
        # 現状では、AWSの非公開APIを直接利用することは困難なため、
        # AWS Pricing Calculatorで手動で新しい見積もりを作成するための手順を提示する形になります
        
        # テスト用に生成されたIDを使用してURLを作成
        # 注: これはダミーのURLであり、実際には機能しません
        generated_id = uuid.uuid4().hex[:40]
        mock_url = f"{self.BASE_URL}/{self.ESTIMATE_PATH}?id={generated_id}"
        
        # データを使用して構築するための手順を返す
        instructions = self._create_manual_instructions(merged_data)
        
        # JSONデータを文字列化して返す（後でクライアントが使用するため）
        json_data = self._convert_to_calculator_format(merged_data)
        
        return {
            "url": mock_url,
            "instructions": instructions,
            "json_data": json.dumps(json_data, indent=4)
        }
    
    def _create_manual_instructions(self, merged_data):
        """合算データから手動で見積もりを構築するための手順を生成する"""
        services_count = len(merged_data["services"])
        total_monthly = merged_data["total_cost"]["monthly"]
        total_annual = merged_data["total_cost"]["12_months"]
        
        instructions = [
            "新しいAWS Pricing Calculator見積もりを作成するには、以下の手順に従ってください：",
            "",
            "1. AWS Pricing Calculator (https://calculator.aws/) にアクセスする",
            "2. 「Create estimate」をクリックする",
            f"3. 以下の{services_count}つのサービスを追加する："
        ]
        
        for idx, service in enumerate(merged_data["services"], 1):
            instructions.append(f"   {idx}. {service['name']} ({service['region']}) - 月額: ${service['cost']['monthly']:.2f}")
            
            # 各サービスのプロパティを追加
            for prop_key, prop_value in service["properties"].items():
                instructions.append(f"      - {prop_key}: {prop_value}")
        
        instructions.extend([
            "",
            f"合算後の月額コスト: ${total_monthly:.2f}",
            f"合算後の年間コスト: ${total_annual:.2f}",
            "",
            "各サービスの詳細な設定については、エクスポートされたJSONデータを参照してください。"
        ])
        
        return "\n".join(instructions)
    
    def _convert_to_calculator_format(self, merged_data):
        """内部データ形式をAWS Pricing Calculator形式に変換する"""
        
        # AWS Pricing Calculatorが期待するJSON形式に変換
        calculator_data = {
            "Name": merged_data["name"],
            "Total Cost": {
                "monthly": f"{merged_data['total_cost']['monthly']:.2f}",
                "upfront": f"{merged_data['total_cost']['upfront']:.2f}",
                "12 months": f"{merged_data['total_cost']['12_months']:.2f}"
            },
            "Metadata": {
                "Currency": "USD",
                "Locale": "en_US",
                "Created On": "auto-generated",
                "Legal Disclaimer": "AWS Pricing Calculator provides only an estimate of your AWS fees and doesn't include any taxes that might apply. Your actual fees depend on a variety of factors, including your actual usage of AWS services."
            },
            "Groups": {
                "Services": []
            }
        }
        
        # サービスデータを変換
        for service in merged_data["services"]:
            calculator_service = {
                "Service Name": service["name"],
                "Description": service["description"] if service["description"] != "-" else "",
                "Region": service["region"],
                "Service Cost": {
                    "monthly": f"{service['cost']['monthly']:.2f}",
                    "upfront": f"{service['cost']['upfront']:.2f}",
                    "12 months": f"{service['cost']['12_months']:.2f}"
                },
                "Properties": service["properties"]
            }
            calculator_data["Groups"]["Services"].append(calculator_service)
        
        return calculator_data
