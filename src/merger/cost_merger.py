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
                "share_url": "",  # 新しいURLは後で生成される
                "estimate_id": "",  # 新しいIDは後で生成される
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
                    # 名前とリージョンの組み合わせでグループ化
                    key = (service["name"], service["region"])
                    service_groups[key].append(service)
            
            # 同じサービス（名前とリージョンが同じ）を合算
            for (name, region), services in service_groups.items():
                # プロパティを統合（同一プロパティの場合は最初のものを使用、異なる場合は連結）
                merged_properties = {}
                all_properties_same = True
                first_service_props = services[0]["properties"]
                
                # すべてのサービスで同じプロパティを持っているか確認
                for service in services[1:]:
                    if service["properties"] != first_service_props:
                        all_properties_same = False
                        break
                
                # プロパティの統合方法を決定
                if all_properties_same:
                    merged_properties = first_service_props
                else:
                    # 異なる場合は、各プロパティを連結してリスト化
                    all_props = defaultdict(list)
                    for service in services:
                        for prop_key, prop_value in service["properties"].items():
                            if prop_value not in all_props[prop_key]:
                                all_props[prop_key].append(prop_value)
                    
                    # リストをカンマ区切りの文字列に変換
                    for prop_key, prop_values in all_props.items():
                        if len(prop_values) == 1:
                            merged_properties[prop_key] = prop_values[0]
                        else:
                            merged_properties[prop_key] = ", ".join([str(v) for v in prop_values])
                
                # 説明の統合
                descriptions = [s["description"] for s in services if s["description"] and s["description"] != "-"]
                merged_description = ", ".join(descriptions) if descriptions else "-"
                
                # コストの合算
                merged_service = {
                    "name": name,
                    "description": merged_description,
                    "region": region,
                    "cost": {
                        "monthly": sum(s["cost"]["monthly"] for s in services),
                        "upfront": sum(s["cost"]["upfront"] for s in services),
                        "12_months": sum(s["cost"]["12_months"] for s in services)
                    },
                    "properties": merged_properties
                }
                
                merged_estimate["services"].append(merged_service)
            
            return merged_estimate
            
        except Exception as e:
            logger.error(f"見積もりの合算に失敗しました: {str(e)}")
            raise
