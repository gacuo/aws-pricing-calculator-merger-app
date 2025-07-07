"""
AWS Pricing Calculator API操作モジュール

AWS Pricing Calculatorとの連携を行います。
"""

from typing import Dict, List, Any, Union, Optional
import json
import uuid


class CalculatorAPI:
    """AWS Pricing CalculatorのAPIを操作するクラス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def create_merged_estimate(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        合算された見積もりデータからAWS Pricing Calculator形式のデータを生成します
        
        Args:
            merged_data: 合算された見積もりデータ
            
        Returns:
            Dict: AWS Pricing Calculator形式のデータとURL
            
        注: 実際のAWS Pricing CalculatorのAPIは公開されていないため、
        ここではJSONファイルとしてエクスポートする実装としています
        """
        # AWS Pricing Calculator形式に変換
        calculator_format = self._convert_to_calculator_format(merged_data)
        
        # 一意のIDを生成
        estimate_id = str(uuid.uuid4()).replace("-", "")
        
        # JSONファイル名
        filename = f"merged_estimate_{estimate_id[:8]}.json"
        
        # JSONファイルとして保存
        with open(f"merged_estimates/{filename}", "w", encoding="utf-8") as file:
            json.dump(calculator_format, file, ensure_ascii=False, indent=2)
        
        # 擬似的なURL生成（実際にはAWS Pricing CalculatorのAPIを使用）
        url = f"https://calculator.aws/#/estimate?id={estimate_id}"
        
        # インポート手順
        instructions = (
            "1. JSONファイルをダウンロードしてください\n"
            "2. AWS Pricing Calculatorにアクセス: https://calculator.aws/\n"
            "3. 「Create estimate」をクリック\n"
            "4. 右上の「Actions」→「Import」を選択\n"
            "5. ダウンロードしたJSONファイルをアップロード\n"
            "6. 「Import」ボタンをクリック"
        )
        
        return {
            "url": url,
            "instructions": instructions,
            "filename": filename
        }
    
    def _convert_to_calculator_format(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        内部形式のデータをAWS Pricing Calculator形式に変換します
        
        Args:
            merged_data: 内部形式の見積もりデータ
            
        Returns:
            Dict: AWS Pricing Calculator形式のデータ
        """
        # AWS Pricing Calculator形式のデータ構造を作成
        calculator_format = {
            "name": merged_data["name"],
            "currency": merged_data["metadata"]["currency"],
            "created": merged_data["metadata"]["created_on"],
            "totalUpfront": merged_data["total_cost"]["upfront"],
            "totalMonthly": merged_data["total_cost"]["monthly"],
            "totalAnnual": merged_data["total_cost"]["12_months"],
            "groups": {
                "services": []
            }
        }
        
        # サービスデータを変換
        for service in merged_data["services"]:
            calculator_service = {
                "name": service["service_name"],
                "region": service["region"],
                "upfrontCost": service["upfront_cost"],
                "monthlyCost": service["monthly_cost"],
                "description": service["description"],
                "config": service["config"]
            }
            calculator_format["groups"]["services"].append(calculator_service)
        
        return calculator_format
