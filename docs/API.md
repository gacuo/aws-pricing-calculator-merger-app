# API リファレンス

AWS Pricing Calculator 見積もり合算ツールのAPI仕様書です。

## 概要

このAPIは複数のAWS Pricing Calculator見積もりURLを入力として受け取り、合算されたデータを返します。

## ベースURL

```
https://{環境ドメイン}/api/v1
```

## エンドポイント

### 見積もりの合算

**エンドポイント**: `/merge`

**メソッド**: POST

**説明**: 複数のAWS Pricing Calculator見積もりURLを合算して結果を返します。

**リクエスト**:

Content-Type: `application/json`

```json
{
  "urls": [
    "https://calculator.aws/#/estimate?id=123456abcdef",
    "https://calculator.aws/#/estimate?id=789012ghijkl"
  ]
}
```

**レスポンス**:

成功時 (200 OK):

```json
{
  "success": true,
  "message": "2件の見積もりを合算しました。",
  "merged_url": "https://calculator.aws/#/estimate?id=abcdef123456",
  "instructions": "1. JSONファイルをダウンロードしてください\n2. AWS Pricing Calculatorにアクセス...",
  "data": {
    "name": "Merged: Estimate1 + Estimate2",
    "total_cost": {
      "monthly": "1,234.56 USD",
      "upfront": "0.00 USD",
      "12_months": "14,814.72 USD"
    }
  }
}
```

エラー時 (400 Bad Request):

```json
{
  "success": false,
  "error": "無効なAWS Pricing Calculator URL: https://example.com"
}
```

エラー時 (500 Internal Server Error):

```json
{
  "success": false,
  "error": "見積もりの合算中にエラーが発生しました: 詳細エラーメッセージ"
}
```

### 見積もりデータのエクスポート

**エンドポイント**: `/export/{format}`

**メソッド**: POST

**説明**: 合算された見積もりデータを指定されたフォーマットでエクスポートします。

**パスパラメータ**:
- `format`: エクスポート形式 (json, csv, pdf)

**リクエスト**:

Content-Type: `application/json`

```json
{
  "urls": [
    "https://calculator.aws/#/estimate?id=123456abcdef",
    "https://calculator.aws/#/estimate?id=789012ghijkl"
  ]
}
```

**レスポンス**:

成功時 (200 OK):

Content-Type: `application/json`, `text/csv`, または `application/pdf`

ファイルダウンロード

エラー時 (400 Bad Request):

```json
{
  "success": false,
  "error": "サポートされていないエクスポート形式です。"
}
```

### 見積もりデータの取得

**エンドポイント**: `/estimate/{id}`

**メソッド**: GET

**説明**: 合算された見積もりデータの詳細を取得します。

**パスパラメータ**:
- `id`: 見積もりID

**レスポンス**:

成功時 (200 OK):

```json
{
  "id": "abcdef123456",
  "name": "Merged Estimate",
  "created_at": "2023-05-01T12:34:56Z",
  "total_cost": {
    "monthly": "1,234.56 USD",
    "upfront": "0.00 USD",
    "12_months": "14,814.72 USD"
  },
  "services": [
    {
      "service_name": "Amazon EC2",
      "region": "ap-northeast-1",
      "upfront_cost": "0.00 USD",
      "monthly_cost": "500.00 USD",
      "description": "t3.large instances",
      "config": {
        "instances": 10
      }
    },
    {
      "service_name": "Amazon S3",
      "region": "ap-northeast-1",
      "upfront_cost": "0.00 USD",
      "monthly_cost": "100.00 USD",
      "description": "Standard storage",
      "config": {
        "storage_gb": 1000
      }
    }
  ]
}
```

エラー時 (404 Not Found):

```json
{
  "success": false,
  "error": "指定されたIDの見積もりが見つかりません。"
}
```

## エラーコード

| コード | 説明 |
|------|------|
| 400 | 無効なリクエスト（URLのフォーマット不正など） |
| 404 | リソースが見つからない |
| 429 | レート制限を超えた |
| 500 | サーバー内部エラー |

## レート制限

APIは以下のレート制限が適用されています：

- IPアドレスごとに1分間に最大60リクエスト
- 超過した場合は429レスポンスを返す

## 認証（将来実装予定）

将来的には、APIキーやOAuth2.0を使用した認証を実装予定です。

## 使用例

### cURLを使用した例

```bash
curl -X POST \
  https://calculator-merger.example.com/api/v1/merge \
  -H 'Content-Type: application/json' \
  -d '{
    "urls": [
      "https://calculator.aws/#/estimate?id=123456abcdef",
      "https://calculator.aws/#/estimate?id=789012ghijkl"
    ]
  }'
```

### Pythonを使用した例

```python
import requests
import json

url = "https://calculator-merger.example.com/api/v1/merge"
payload = {
    "urls": [
        "https://calculator.aws/#/estimate?id=123456abcdef",
        "https://calculator.aws/#/estimate?id=789012ghijkl"
    ]
}

response = requests.post(url, json=payload)
data = response.json()

if data["success"]:
    print("合算成功:", data["message"])
    print("合算URL:", data["merged_url"])
    print("月額コスト:", data["data"]["total_cost"]["monthly"])
else:
    print("エラー:", data["error"])
```
