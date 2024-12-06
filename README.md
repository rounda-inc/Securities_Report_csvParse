# Securities_Report_csvParse
有価証券報告書のPDFデータをClaudeのモデルを用いてCSVにパースする

# Cloud Run functionsにdeployする場合
- Cloud Run functionsの中身をそのままDeployする形
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

## LLMの出力例
```
企業名,年度,カテゴリ,項目名,数値,補足
株式会社ニトリホールディングス,2023年12月期第3四半期,全体,売上高,663746,既存店改装や客数対策により増収 原材料価格上昇の影響あるも円安対策を継続
株式会社ニトリホールディングス,2023年12月期第3四半期,全体,営業利益,97865,物流の内製化や拠点再配置による発送配達費削減に努める
株式会社ニトリホールディングス,2023年12月期第3四半期,全体,経常利益,101268,為替差益や受取利息等の営業外収益が寄与
株式会社ニトリホールディングス,2023年12月期第3四半期,全体,親会社株主に帰属する四半期純利益,68535,特別損失として減損損失512百万円を計上
株式会社ニトリホールディングス,2023年12月期第3四半期,セグメント,ニトリ事業売上高,579571,既存店改装や商品施策が奏功し増収
株式会社ニトリホールディングス,2023年12月期第3四半期,セグメント,島忠事業売上高,91169,新規出店効果あるも既存店売上が減少
```


# 補足
- sample.pyはローカルで検証可能なコードです
