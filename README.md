# Securities_Report_csvParse
有価証券報告書のPDFデータをClaudeのモデルを用いてCSVにパースする

# Google Cloud Functionにdeployする場合
- Google_CloudFunctionRunの中身をそのままDeployする形
- Function側のトリガーはHTTPを想定しており、secret managerによる設定キーとの照合プロセスをコード内に記載
  - そのため事前にsecret managerにて事前にシークレットを発行し、デプロイ時に環境変数として与えるようにすること
  - https://console.cloud.google.com/security/secret-manager

## デプロイ時のコマンド例
```
gcloud functions deploy llm_parse_function \
    --project [プロジェクトID]\
    --runtime python312 \
    --memory 512 \
    --timeout 300 \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars GCP_PROJECT=[プロジェクトID] \
    --set-env-vars SECRET_MANAGER_KEY=[secret managerで発行したシークレット名] \
    --set-env-vars GCS_BUCKET_NAME=[アップロードするCloud Storageのバケット名] \
    --set-env-vars CLAUDE_SECRET_KEY=[ClaudeのAPIキー]
```

## APIリクエスト時のコマンド例
```
curl -X POST [Functionで発行されたエンドポイントURL] \
    -H "Authorization: [secret managerで設定したpass]" \
    -d "url=https://disclosure2dl.edinet-fsa.go.jp/searchdocument/pdf/S100SR91.pdf?sv=2020-08-04&st=2024-12-05T08%3A20%3A22Z&se=2034-02-08T15%3A00%3A00Z&sr=b&sp=rl&sig=dcXNR3bgmHUDhLzqd8RhSn%2B47so%2FJCroWpND41e1Y%2Fo%3D"
```

# 補足
- sample.pyはローカルで検証できる用のコード
