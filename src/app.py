"""
AWS Pricing Calculator 見積もり合算ツール

このツールは複数のAWS Pricing Calculatorの見積もりURLを入力として受け取り、
すべての見積もりを合算した結果を表示します。
"""

import json
import os
from flask import Flask, request, render_template, jsonify

from src.data.parser import EstimateParser
from src.merger.cost_merger import EstimateMerger
from src.api.calculator_api import CalculatorAPI

app = Flask(__name__, template_folder='../templates')
parser = EstimateParser()
merger = EstimateMerger()
calculator_api = CalculatorAPI()

@app.route('/')
def index():
    """インデックスページを表示"""
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_estimates():
    """見積もりを合算して結果を返す"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({
                'success': False,
                'error': '見積もりURLが提供されていません。'
            })
        
        # 重複したURLを削除
        unique_urls = list(set(urls))
        
        # URLの検証
        valid_urls = []
        for url in unique_urls:
            if parser.validate_calculator_url(url):
                valid_urls.append(url)
            else:
                return jsonify({
                    'success': False,
                    'error': f'無効なAWS Pricing Calculator URL: {url}'
                })
        
        # 見積もりデータの取得
        estimate_data_list = []
        
        # テスト実装: サンプルJSONを使用
        for i, url in enumerate(valid_urls):
            if i == 0:
                with open('json_samples/sample1.json', 'r', encoding='utf-8') as file:
                    raw_data = json.load(file)
                    estimate_data = parser._structure_estimate_data(raw_data)
                    estimate_data_list.append(estimate_data)
            else:
                with open('json_samples/sample2.json', 'r', encoding='utf-8') as file:
                    raw_data = json.load(file)
                    estimate_data = parser._structure_estimate_data(raw_data)
                    estimate_data_list.append(estimate_data)
            
        # 見積もりの合算
        merged_data = merger.merge_estimates(estimate_data_list)
        
        if not merged_data:
            return jsonify({
                'success': False,
                'error': '見積もりデータの合算に失敗しました。'
            })
        
        # 合算された見積もりの新しいURLを生成
        merged_url_data = calculator_api.create_merged_estimate(merged_data)
        
        # 応答の作成
        response = {
            'success': True,
            'message': f'{len(valid_urls)}件の見積もりを合算しました。',
            'merged_url': merged_url_data['url'],
            'instructions': merged_url_data['instructions'],
            'data': {
                'name': merged_data['name'],
                'total_cost': merged_data['total_cost']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'見積もりの合算中にエラーが発生しました: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
