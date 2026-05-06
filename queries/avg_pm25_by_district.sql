-- Average PM2.5 by station (worst air quality areas)
SELECT stationname,
       AVG(CAST(pm25value AS DOUBLE)) AS avg_pm25,
       AVG(CAST(pm10value AS DOUBLE)) AS avg_pm10
FROM air_quality
WHERE pm25value != '-'
  AND pm10value != '-'
  AND stationname LIKE '%구'
GROUP BY stationname
ORDER BY avg_pm25 DESC;
