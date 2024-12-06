import functions_framework
from google.cloud import secretmanager
from google.cloud import storage
import anthropic
import base64
import httpx
import pandas as pd
import io, os
import datetime, time

def get_secret(secret_id, version_id="latest"):
    """
    シークレットキーの取得
    """
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT")
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")

def authenticate_request(request):
    """
    シークレットキーと入力の照合
    """
    # リクエストヘッダーからAuthorizationを取得
    provided_secret = request.headers.get("Authorization")
    if not provided_secret:
        return False, "Authorization header missing"

    # Secret Managerからシークレットキーを取得
    secret_manager_key = os.getenv("SECRET_MANAGER_KEY")
    expected_secret = get_secret(secret_manager_key)
    if provided_secret != expected_secret:
        return False, "Invalid secret key"

    return True, "Authenticated successfully"

@functions_framework.http
def llm_parse_function(request):
    """
    本処理
    """

    try:

        # 認証チェック
        is_authenticated, message = authenticate_request(request)
        if not is_authenticated:
            return message, 401

        # 環境変数を取得
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        claude_secret_key = os.getenv('CLAUDE_SECRET_KEY')


        # PDF情報の設定、URLはリクエストのdataとして設定可能にする
        pdf_url = request.form.get('url')
        #sampleのPDF例（ニトリの四半期報告書－第52期第3四半期(2023/10/01－2023/12/31)）
        #pdf_url = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/pdf/S100SR91.pdf?sv=2020-08-04&st=2024-12-05T08%3A20%3A22Z&se=2034-02-08T15%3A00%3A00Z&sr=b&sp=rl&sig=dcXNR3bgmHUDhLzqd8RhSn%2B47so%2FJCroWpND41e1Y%2Fo%3D"
        pdf_data = base64.standard_b64encode(httpx.get(pdf_url).content).decode("utf-8")

        # 当日日付の取得
        dt_now = datetime.datetime.now()
        today_date = dt_now.strftime('%Y%m%d')

        # GCSクライアントの作成
        gcs_client = storage.Client()
        bucket = gcs_client.get_bucket(bucket_name)

        # Claudeクライアント呼び出し
        claude_client = anthropic.Anthropic(
            api_key=claude_secret_key
        )

        # 連続でAPIをリクエストするとエラー（コード：429でper minuteの上限が40000トークンエラー）になるので暫定回避
        #time.sleep(60)

        # リクエスト
        message = claude_client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            betas=["pdfs-2024-09-25"],
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "添付の資料は企業の四半期報告書です。資料に含まれる財務諸表から項目を抜き出してください\
                                出力されたデータはデータベースに連携するため、カンマ区切りのCSVで出力してください。それ以外の文章の出力は不要です。csv形式のデータのみを出力してください\
                                出力するcsvデータのヘッダーは下記としてください\
                                |企業名|年度|カテゴリ|項目名|数値|補足|\
                                \
                                続けてヘッダーに含む情報の補足を記載します\
                                企業名：取得している企業の和名正式名称を記載すること、例：トヨタ自動車株式会社\
                                年度：取得できた年度を記載する、例：2022年12月期第3四半期\
                                カテゴリ：会社全体全体の収益を表す:全体 または、セグメントや内訳を示す場合：セグメント の2つのどちらかを選択すること\
                                項目名：企業にとって重要と思われる項目を記載すること、例：営業収益\
                                数値：項目に紐づく数値を記載すること、数値を区切るカンマは不要、単位は百万円として記載は不要、単位が千円などの場合は小数点を使って修正してください。数字のみ記載すること\
                                補足：その数値がなぜそのような結果になったか、起因する情報をまとめて100文字以内で記載し文章内にはカンマやクォーテーションを含めないこと、資料内の各状況に記載することが参考になる\
                                "
                                
                        }
                    ]
                }
            ],
        )

        # データの保存
        response = message.content[0].text

        csv_buffer = io.StringIO(response)
        df_resp = pd.read_csv(csv_buffer, header=0, sep=',',lineterminator='\n')
        company_name = df_resp["企業名"].unique()[0]
        year = df_resp["年度"].unique()[0]

        out_file_name = "{}_{}_{}.csv".format(today_date, company_name, year)
        #df_resp.to_csv(out_file_name, index = False)

        # ファイルをGCSにアップロード
        blob = bucket.blob(out_file_name)
        blob.upload_from_string(csv_buffer.getvalue(), content_type='text/csv')

        return f"DataFrame CSV file '{out_file_name}' successfully uploaded to bucket '{bucket_name}'.", 200
    
    except Exception as e:
        return f"An error occurred: {str(e)}", 500