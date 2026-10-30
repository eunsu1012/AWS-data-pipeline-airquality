import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

import boto3

BUCKET = "air-quality-data-eunsu"
RAW_PREFIX = "processed/seoul-air-quality/"
OUT_PREFIX = "summaries/seoul-air-quality/"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-5-5")
API_KEY_PARAM = "/airquality/anthropic-api-key"
KST = timezone(timedelta(hours=9))
WHO_PM25_24H = 15.0  # WHO 2021 PM2.5 24시간 권고기준 (μg/m³)

s3 = boto3.client("s3")
ssm = boto3.client("ssm")
_api_key = None

SYSTEM_PROMPT = """당신은 서울시 대기질 데이터를 일반 시민에게 설명하는 분석가입니다.
규칙:
- <data> 안의 수치만 사용하세요. 데이터에 없는 수치, 원인(황사, 국외 유입 등), 예보는 지어내지 마세요.
- 한국어로 4~6문장의 단락 하나로 쓰세요. 마크다운, 목록, 제목은 쓰지 마세요.
- 서울 전체 평균과 등급을 먼저 말하고, 가장 나쁜 구와 가장 좋은 구를 수치와 함께 언급하세요.
- WHO 권고기준(PM2.5 24시간 평균 15㎍/㎥)을 넘은 구의 수를 언급하세요. mode가 latest면 1시간 측정값이라 24시간 기준과 직접 비교하기 어렵다는 점을 짧게 밝히세요.
- 마지막 문장은 등급에 맞는 행동 권고 한 문장으로 끝내세요."""


def get_api_key():
    key = ssm.get_parameter(
        Name=API_KEY_PARAM, WithDecryption=True
    )["Parameter"]["Value"].strip()
    if not key.isascii():
        raise ValueError("API 키에 특수문자(예: — 긴 대시)가 섞여 있어요. Parameter Store 값을 다시 넣어 주세요.")
    return key


def list_keys(prefix):
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        keys += [o["Key"] for o in page.get("Contents", [])]
    return sorted(keys)


def load_records(keys):
    records = []
    for key in keys:
        body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode("utf-8")
        for line in body.splitlines():
            if line.strip():
                # API 원본은 camelCase(stationName, pm25Value) → 소문자로 통일
                records.append({k.lower(): v for k, v in json.loads(line).items()})
    return records


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None  # '-' 등 결측값


def grade(value, cuts):
    for limit, label in cuts:
        if value <= limit:
            return label
    return "매우나쁨"


PM25_CUTS = [(15, "좋음"), (35, "보통"), (75, "나쁨")]
PM10_CUTS = [(30, "좋음"), (80, "보통"), (150, "나쁨")]


def compute_stats(records, mode):
    # 구 단위 측정소만 사용하고, 같은 측정소·시각 중복 제거
    seen, rows = set(), []
    for r in records:
        name, t = r.get("stationname") or "", r.get("datatime") or ""
        if not name.endswith("구") or (name, t) in seen:
            continue
        seen.add((name, t))
        rows.append(r)

    by_station = {}
    for r in rows:
        s = by_station.setdefault(r["stationname"], {"pm25": [], "pm10": []})
        for f, k in (("pm25value", "pm25"), ("pm10value", "pm10")):
            v = num(r.get(f))
            if v is not None:
                s[k].append(v)

    districts = []
    for name, s in by_station.items():
        if not s["pm25"]:
            continue
        pm25 = sum(s["pm25"]) / len(s["pm25"])
        pm10 = sum(s["pm10"]) / len(s["pm10"]) if s["pm10"] else None
        districts.append({"district": name, "pm25": round(pm25, 1),
                          "pm10": round(pm10, 1) if pm10 is not None else None})
    if not districts:
        return None

    districts.sort(key=lambda d: d["pm25"], reverse=True)
    seoul_pm25 = sum(d["pm25"] for d in districts) / len(districts)
    pm10_vals = [d["pm10"] for d in districts if d["pm10"] is not None]
    seoul_pm10 = sum(pm10_vals) / len(pm10_vals) if pm10_vals else None
    times = sorted(r["datatime"] for r in rows if r.get("datatime"))

    return {
        "mode": mode,
        "period": {"from": times[0], "to": times[-1]} if times else None,
        "district_count": len(districts),
        "seoul_avg": {
            "pm25": round(seoul_pm25, 1), "pm25_grade": grade(seoul_pm25, PM25_CUTS),
            "pm10": round(seoul_pm10, 1) if seoul_pm10 else None,
            "pm10_grade": grade(seoul_pm10, PM10_CUTS) if seoul_pm10 else None,
        },
        "worst_5_pm25": districts[:5],
        "best_3_pm25": districts[-3:][::-1],
        "over_who_pm25_count": sum(d["pm25"] > WHO_PM25_24H for d in districts),
        "who_pm25_24h_guideline": WHO_PM25_24H,
    }


