CREATE TABLE air_quality_db.insights_pm25_ranking
WITH (
  format = 'PARQUET',
  external_location = 's3://air-quality-data-eunsu/processed/insights/'
) AS
SELECT stationname,
       AVG(CAST(pm25value AS DOUBLE)) AS avg_pm25,
       AVG(CAST(pm10value AS DOUBLE)) AS avg_pm10,
       AVG(CAST(khaivalue AS DOUBLE)) AS avg_khai
FROM air_quality
WHERE pm25value != '-'
  AND pm10value != '-'
  AND khaivalue != '-'
GROUP BY stationname
ORDER BY avg_pm25 DESC;
