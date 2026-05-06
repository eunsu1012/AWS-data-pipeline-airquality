CREATE EXTERNAL TABLE IF NOT EXISTS air_quality_db.air_quality (
  so2grade STRING,
  coflag STRING,
  khaivalue STRING,
  so2value STRING,
  covalue STRING,
  pm25flag STRING,
  pm10flag STRING,
  o3grade STRING,
  pm10value STRING,
  khaigrade STRING,
  pm25value STRING,
  sidoname STRING,
  no2flag STRING,
  no2grade STRING,
  o3value STRING,
  pm10grade STRING,
  so2flag STRING,
  datatime STRING,
  pm25grade STRING,
  cograde STRING,
  no2value STRING,
  stationname STRING,
  o3flag STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://air-quality-data-eunsu/processed/'
TBLPROPERTIES ('has_encrypted_data'='false');