def call_claude(stats, retries=2):
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "output_config": {"effort": "low"},
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": f"<data>\n{json.dumps(stats, ensure_ascii=False)}\n</data>\n\n위 데이터로 대기질 요약을 작성해 주세요.",
        }],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": get_api_key(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=50) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            # 429(요청 과다), 529(서버 혼잡), 5xx만 재시도
            if attempt < retries and (e.code in (429, 529) or e.code >= 500):
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"Claude API error {e.code}: {e.read().decode('utf-8', 'ignore')}")

    stop_reason = data.get("stop_reason")
    usage = data.get("usage", {})
    print(f"stop_reason={stop_reason}, usage={usage}")

    # 응답에 thinking 블록이 먼저 올 수 있으니 type이 text인 것만 모음
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()
    if not text:
        raise RuntimeError(f"요약 문장이 비어 있어요 (stop_reason={stop_reason}). 저장하지 않습니다.")
    return text, usage


def lambda_handler(event, context):
    event = event or {}
    mode = event.get("mode", "latest")
    now_utc = datetime.now(timezone.utc)

    # 수집 Lambda가 UTC 기준으로 폴더를 만들므로 S3 경로는 UTC로 찾음
    if mode == "daily":
        day = event.get("date") or (now_utc.astimezone(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
        d = datetime.strptime(day, "%Y-%m-%d")
        keys = list_keys(f"{RAW_PREFIX}{d - timedelta(days=1):%Y/%m/%d}/") + \
               list_keys(f"{RAW_PREFIX}{d:%Y/%m/%d}/")
        # 레코드 안의 dataTime(한국 시간) 기준으로 해당 날짜만 남김
        records = [r for r in load_records(keys) if (r.get("datatime") or "").startswith(day)]
    else:
        keys = list_keys(f"{RAW_PREFIX}{now_utc:%Y/%m/%d}/") or \
               list_keys(f"{RAW_PREFIX}{now_utc - timedelta(days=1):%Y/%m/%d}/")
        records = load_records(keys[-1:])

    stats = compute_stats(records, mode)
    if stats is None:
        print("No valid records; skipping LLM call")
        return {"statusCode": 204, "message": "no data"}

    summary, usage = call_claude(stats)

    result = {
        "generated_at": now_utc.astimezone(KST).isoformat(),
        "model": MODEL,
        "stats": stats,
        "summary": summary,
        "usage": usage,
    }
    body = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
    now_kst = now_utc.astimezone(KST)
    folder = day.replace("-", "/") if mode == "daily" else now_kst.strftime("%Y/%m/%d")
    out_key = f"{OUT_PREFIX}{mode}/{folder}/{now_kst:%H%M%S}.json"
    for key in (out_key, f"{OUT_PREFIX}latest_{mode}.json"):
        s3.put_object(Bucket=BUCKET, Key=key, Body=body,
                      ContentType="application/json; charset=utf-8")

    print(f"Saved summary to s3://{BUCKET}/{out_key}")
    print(summary)
    return {"statusCode": 200, "summary": summary, "s3_key": out_key}
