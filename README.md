# AWS Pricing Calculator Merger

AWS Pricing Calculatorの複数エクスポートURLを合算するツールです。複数の見積もりURLを入力として受け取り、それらを組み合わせた新しいAWS Pricing Calculator URLを生成します。

## 機能

- 複数のAWS Pricing Calculator URLの解析
- 見積もりデータの抽出と合算処理
- 合算されたデータに基づく新しい見積もりURLの生成
- シンプルなWebインターフェースによる操作

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/gacuo/aws-pricing-calculator-merger.git
cd aws-pricing-calculator-merger

# 仮想環境の作成とアクティベート
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scriptsctivate

# 依存パッケージのインストール
pip install -r requirements.txt

# アプリケーションの実行
python app.py
```

## 使用方法

1. ブラウザで `http://localhost:5000` にアクセス
2. フォームに複数のAWS Pricing Calculator エクスポートURLを入力
3. 「合算」ボタンをクリック
4. 新しく生成された合算済みのURLを取得

## 技術スタック

- Python 3.8+
- Flask (Webフレームワーク)
- requests (HTTP通信)
- beautifulsoup4 (HTMLパース)
