import json
import urllib.request
import urllib.parse
import boto3
from datetime import datetime

ssm = boto3.client("ssm")
API_KEY = ssm.get_parameter(
    Name="/airquality/airkorea-api-key", WithDecryption=True
)["Parameter"]["Value"]
BUCKET_NAME = "air-quality-data-eunsu"

def lambda_handler(event, context):
    params = urllib.parse.urlencode({
        "serviceKey": API_KEY,
        "returnType": "json",
        "numOfRows": "100",
        "pageNo": "1",
        "sidoName": "서울",
        "ver": "1.0"
    })
    
    url = f"https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty?{params}"
    
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
    
    # Extract just the items array ← this is the fix
    items = data["response"]["body"]["items"]
    
    s3 = boto3.client("s3")
    timestamp = datetime.now().strftime("%Y/%m/%d/%H%M%S")
    
    # Save each record as a separate line (newline-delimited JSON)
    ndjson = "\n".join(json.dumps(item, ensure_ascii=False) for item in items)
    
    key = f"processed/seoul-air-quality/{timestamp}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=ndjson,
        ContentType="application/json"
    )
    
    print(f"Saved {len(items)} records to s3://{BUCKET_NAME}/{key}")
    return {"statusCode": 200, "records_saved": len(items)}
