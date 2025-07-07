from flask import Flask
from src.ui.routes import register_routes

def create_app():
    """アプリケーションファクトリ関数"""
    app = Flask(__name__)
    
    # 設定の読み込み
    app.config.from_mapping(
        SECRET_KEY='dev',
        # その他の設定をここに追加
    )
    
    # ルートの登録
    register_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
