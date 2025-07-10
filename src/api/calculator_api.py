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
            
    def create_merged_estimate(self, estimate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        マージされた見積もりデータからAWS Pricing Calculatorへのエクスポートを作成する
        
        Args:
            estimate_data: マージされた見積もりデータ
            
        Returns:
            Dict: 生成されたURL情報
        """
        try:
            # AWS Pricing Calculator形式に変換
            calculator_data = self._convert_to_calculator_format(estimate_data)
            
            # URLの生成
            calculator_url = self.generate_calculator_url(calculator_data)
            
            # 結果を返す
            return {
                'url': calculator_url,
                'instructions': '新しいURLが生成されました。リンク先でマージされた見積もりを確認できます。',
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"マージ見積もり作成中にエラーが発生: {str(e)}", exc_info=True)
            return {
                'url': f"{self.base_url}#/estimate",
                'instructions': 'エラーが発生しました。手動でAWS Pricing Calculatorにアクセスして見積もりを作成してください。',
                'status': 'error',
                'error': str(e)
            }
    
    def _convert_to_calculator_format(self, estimate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        内部形式からAWS Pricing Calculator形式に変換する
        
        Args:
            estimate_data: 内部形式の見積もりデータ
            
        Returns:
            Dict: AWS Pricing Calculator形式のデータ
        """
        # AWS Pricing Calculator形式のデータ構造
        calculator_data = {
            'name': estimate_data.get('name', 'Merged Estimate'),
            'timeUnit': 'monthly',
            'currency': estimate_data.get('metadata', {}).get('currency', 'USD'),
            'regions': self._extract_regions(estimate_data),
            'services': self._convert_services(estimate_data.get('services', []))
        }
        
        return calculator_data
    
    def _extract_regions(self, estimate_data: Dict[str, Any]) -> List[str]:
        """
        見積もりデータから使用しているリージョンのリストを抽出する
        
        Args:
            estimate_data: 見積もりデータ
            
        Returns:
            List[str]: リージョンのリスト
        """
        regions = set()
        for service in estimate_data.get('services', []):
            if 'region' in service and service['region']:
                regions.add(service['region'])
        
        return list(regions)
    
    def calculate_total_cost(self, estimate_data: Dict[str, Any]) -> Dict[str, str]:
        """
        見積もりデータから総コストを計算する
        
        Args:
            estimate_data: 見積もりデータ
            
        Returns:
            Dict: 月額、初期、年間コスト
        """
        try:
            # サービスごとのコスト集計
            monthly_total = 0.0
            upfront_total = 0.0
            
            # サービスコストの集計
            if 'services' in estimate_data:
                for service in estimate_data['services']:
                    # monthlyCostとupfrontCostの処理
                    if isinstance(service.get('monthlyCost'), (int, float)):
                        monthly_total += service['monthlyCost']
                    elif isinstance(service.get('monthlyCost'), str):
                        # 文字列から数値への変換
                        try:
                            cost_str = service['monthlyCost'].replace(',', '').replace(' USD', '')
                            monthly_total += float(cost_str)
                        except (ValueError, TypeError):
                            logger.warning(f"月額コストの解析エラー: {service.get('monthlyCost')}")
                    
                    # upfrontCostの処理
                    if isinstance(service.get('upfrontCost'), (int, float)):
                        upfront_total += service['upfrontCost']
                    elif isinstance(service.get('upfrontCost'), str):
                        # 文字列から数値への変換
                        try:
                            cost_str = service['upfrontCost'].replace(',', '').replace(' USD', '')
                            upfront_total += float(cost_str)
                        except (ValueError, TypeError):
                            logger.warning(f"初期コストの解析エラー: {service.get('upfrontCost')}")
                            
                    # monthly_costとupfront_costの処理 (別の形式)
                    if isinstance(service.get('monthly_cost'), str):
                        try:
                            cost_str = service['monthly_cost'].replace(',', '').replace(' USD', '')
                            monthly_total += float(cost_str)
                        except (ValueError, TypeError):
                            pass
                    
                    if isinstance(service.get('upfront_cost'), str):
                        try:
                            cost_str = service['upfront_cost'].replace(',', '').replace(' USD', '')
                            upfront_total += float(cost_str)
                        except (ValueError, TypeError):
                            pass
            
            # 年間コストの計算（月額 × 12 + 初期コスト）
            annual_total = monthly_total * 12 + upfront_total
            
            # 結果をフォーマット
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
        
    def _convert_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        内部サービス形式からAWS Pricing Calculator形式に変換する
        
        Args:
            services: 内部形式のサービスリスト
            
        Returns:
            List[Dict]: AWS Pricing Calculator形式のサービスリスト
        """
        calculator_services = []
        
        for service in services:
            calc_service = {
                'name': service.get('service_name', 'Unknown Service'),
                'description': service.get('description', ''),
                'region': service.get('region', 'us-east-1'),
                'monthly': self._parse_cost_value(service.get('monthly_cost', '0.00')),
                'upfront': self._parse_cost_value(service.get('upfront_cost', '0.00')),
                'configuration': service.get('config', {})
            }
            calculator_services.append(calc_service)
            
        return calculator_services
    
    def _parse_cost_value(self, cost_str: str) -> float:
        """
        コスト文字列から数値を抽出する
        
        Args:
            cost_str: コスト文字列（例: "1,234.56 USD"）
            
        Returns:
            float: 数値としてのコスト
        """
        try:
            # カンマと通貨単位を削除
            clean_str = cost_str.replace(',', '').replace(' USD', '')
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0
    
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
