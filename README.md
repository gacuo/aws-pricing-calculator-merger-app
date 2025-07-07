# AWS Pricing Calculator 見積もり合算ツール

複数のAWS Pricing Calculatorの見積もりURLを入力として受け取り、すべての見積もりを合算した結果を表示するツールです。

## 機能

- 複数のAWS Pricing Calculator見積もりURLを入力
- サービスごとのコスト合算
- 同一サービス・リージョンの設定マージ
- 合算結果のサマリーを表示
- 合算見積もりを新しいURLとして生成

## 使い方

### 環境設定

```bash
# リポジトリのクローン
git clone https://github.com/gacuo/aws-pricing-calculator-merger.git
cd aws-pricing-calculator-merger

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 起動方法

```bash
python app.py
```

ブラウザで http://localhost:5000 にアクセスすると、見積もり合算ツールが表示されます。

## 利用方法

1. AWS Pricing Calculatorで見積もりを作成し、「Export」からJSONファイルをダウンロードするか、共有URLを取得します。
2. このツールの入力欄に見積もりのURLを入力します（複数可）。
3. 「見積もりを合算」ボタンをクリックします。
4. 合算結果のURLとサマリーが表示されます。

## システム構成

- `app.py` - アプリケーションエントリポイント
- `src/api/calculator_api.py` - AWS Pricing Calculator API操作
- `src/data/parser.py` - 見積もりデータ解析
- `src/merger/cost_merger.py` - コスト合算ロジック
- `src/ui/routes.py` - Webルーティング
- `templates/` - HTMLテンプレート

## 注意事項

- 実装の制限として、現在のバージョンではAWS Pricing CalculatorのJSONファイルを直接解析し、AWS APIの実際の制約の範囲内で動作するようにしています。
- AWS Pricing Calculatorの仕様が変更された場合、このツールも更新が必要になる場合があります。

## ライセンス

このプロジェクトはMITライセンスで提供されています。
