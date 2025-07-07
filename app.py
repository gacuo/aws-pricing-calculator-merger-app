"""
AWS Pricing Calculator 見積もり合算ツール

このアプリケーションは複数のAWS Pricing Calculatorの見積もりURLを入力として受け取り、
それらを合算した結果を返すウェブアプリケーションです。
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import logging
from logging.config import dictConfig

# 自作モジュールのインポート
from src.api.calculator_api import CalculatorAPI
from src.data.parser import EstimateParser
from src.merger.estimate_merger import EstimateMerger

# ロギング設定
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'file']
    }
})

# Flaskアプリケーションの初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['UPLOAD_FOLDER'] = 'json_samples'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB制限
app.config['MERGED_ESTIMATES_FOLDER'] = 'merged_estimates'

# ディレクトリがない場合は作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MERGED_ESTIMATES_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# ロガーの取得
logger = logging.getLogger(__name__)

# 許可されるファイル拡張子
ALLOWED_EXTENSIONS = {'json'}

def allowed_file(filename):
    """アップロードされたファイルの拡張子が許可されているかチェックする"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """トップページを表示する"""
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_estimates():
    """見積もりの合算処理を行う"""
    try:
        # URLからの合算
        if 'urls' in request.form:
            urls = request.form.getlist('urls')
            if not urls or not urls[0]:
                return jsonify({
                    'success': False,
                    'error': 'URLが入力されていません。'
                }), 400
                
            logger.info(f"URLからの合算処理: {len(urls)}件のURL")
            
            # URLからデータを抽出
            parser = EstimateParser()
            estimate_data_list = []
            
            for url in urls:
                try:
                    estimate_data = parser.parse_from_url(url)
                    estimate_data_list.append(estimate_data)
                except Exception as e:
                    logger.error(f"URLからのデータ抽出エラー: {str(e)}", exc_info=True)
                    return jsonify({
                        'success': False,
                        'error': f"無効なAWS Pricing Calculator URL: {url}"
                    }), 400
            
            # データを合算
            merger = EstimateMerger()
            merged_data = merger.merge_estimates(estimate_data_list)
            
            # 結果を保存
            merged_id = str(uuid.uuid4())
            output_path = os.path.join(app.config['MERGED_ESTIMATES_FOLDER'], f"{merged_id}.json")
            with open(output_path, 'w') as f:
                json.dump(merged_data, f, indent=2)
            
            # AWS Calculator APIを使用してURLを生成
            calculator_api = CalculatorAPI()
            merged_url = calculator_api.generate_calculator_url(merged_data)
            
            return jsonify({
                'success': True,
                'message': f"{len(urls)}件の見積もりを合算しました。",
                'merged_url': merged_url,
                'data': {
                    'name': merged_data.get('name', 'Merged Estimate'),
                    'total_cost': calculator_api.calculate_total_cost(merged_data)
                },
                'download_url': url_for('download_estimate', estimate_id=merged_id),
                'id': merged_id
            })
            
        # ファイルアップロードからの合算
        elif 'files' in request.files:
            uploaded_files = request.files.getlist('files')
            valid_files = []
            
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    valid_files.append(file_path)
            
            if not valid_files:
                return jsonify({
                    'success': False,
                    'error': '有効なJSONファイルがアップロードされていません。'
                }), 400
                
            logger.info(f"ファイルからの合算処理: {len(valid_files)}件のファイル")
            
            # ファイルからデータを抽出
            parser = EstimateParser()
            estimate_data_list = []
            
            for file_path in valid_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    estimate_data = parser.parse_from_json(data)
                    estimate_data_list.append(estimate_data)
                except Exception as e:
                    logger.error(f"ファイルからのデータ抽出エラー: {str(e)}", exc_info=True)
                    return jsonify({
                        'success': False,
                        'error': f"無効なJSON形式: {os.path.basename(file_path)}"
                    }), 400
            
            # データを合算
            merger = EstimateMerger()
            merged_data = merger.merge_estimates(estimate_data_list)
            
            # 結果を保存
            merged_id = str(uuid.uuid4())
            output_path = os.path.join(app.config['MERGED_ESTIMATES_FOLDER'], f"{merged_id}.json")
            with open(output_path, 'w') as f:
                json.dump(merged_data, f, indent=2)
            
            # AWS Calculator APIを使用してURLを生成
            calculator_api = CalculatorAPI()
            merged_url = calculator_api.generate_calculator_url(merged_data)
            
            return jsonify({
                'success': True,
                'message': f"{len(valid_files)}件の見積もりを合算しました。",
                'merged_url': merged_url,
                'data': {
                    'name': merged_data.get('name', 'Merged Estimate'),
                    'total_cost': calculator_api.calculate_total_cost(merged_data)
                },
                'download_url': url_for('download_estimate', estimate_id=merged_id),
                'id': merged_id
            })
        
        else:
            return jsonify({
                'success': False,
                'error': 'URLまたはファイルが提供されていません。'
            }), 400
            
    except Exception as e:
        logger.error(f"見積もり合算中にエラーが発生: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"見積もりの合算中にエラーが発生しました: {str(e)}"
        }), 500

@app.route('/download/<estimate_id>', methods=['GET'])
def download_estimate(estimate_id):
    """合算した見積もりデータをダウンロードする"""
    try:
        file_path = os.path.join(app.config['MERGED_ESTIMATES_FOLDER'], f"{estimate_id}.json")
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '指定されたIDの見積もりが見つかりません。'
            }), 404
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"aws-merged-estimate-{timestamp}.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"ダウンロード処理中にエラーが発生: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"ダウンロード中にエラーが発生しました: {str(e)}"
        }), 500

@app.route('/api/v1/merge', methods=['POST'])
def api_merge_estimates():
    """API: 見積もりの合算処理を行う"""
    try:
        data = request.json
        if not data or 'urls' not in data or not data['urls']:
            return jsonify({
                'success': False,
                'error': 'URLsが提供されていません。'
            }), 400
            
        urls = data['urls']
        logger.info(f"API: URLからの合算処理: {len(urls)}件のURL")
        
        # URLからデータを抽出
        parser = EstimateParser()
        estimate_data_list = []
        
        for url in urls:
            try:
                estimate_data = parser.parse_from_url(url)
                estimate_data_list.append(estimate_data)
            except Exception as e:
                logger.error(f"API: URLからのデータ抽出エラー: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f"無効なAWS Pricing Calculator URL: {url}"
                }), 400
        
        # データを合算
        merger = EstimateMerger()
        merged_data = merger.merge_estimates(estimate_data_list)
        
        # 結果を保存
        merged_id = str(uuid.uuid4())
        output_path = os.path.join(app.config['MERGED_ESTIMATES_FOLDER'], f"{merged_id}.json")
        with open(output_path, 'w') as f:
            json.dump(merged_data, f, indent=2)
        
        # AWS Calculator APIを使用してURLを生成
        calculator_api = CalculatorAPI()
        merged_url = calculator_api.generate_calculator_url(merged_data)
        
        return jsonify({
            'success': True,
            'message': f"{len(urls)}件の見積もりを合算しました。",
            'merged_url': merged_url,
            'instructions': "1. JSONファイルをダウンロードしてください\n2. AWS Pricing Calculatorにアクセス...",
            'data': {
                'name': merged_data.get('name', 'Merged Estimate'),
                'total_cost': calculator_api.calculate_total_cost(merged_data)
            },
            'id': merged_id
        })
            
    except Exception as e:
        logger.error(f"API: 見積もり合算中にエラーが発生: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"見積もりの合算中にエラーが発生しました: {str(e)}"
        }), 500

@app.route('/api/v1/estimate/<id>', methods=['GET'])
def api_get_estimate(id):
    """API: 合算された見積もりデータの詳細を取得する"""
    try:
        file_path = os.path.join(app.config['MERGED_ESTIMATES_FOLDER'], f"{id}.json")
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '指定されたIDの見積もりが見つかりません。'
            }), 404
            
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # AWS Calculator APIを使用して総コストを計算
        calculator_api = CalculatorAPI()
        total_cost = calculator_api.calculate_total_cost(data)
        
        # レスポンス用にデータを整形
        created_time = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
        
        return jsonify({
            'id': id,
            'name': data.get('name', 'Merged Estimate'),
            'created_at': created_time,
            'total_cost': total_cost,
            'services': calculator_api.extract_services(data)
        })
            
    except Exception as e:
        logger.error(f"API: 見積もり取得中にエラーが発生: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"見積もりの取得中にエラーが発生しました: {str(e)}"
        }), 500

@app.route('/api/v1/export/<format>', methods=['POST'])
def api_export_estimate(format):
    """API: 合算された見積もりデータをエクスポートする"""
    if format not in ['json', 'csv', 'pdf']:
        return jsonify({
            'success': False,
            'error': 'サポートされていないエクスポート形式です。'
        }), 400
        
    try:
        data = request.json
        if not data or 'urls' not in data or not data['urls']:
            return jsonify({
                'success': False,
                'error': 'URLsが提供されていません。'
            }), 400
            
        urls = data['urls']
        logger.info(f"API: エクスポート処理: {len(urls)}件のURL, 形式={format}")
        
        # URLからデータを抽出
        parser = EstimateParser()
        estimate_data_list = []
        
        for url in urls:
            try:
                estimate_data = parser.parse_from_url(url)
                estimate_data_list.append(estimate_data)
            except Exception as e:
                logger.error(f"API: URLからのデータ抽出エラー: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f"無効なAWS Pricing Calculator URL: {url}"
                }), 400
        
        # データを合算
        merger = EstimateMerger()
        merged_data = merger.merge_estimates(estimate_data_list)
        
        # 結果を保存
        merged_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        if format == 'json':
            output_path = os.path.join(app.config['MERGED_ESTIMATES_FOLDER'], f"{merged_id}.json")
            with open(output_path, 'w') as f:
                json.dump(merged_data, f, indent=2)
                
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"aws-merged-estimate-{timestamp}.json",
                mimetype='application/json'
            )
            
        elif format == 'csv':
            # TODO: CSVエクスポート機能の実装
            # 現在はサンプル実装
            calculator_api = CalculatorAPI()
            output_path = calculator_api.export_to_csv(merged_data, merged_id, app.config['MERGED_ESTIMATES_FOLDER'])
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"aws-merged-estimate-{timestamp}.csv",
                mimetype='text/csv'
            )
            
        elif format == 'pdf':
            # TODO: PDFエクスポート機能の実装
            # 現在はサンプル実装
            calculator_api = CalculatorAPI()
            output_path = calculator_api.export_to_pdf(merged_data, merged_id, app.config['MERGED_ESTIMATES_FOLDER'])
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"aws-merged-estimate-{timestamp}.pdf",
                mimetype='application/pdf'
            )
            
    except Exception as e:
        logger.error(f"API: エクスポート中にエラーが発生: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"エクスポート中にエラーが発生しました: {str(e)}"
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    """404エラーハンドラ"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500エラーハンドラ"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
