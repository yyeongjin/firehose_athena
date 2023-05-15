CREATE EXTERNAL TABLE IF NOT EXISTS log_data (
  `timestamp` STRING,
  `log` STRING,
  `source` STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://aws-data-demo-bucket/output/'
