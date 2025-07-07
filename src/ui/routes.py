"""
ウェブUIルートモジュール

このモジュールは、Webアプリケーションのルートを定義し、
ユーザーインターフェースを提供します。
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from src.data.parser import EstimateParser
from src.merger.cost_merger import EstimateMerger
from src.api.calculator_api import CalculatorAPI

# Blueprintの作成
bp = Blueprint('main', __name__)

def register_routes(app):
    """アプリケーションにルートを登録する"""
    app.register_blueprint(bp)

@bp.route('/')
def index():
    """メインページを表示する"""
    return render_template('index.html')

@bp.route('/merge', methods=['POST'])
def merge_estimates():
    """複数の見積もりURLを合算する"""
    # POSTデータの取得
    data = request.json
    urls = data.get('urls', [])
    
    # URLの検証
    if not urls:
        return jsonify({
            'success': False,
            'error': '見積もりURLが提供されていません'
        }), 400
    
    try:
        # 必要なオブジェクトのインスタンス化
        calculator_api = CalculatorAPI()
        parser = EstimateParser()
        merger = EstimateMerger()
        
        # すべてのURLの検証
        for url in urls:
            if not calculator_api.validate_calculator_url(url):
                return jsonify({
                    'success': False,
                    'error': f'無効なAWS Pricing Calculator URL: {url}'
                }), 400
        
        # 各URLからデータを解析
        estimate_data_list = []
        for url in urls:
            estimate_data = parser.parse_estimate_url(url)
            estimate_data_list.append(estimate_data)
        
        # データの合算
        merged_data = merger.merge_estimates(estimate_data_list)
        
        # 新しい見積もりURLの生成
        merged_url = calculator_api.create_merged_estimate(merged_data)
        
        return jsonify({
            'success': True,
            'merged_url': merged_url,
            'data': merged_data
        })
        
    except Exception as e:
        current_app.logger.error(f"見積もりの合算中にエラーが発生しました: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'処理中にエラーが発生しました: {str(e)}'
        }), 500
