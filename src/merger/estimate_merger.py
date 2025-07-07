"""
見積もり合算モジュール

複数のAWS Pricing Calculator見積もりデータを合算するクラスを提供します。
"""

import logging
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class EstimateMerger:
    """
    AWS Pricing Calculator見積もりデータの合算を行うクラス
    
    このクラスは、以下の機能を提供します：
    - 複数の見積もりデータの合算
    - 同一サービス間でのコストの合算
    - サービス設定の統合
    """
    
    def __init__(self):
        """初期化"""
        pass
        
    def merge_estimates(self, estimate_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数の見積もりデータを合算する
        
        Args:
            estimate_data_list: 見積もりデータのリスト
            
        Returns:
            Dict: 合算された見積もりデータ
        """
        if not estimate_data_list:
            raise ValueError("見積もりデータが提供されていません")
        
        if len(estimate_data_list) == 1:
            # 1つだけの場合はそのまま返す
            return estimate_data_list[0]
        
        # マージ処理
        merged_data = {
            'name': self._generate_merged_name(estimate_data_list),
            'currency': self._get_common_currency(estimate_data_list),
            'services': self._merge_services(estimate_data_list)
        }
        
        return merged_data
    
    def _generate_merged_name(self, estimate_data_list: List[Dict[str, Any]]) -> str:
        """
        合算された見積もりの名前を生成する
        
        Args:
            estimate_data_list: 見積もりデータのリスト
            
        Returns:
            str: 合算された見積もりの名前
        """
        names = [data.get('name', 'Unnamed Estimate') for data in estimate_data_list]
        
        # 長さ制限を考慮
        if len(names) <= 2:
            return "Merged: " + " + ".join(names)
        else:
            return f"Merged: {names[0]} + {len(names) - 1} others"
    
    def _get_common_currency(self, estimate_data_list: List[Dict[str, Any]]) -> str:
        """
        共通通貨を取得する
        
        Args:
            estimate_data_list: 見積もりデータのリスト
            
        Returns:
            str: 共通通貨コード
        """
        currencies = {data.get('currency', 'USD') for data in estimate_data_list}
        
        if len(currencies) == 1:
            return list(currencies)[0]
        else:
            # 複数の通貨がある場合はUSDを使用
            logger.warning(f"複数の通貨が使用されています: {currencies}、USDに統一します")
            return "USD"
    
    def _merge_services(self, estimate_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        サービスデータをマージする
        
        Args:
            estimate_data_list: 見積もりデータのリスト
            
        Returns:
            List[Dict]: マージされたサービスデータのリスト
        """
        # サービスをキーでグループ化する
        # キーは「サービス名_リージョン」形式
        service_groups = defaultdict(list)
        
        for estimate in estimate_data_list:
            for service in estimate.get('services', []):
                service_name = service.get('name', 'Unknown Service')
                region = service.get('region', 'us-east-1')
                key = f"{service_name}_{region}"
                
                service_groups[key].append(service)
        
        # グループごとにマージ
        merged_services = []
        for key, services in service_groups.items():
            merged_service = self._merge_service_group(services)
            merged_services.append(merged_service)
        
        return merged_services
    
    def _merge_service_group(self, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同一サービスグループをマージする
        
        Args:
            services: 同一サービスグループ
            
        Returns:
            Dict: マージされたサービスデータ
        """
        if not services:
            return {}
        
        if len(services) == 1:
            # 1つだけの場合はそのまま返す
            return services[0]
        
        # 基本情報の取得
        first_service = services[0]
        service_name = first_service.get('name', 'Unknown Service')
        region = first_service.get('region', 'us-east-1')
        
        # コスト合算
        monthly_cost = sum(float(service.get('monthlyCost', 0)) for service in services)
        upfront_cost = sum(float(service.get('upfrontCost', 0)) for service in services)
        
        # 設定の統合
        configs = [service.get('config', {}) for service in services]
        merged_config = self._merge_configs(configs, service_name)
        
        # 説明の統合
        descriptions = [service.get('description', '') for service in services if service.get('description')]
        if descriptions:
            if len(descriptions) == 1:
                merged_description = descriptions[0]
            else:
                merged_description = f"Combined: {', '.join(descriptions[:2])}" + (f" and {len(descriptions) - 2} more" if len(descriptions) > 2 else "")
        else:
            merged_description = f"Merged {service_name} in {region}"
        
        # マージされたサービスデータ
        merged_service = {
            'name': service_name,
            'region': region,
            'monthlyCost': monthly_cost,
            'upfrontCost': upfront_cost,
            'description': merged_description,
            'config': merged_config
        }
        
        return merged_service
    
    def _merge_configs(self, configs: List[Dict[str, Any]], service_name: str) -> Dict[str, Any]:
        """
        サービス設定をマージする
        
        Args:
            configs: 設定のリスト
            service_name: サービス名
            
        Returns:
            Dict: マージされた設定
        """
        # サービスタイプによって異なるマージロジックを適用
        if "EC2" in service_name:
            return self._merge_ec2_configs(configs)
        elif "S3" in service_name:
            return self._merge_s3_configs(configs)
        elif "RDS" in service_name:
            return self._merge_rds_configs(configs)
        elif "DynamoDB" in service_name:
            return self._merge_dynamodb_configs(configs)
        else:
            # デフォルトのマージロジック
            return self._merge_default_configs(configs)
    
    def _merge_ec2_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        EC2の設定をマージする
        
        Args:
            configs: EC2設定のリスト
            
        Returns:
            Dict: マージされたEC2設定
        """
        merged_config = {
            'serviceCode': 'ec2',
            'instances': {}
        }
        
        # インスタンスタイプごとにカウント
        instance_counts = defaultdict(int)
        for config in configs:
            instance_type = config.get('instanceType', 'unknown')
            count = config.get('count', 1)
            instance_counts[instance_type] += count
        
        # マージ結果を設定
        for instance_type, count in instance_counts.items():
            merged_config['instances'][instance_type] = {
                'count': count
            }
        
        return merged_config
    
    def _merge_s3_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        S3の設定をマージする
        
        Args:
            configs: S3設定のリスト
            
        Returns:
            Dict: マージされたS3設定
        """
        merged_config = {
            'serviceCode': 's3',
            'storage': {
                'totalGB': 0,
                'standardGB': 0,
                'iaGB': 0,
                'glacierGB': 0
            }
        }
        
        # ストレージ容量を合算
        for config in configs:
            storage = config.get('storage', {})
            merged_config['storage']['totalGB'] += storage.get('totalGB', 0)
            merged_config['storage']['standardGB'] += storage.get('standardGB', 0)
            merged_config['storage']['iaGB'] += storage.get('iaGB', 0)
            merged_config['storage']['glacierGB'] += storage.get('glacierGB', 0)
        
        return merged_config
    
    def _merge_rds_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        RDSの設定をマージする
        
        Args:
            configs: RDS設定のリスト
            
        Returns:
            Dict: マージされたRDS設定
        """
        merged_config = {
            'serviceCode': 'rds',
            'instances': {}
        }
        
        # インスタンスタイプごとにカウント
        instance_counts = defaultdict(int)
        storage_gb = 0
        
        for config in configs:
            instance_type = config.get('instanceType', 'db.unknown')
            count = config.get('count', 1)
            storage_gb += config.get('storageGB', 0)
            instance_counts[instance_type] += count
        
        # マージ結果を設定
        for instance_type, count in instance_counts.items():
            merged_config['instances'][instance_type] = {
                'count': count
            }
        
        merged_config['storageGB'] = storage_gb
        
        return merged_config
    
    def _merge_dynamodb_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        DynamoDBの設定をマージする
        
        Args:
            configs: DynamoDB設定のリスト
            
        Returns:
            Dict: マージされたDynamoDB設定
        """
        merged_config = {
            'serviceCode': 'dynamodb',
            'totalStorage': 0,
            'readCapacity': 0,
            'writeCapacity': 0
        }
        
        # キャパシティユニットと容量を合算
        for config in configs:
            merged_config['totalStorage'] += config.get('totalStorage', 0)
            merged_config['readCapacity'] += config.get('readCapacity', 0)
            merged_config['writeCapacity'] += config.get('writeCapacity', 0)
        
        return merged_config
    
    def _merge_default_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        デフォルトの設定マージロジック
        
        Args:
            configs: 設定のリスト
            
        Returns:
            Dict: マージされた設定
        """
        # 最も単純なマージ: 最初の設定をベースに使用
        merged_config = {}
        
        if configs:
            # サービスコードがあれば保持
            for config in configs:
                if 'serviceCode' in config:
                    merged_config['serviceCode'] = config['serviceCode']
                    break
            
            # 数値項目の合算
            numeric_fields = set()
            for config in configs:
                for key, value in config.items():
                    if isinstance(value, (int, float)) and key != 'serviceCode':
                        numeric_fields.add(key)
            
            for field in numeric_fields:
                merged_config[field] = sum(config.get(field, 0) for config in configs)
        
        return merged_config
