"""
AWS Pricing Calculator コスト合算モジュール

複数のAWS Pricing Calculator見積もりデータを合算します。
"""

from typing import Dict, List, Any, Union, Optional


class EstimateMerger:
    """AWS Pricing Calculator見積もりデータの合算を行うクラス"""
    
    def merge_estimates(self, estimate_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数の見積もりデータを合算します
        
        Args:
            estimate_data_list: 合算する見積もりデータのリスト
            
        Returns:
            Dict: 合算された見積もりデータ
            
        Raises:
            ValueError: 見積もりデータが無効な場合
        """
        if not estimate_data_list:
            raise ValueError("合算する見積もりデータがありません")
        
        if len(estimate_data_list) == 1:
            return estimate_data_list[0]
        
        # 合算結果の初期値を作成
        merged_estimate = {
            "name": "Merged Estimate",
            "total_cost": {
                "upfront": "0.00",
                "monthly": "0.00",
                "12_months": "0.00"
            },
            "metadata": {
                "currency": "USD",
                "created_on": "",
                "region": "",
                "share_url": ""
            },
            "services": []
        }
        
        # メタデータを設定
        # 最新の見積もりのメタデータを使用
        merged_estimate["metadata"] = estimate_data_list[0]["metadata"]
        
        # サービスのグループ化と合算
        all_services = []
        for estimate_data in estimate_data_list:
            all_services.extend(estimate_data.get("services", []))
        
        # サービス名とリージョンでグループ化
        service_groups = {}
        for service in all_services:
            key = (service["service_name"], service["region"])
            if key not in service_groups:
                service_groups[key] = []
            service_groups[key].append(service)
        
        # 各サービスグループの合算
        for key, services in service_groups.items():
            merged_service = self._merge_services(services)
            merged_estimate["services"].append(merged_service)
        
        # 合計コストの計算
        upfront_total = sum(float(service["upfront_cost"].replace(",", "")) 
                         for service in merged_estimate["services"])
        monthly_total = sum(float(service["monthly_cost"].replace(",", "")) 
                          for service in merged_estimate["services"])
        yearly_total = monthly_total * 12 + upfront_total
        
        merged_estimate["total_cost"]["upfront"] = f"{upfront_total:,.2f}"
        merged_estimate["total_cost"]["monthly"] = f"{monthly_total:,.2f}"
        merged_estimate["total_cost"]["12_months"] = f"{yearly_total:,.2f}"
        
        # 見積もり名の設定
        estimate_names = [data["name"] for data in estimate_data_list if "name" in data]
        if estimate_names:
            merged_estimate["name"] = f"Merged: {' + '.join(estimate_names)}"
        
        return merged_estimate
    
    def _merge_services(self, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同一サービスの複数の見積もりデータを合算します
        
        Args:
            services: 合算するサービスのリスト（同一サービス名・リージョン）
            
        Returns:
            Dict: 合算されたサービスデータ
        """
        if not services:
            return {}
        
        if len(services) == 1:
            return services[0]
        
        # 最初のサービスをベースにする
        base_service = services[0]
        merged_service = base_service.copy()
        
        # コストの合算
        upfront_cost = 0.0
        monthly_cost = 0.0
        yearly_cost = 0.0
        
        for service in services:
            # upfront_cost 処理
            if "upfront_cost" in service:
                try:
                    if isinstance(service["upfront_cost"], (int, float)):
                        upfront_cost += service["upfront_cost"]
                    elif isinstance(service["upfront_cost"], str):
                        clean_str = service["upfront_cost"].replace(",", "").replace(" USD", "")
                        upfront_cost += float(clean_str) if clean_str else 0.0
                except (ValueError, TypeError):
                    pass  # エラーの場合はスキップ
                    
            # monthly_cost 処理
            if "monthly_cost" in service:
                try:
                    if isinstance(service["monthly_cost"], (int, float)):
                        monthly_cost += service["monthly_cost"]
                    elif isinstance(service["monthly_cost"], str):
                        clean_str = service["monthly_cost"].replace(",", "").replace(" USD", "")
                        monthly_cost += float(clean_str) if clean_str else 0.0
                except (ValueError, TypeError):
                    pass  # エラーの場合はスキップ
                    
            # yearly_cost 処理
            if "yearly_cost" in service and service["yearly_cost"]:
                try:
                    if isinstance(service["yearly_cost"], (int, float)):
                        yearly_cost += service["yearly_cost"]
                    elif isinstance(service["yearly_cost"], str):
                        clean_str = service["yearly_cost"].replace(",", "").replace(" USD", "")
                        yearly_cost += float(clean_str) if clean_str else 0.0
                except (ValueError, TypeError):
                    pass  # エラーの場合はスキップ
        
        # 年間コストが正しく計算されていない場合は再計算
        if yearly_cost == 0 and monthly_cost > 0:
            yearly_cost = monthly_cost * 12 + upfront_cost
            
        merged_service["upfront_cost"] = f"{upfront_cost:,.2f}"
        merged_service["monthly_cost"] = f"{monthly_cost:,.2f}"
        merged_service["yearly_cost"] = f"{yearly_cost:,.2f}"
        
        # 説明の統合
        descriptions = list(set(service["description"] for service in services if service.get("description")))
        merged_service["description"] = ", ".join(descriptions) if descriptions else ""
        
        # 設定の統合
        # 各サービスの設定キーを統合
        config_keys = set()
        for service in services:
            if "config" in service and service["config"]:
                config_keys.update(service["config"].keys())
        
        merged_config = {}
        for key in config_keys:
            # 各サービスから同じキーの値を取得
            values = [service["config"].get(key) for service in services 
                     if "config" in service and service["config"] and key in service["config"]]
            
            # 値が1つしかない場合はそのまま使用
            if len(values) == 1:
                merged_config[key] = values[0]
            else:
                # 複数の値がある場合は配列として保存
                merged_config[key] = values
        
        merged_service["config"] = merged_config
        
        return merged_service
