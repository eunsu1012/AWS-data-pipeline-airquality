# ☁️ AWS Data Pipeline - Seoul Air Quality

An automated serverless data pipeline that collects, processes,
and analyzes real-time air quality data across Seoul districts.
Built entirely on AWS Free Tier using Python and SQL.

---

## 📌 Overview

This project focuses on building an **end-to-end data pipeline** that automatically
collects air quality data from Korea's public API (에어코리아) every hour,
stores it in a cloud data lake, and generates district-level insights using SQL analytics.

The pipeline demonstrates core data engineering concepts including
ETL automation, serverless architecture, and cloud-based analytics.

---

## 🎯 Objectives

- Build a fully automated serverless data ingestion pipeline
- Design a scalable data lake architecture on AWS S3
- Analyze real-time air quality trends across Seoul districts
- Generate actionable insights from raw API data using SQL

---

## 🏗️ Architecture
```
EventBridge (hourly)
      ↓
AWS Lambda (Python)
      ↓
Amazon S3 (data lake)
      ↓
AWS Glue (schema catalog)
      ↓
Amazon Athena (SQL analytics)
      ↓
Matplotlib (visualization)
```

---

## 🧠 Key Features

- Fully automated hourly data collection with zero manual intervention
- Serverless ETL pipeline with no server management required
- Data lake with raw and processed layers for efficient querying
- SQL-based analytics generating district-level air quality insights
- Data cleaning to filter and standardize monitoring station categories

---

## ☁️ AWS Services Used

| Service | Purpose |
|---|---|
| AWS Lambda | Serverless hourly data collection (Python) |
| Amazon S3 | Data lake storage (raw + processed layers) |
| Amazon EventBridge | Hourly scheduling & automation |
| AWS Glue | Schema cataloging |
| Amazon Athena | SQL-based analytics & insights |

---

## 📊 Key Findings

- Analyzed PM2.5 and PM10 levels across 25 districts in Seoul
- 강남구 recorded the highest average PM2.5 (19.5 μg/m³)
- All districts exceeded WHO PM2.5 guideline of 15 μg/m³
- Pipeline processes 700+ records per day automatically

---

## 🔄 Pipeline Flow

1. EventBridge triggers Lambda every hour automatically
2. Lambda calls Korea Public Air Quality API (에어코리아)
3. Raw data saved as newline-delimited JSON to S3
4. AWS Glue catalogs the schema for SQL querying
5. Athena queries generate district-level insights
6. Results saved as Parquet files for efficient querying

---

## 📈 Visualizations

![Seoul Air Quality by District](air_quality_results.png)

---

## 🛠️ Tech Stack

- Python
- AWS Lambda / EventBridge
- Amazon S3
- AWS Glue
- Amazon Athena
- Matplotlib

---

## 📁 Project Structure

\```
AWS-data-pipeline-airquality/
│
├── lambda/              # Lambda function code
├── queries/             # Athena SQL queries
├── notebooks/           # Colab visualization notebook
├── results/             # Charts & outputs
└── README.md
\```

---

## 🚀 Results

- Fully automated pipeline running 24/7 at zero cost (AWS Free Tier)
- Successfully processed and analyzed 700+ air quality records
- Identified 강남구 as the district with highest PM2.5 levels in Seoul

---

## 👤 Developer

Park, Eunsoo

---

## ✔️ Summary

> A serverless AWS data pipeline that automatically collects, processes,
> and analyzes real-time air quality data across Seoul districts using
> Lambda, S3, Glue, and Athena.
