#!/usr/bin/env python3
"""
AWS Pricing Calculator 見積もり合算ツール

複数のAWS Pricing Calculator見積もりURLを入力として受け取り、
それらを合算した結果を表示するウェブアプリケーション。
"""

import os
import logging
import json
import uuid
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.exceptions import NotFound, InternalServerError
from dotenv import load_dotenv
from src.data.parser import EstimateParser
from src.merger.estimate_merger import EstimateMerger
from src.api.calculator_api import CalculatorAPI

# 環境変数の読み込み
load_dotenv()

# アプリケーション設定
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# 出力ディレクトリの設定
MERGED_ESTIMATES_DIR = os.environ.get("MERGED_ESTIMATES_DIR", "merged_estimates")
JSON_SAMPLES_DIR = os.environ.get("JSON_SAMPLES_DIR", "json_samples")
LOG_DIR = os.environ.get("LOG_DIR", "logs")

# ディレクトリの作成
os.makedirs(MERGED_ESTIMATES_DIR, exist_ok=True)
os.makedirs(JSON_SAMPLES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "app.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# コンポーネント初期化
parser = EstimateParser()
merger = EstimateMerger()
calculator_api = CalculatorAPI()


@app.route("/")
def index():
    """ホームページ表示"""
    return render_template("index.html")


@app.route("/merge", methods=["POST"])
def merge_estimates():
    """
    複数の見積もりURLを合算する
    
    フォームデータ:
        urls: 見積もりURLのリスト
        
    Returns:
        JSON: 合算結果データ
    """
    try:
        # URLリスト取得
        urls = request.form.getlist("urls")
        
        if not urls:
            return jsonify({"success": False, "error": "URLが提供されていません"}), 400
        
        # 各URLからデータを抽出
        estimate_data_list = []
        for url in urls:
            try:
                estimate_data = parser.parse_from_url(url)
                estimate_data_list.append(estimate_data)
            except ValueError as e:
                logger.error(f"URLの解析エラー: {str(e)}")
                return jsonify({"success": False, "error": f"URLの解析エラー: {str(e)}"}), 400
        
        # データを合算
        merged_estimate = merger.merge_estimates(estimate_data_list)
        
        # 合算URLを生成
        merged_url = calculator_api.generate_calculator_url(merged_estimate)
        
        # 総コスト計算
        total_cost = calculator_api.calculate_total_cost(merged_estimate)
        
        # JSONファイル保存
        estimate_id = str(uuid.uuid4())
        json_path = os.path.join(MERGED_ESTIMATES_DIR, f"{estimate_id}.json")
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(merged_estimate, f, ensure_ascii=False, indent=2)
        
        # レスポンス作成
        response_data = {
            "success": True,
            "merged_url": merged_url,
            "download_url": f"/download/{estimate_id}",
            "data": {
                "name": merged_estimate.get("name", "合算見積もり"),
                "total_cost": total_cost,
                "service_count": len(merged_estimate.get("services", []))
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.exception("見積もり合算中にエラーが発生")
        return jsonify({
            "success": False,
            "error": f"処理中にエラーが発生しました: {str(e)}"
        }), 500


@app.route("/download/<estimate_id>", methods=["GET"])
def download_estimate(estimate_id):
    """
    合算された見積もりデータをダウンロードする
    
    Args:
        estimate_id: 見積もりID
        
    Returns:
        File: JSONファイル
    """
    try:
        json_path = os.path.join(MERGED_ESTIMATES_DIR, f"{estimate_id}.json")
        
        if not os.path.exists(json_path):
            logger.error(f"見積もりファイルが見つかりません: {estimate_id}")
            return jsonify({
                "success": False,
                "error": "見積もりファイルが見つかりません"
            }), 404
        
        return send_file(
            json_path,
            as_attachment=True,
            download_name=f"aws-pricing-merged-{estimate_id[:8]}.json",
            mimetype="application/json"
        )
    
    except Exception as e:
        logger.exception("ファイルダウンロード中にエラーが発生")
        return jsonify({
            "success": False,
            "error": f"ファイルダウンロード中にエラーが発生: {str(e)}"
        }), 500


@app.route("/export/<format>/<estimate_id>", methods=["GET"])
def export_estimate(format, estimate_id):
    """
    見積もりデータを指定された形式でエクスポート
    
    Args:
        format: エクスポート形式 (csv, pdf)
        estimate_id: 見積もりID
        
    Returns:
        File: エクスポートファイル
    """
    try:
        json_path = os.path.join(MERGED_ESTIMATES_DIR, f"{estimate_id}.json")
        
        if not os.path.exists(json_path):
            logger.error(f"見積もりファイルが見つかりません: {estimate_id}")
            return jsonify({
                "success": False,
                "error": "見積もりファイルが見つかりません"
            }), 404
        
        # JSONファイル読み込み
        with open(json_path, "r", encoding="utf-8") as f:
            estimate_data = json.load(f)
        
        # 一時ディレクトリの作成
        with tempfile.TemporaryDirectory() as temp_dir:
            if format.lower() == "csv":
                output_path = calculator_api.export_to_csv(estimate_data, estimate_id, temp_dir)
                mimetype = "text/csv"
                extension = "csv"
            elif format.lower() == "pdf":
                output_path = calculator_api.export_to_pdf(estimate_data, estimate_id, temp_dir)
                mimetype = "application/pdf"
                extension = "pdf"
            else:
                return jsonify({
                    "success": False,
                    "error": "サポートされていない形式です"
                }), 400
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"aws-pricing-merged-{estimate_id[:8]}.{extension}",
                mimetype=mimetype
            )
    
    except Exception as e:
        logger.exception(f"エクスポート中にエラーが発生: {format}")
        return jsonify({
            "success": False,
            "error": f"エクスポート中にエラーが発生: {str(e)}"
        }), 500


@app.route("/sample/<sample_id>", methods=["GET"])
def get_sample(sample_id):
    """
    サンプルデータを取得する
    
    Args:
        sample_id: サンプルID
        
    Returns:
        File: JSONファイル
    """
    try:
        sample_path = os.path.join(JSON_SAMPLES_DIR, f"{sample_id}.json")
        
        if not os.path.exists(sample_path):
            logger.error(f"サンプルファイルが見つかりません: {sample_id}")
            return jsonify({
                "success": False,
                "error": "サンプルファイルが見つかりません"
            }), 404
        
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        
        return jsonify({
            "success": True,
            "data": sample_data
        })
    
    except Exception as e:
        logger.exception("サンプルデータ取得中にエラーが発生")
        return jsonify({
            "success": False,
            "error": f"サンプルデータ取得中にエラーが発生: {str(e)}"
        }), 500


@app.errorhandler(404)
def page_not_found(e):
    """404エラーハンドラ"""
    logger.info("404 Not Found: %s", request.path)
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    """500エラーハンドラ"""
    logger.error("500 Server Error: %s", str(e))
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("DEBUG", "False").lower() == "true")
