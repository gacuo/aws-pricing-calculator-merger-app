"""
AWS Pricing Calculator API連携モジュール

AWS Pricing Calculatorとの連携を行うためのAPIクラスを提供します。
"""

import os
import json
import uuid
import base64
import zlib
import csv
from typing import Dict, List, Any, Optional
import logging
import requests

logger = logging.getLogger(__name__)

class CalculatorAPI:
    """
    AWS Pricing Calculator APIとの連携を行うクラス
    
    このクラスは、以下の機能を提供します：
    - 見積もりデータからAWS Pricing Calculator URLの生成
    - 見積もりデータからの総コスト計算
    - 各種形式へのエクスポート（CSV, PDF）
    """
    
    def __init__(self):
        """初期化"""
        self.base_url = "https://calculator.aws/"
        
    def generate_calculator_url(self, estimate_data: Dict[str, Any]) -> str:
        """
        見積もりデータからAWS Pricing Calculator URLを生成する
        
        Args:
            estimate_data: 見積もりデータ
            
        Returns:
            str: 生成されたAWS Pricing Calculator URL
        """
        try:
            # 実際のAWS Pricing CalculatorはデータをBase64エンコードし、
            # クエリパラメータとして渡す仕組みになっています
            # ここではシミュレーションとして一意のIDを生成します
            
            # 本番実装では実際のデータをエンコードしてURLを生成します
            # data_json = json.dumps(estimate_data)
            # compressed = zlib.compress(data_json.encode('utf-8'))
            # encoded = base64.b64encode(compressed).decode('ascii')
            
            # シミュレーション用にUUIDを生成
            estimate_id = str(uuid.uuid4()).replace('-', '')[:16]
            
            return f"{self.base_url}#/estimate?id={estimate_id}"
            
        except Exception as e:
            logger.error(f"URL生成中にエラーが発生: {str(e)}", exc_info=True)
            return f"{self.base_url}#/estimate"
    
    def calculate_total_cost(self, estimate_data: Dict[str, Any]) -> Dict[str, str]:
        """
        見積もりデータから総コストを計算する
        
        Args:
            estimate_data: 見積もりデータ
            
        Returns:
            Dict: 月額、初期、年間コスト
        """
        try:
            # 実際の実装では見積もりデータから総コストを計算します
            # ここではサンプル実装としてモック値を返します
            
            # サービスごとのコスト集計
            monthly_total = 0.0
            upfront_total = 0.0
            
            # モック実装
            if 'services' in estimate_data:
                for service in estimate_data['services']:
                    if 'monthlyCost' in service:
                        monthly_total += float(service['monthlyCost'])
                    if 'upfrontCost' in service:
                        upfront_total += float(service['upfrontCost'])
            
            # 12ヶ月分の計算
            annual_total = monthly_total * 12 + upfront_total
            
            return {
                'monthly': f"{monthly_total:,.2f} USD",
                'upfront': f"{upfront_total:,.2f} USD",
                '12_months': f"{annual_total:,.2f} USD"
            }
            
        except Exception as e:
            logger.error(f"コスト計算中にエラーが発生: {str(e)}", exc_info=True)
            return {
                'monthly': "0.00 USD",
                'upfront': "0.00 USD",
                '12_months': "0.00 USD"
            }
    
    def extract_services(self, estimate_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        見積もりデータからサービス情報を抽出する
        
        Args:
            estimate_data: 見積もりデータ
            
        Returns:
            List[Dict]: サービス情報のリスト
        """
        services = []
        
        try:
            if 'services' in estimate_data:
                for service in estimate_data['services']:
                    service_info = {
                        'service_name': service.get('name', 'Unknown'),
                        'region': service.get('region', 'us-east-1'),
                        'upfront_cost': f"{float(service.get('upfrontCost', 0)):,.2f} USD",
                        'monthly_cost': f"{float(service.get('monthlyCost', 0)):,.2f} USD",
                        'description': service.get('description', ''),
                        'config': service.get('config', {})
                    }
                    services.append(service_info)
        except Exception as e:
            logger.error(f"サービス情報抽出中にエラーが発生: {str(e)}", exc_info=True)
            
        return services
    
    def export_to_csv(self, estimate_data: Dict[str, Any], estimate_id: str, output_dir: str) -> str:
        """
        見積もりデータをCSV形式にエクスポートする
        
        Args:
            estimate_data: 見積もりデータ
            estimate_id: 見積もりID
            output_dir: 出力ディレクトリ
            
        Returns:
            str: 出力ファイルのパス
        """
        output_path = os.path.join(output_dir, f"{estimate_id}.csv")
        
        try:
            services = self.extract_services(estimate_data)
            total_cost = self.calculate_total_cost(estimate_data)
            
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = ['Service', 'Region', 'Monthly Cost', 'Upfront Cost', 'Description']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for service in services:
                    writer.writerow({
                        'Service': service['service_name'],
                        'Region': service['region'],
                        'Monthly Cost': service['monthly_cost'],
                        'Upfront Cost': service['upfront_cost'],
                        'Description': service['description']
                    })
                
                # 合計行
                writer.writerow({
                    'Service': 'TOTAL',
                    'Region': '',
                    'Monthly Cost': total_cost['monthly'],
                    'Upfront Cost': total_cost['upfront'],
                    'Description': f"Annual total: {total_cost['12_months']}"
                })
                
            return output_path
            
        except Exception as e:
            logger.error(f"CSV出力中にエラーが発生: {str(e)}", exc_info=True)
            
            # エラー時は空のCSVを作成
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Error generating CSV'])
                
            return output_path
    
    def export_to_pdf(self, estimate_data: Dict[str, Any], estimate_id: str, output_dir: str) -> str:
        """
        見積もりデータをPDF形式にエクスポートする
        
        Args:
            estimate_data: 見積もりデータ
            estimate_id: 見積もりID
            output_dir: 出力ディレクトリ
            
        Returns:
            str: 出力ファイルのパス
        """
        # 注意: これは実際のPDF生成コードではありません
        # 実際の実装ではreportlabやWeasyPrintなどのライブラリを使用してPDFを生成します
        output_path = os.path.join(output_dir, f"{estimate_id}.pdf")
        
        try:
            # ここでは代わりにCSVを生成してpdfという拡張子をつけます
            services = self.extract_services(estimate_data)
            total_cost = self.calculate_total_cost(estimate_data)
            
            with open(output_path, 'w', newline='') as file:
                file.write("AWS Pricing Calculator Merged Estimate\n\n")
                file.write(f"Estimate Name: {estimate_data.get('name', 'Merged Estimate')}\n")
                file.write(f"Monthly Cost: {total_cost['monthly']}\n")
                file.write(f"Upfront Cost: {total_cost['upfront']}\n")
                file.write(f"12-month Cost: {total_cost['12_months']}\n\n")
                
                file.write("Services:\n")
                for service in services:
                    file.write(f"- {service['service_name']} ({service['region']}): {service['monthly_cost']} monthly\n")
                
            return output_path
            
        except Exception as e:
            logger.error(f"PDF出力中にエラーが発生: {str(e)}", exc_info=True)
            
            # エラー時は空のファイルを作成
            with open(output_path, 'w') as file:
                file.write("Error generating PDF")
                
            return output_path
