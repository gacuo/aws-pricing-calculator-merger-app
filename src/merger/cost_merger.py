"""
見積もり合算モジュール

このモジュールは複数の見積もりデータを合算し、新しい見積もりデータを生成します。
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class EstimateMerger:
    """見積もり合算クラス"""
    
    def __init__(self):
        pass
    
    def merge_estimates(self, estimate_data_list):
        """複数の見積もりデータを合算する"""
        if not estimate_data_list:
            logger.warning("合算する見積もりデータがありません")
            return None
        
        if len(estimate_data_list) == 1:
            logger.info("単一の見積もりのみが提供されたため、そのまま返します")
            return estimate_data_list[0]
        
        try:
            # 合算された見積もりの基本構造を作成
            merged_estimate = {
                "name": "合算された見積もり",
                "total_cost": {
                    "monthly": 0.0,
                    "upfront": 0.0,
                    "12_months": 0.0
                },
                "services": []
            }
            
            # サービスを名前とリージョンでグループ化するための辞書
            service_groups = defaultdict(list)
            
            # すべての見積もりからサービスを収集
            for estimate in estimate_data_list:
                # 合計コストを加算
                merged_estimate["total_cost"]["monthly"] += estimate["total_cost"]["monthly"]
                merged_estimate["total_cost"]["upfront"] += estimate["total_cost"]["upfront"]
                merged_estimate["total_cost"]["12_months"] += estimate["total_cost"]["12_months"]
                
                # サービスをグループ化
                for service in estimate.get("services", []):
                    key = (service["name"], service["region"])
                    service_groups[key].append(service)
            
            # 同じサービス（名前とリージョンが同じ）を合算
            for (name, region), services in service_groups.items():
                merged_service = {
                    "name": name,
                    "description": f"合算: {', '.join([s['description'] for s in services if s['description']])}",
                    "region": region,
                    "cost": {
                        "monthly": sum(s["cost"]["monthly"] for s in services),
                        "upfront": sum(s["cost"]["upfront"] for s in services),
                        "12_months": sum(s["cost"]["12_months"] for s in services)
                    }
                }
                merged_estimate["services"].append(merged_service)
            
            return merged_estimate
            
        except Exception as e:
            logger.error(f"見積もりの合算に失敗しました: {str(e)}")
            raise
