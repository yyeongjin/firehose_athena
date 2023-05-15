CREATE TABLE join_data AS
SELECT
  ld.timestamp,
  ld.source,
  ld.log,
  cf.date,
  cf.location,
  cf.bytes,
  cf.method,
  cf.host,
  cf.uri
FROM
  (
    SELECT
      'localhost' AS request_ip,
      date,
      location,
      bytes,
      method,
      host,
      uri
    FROM
      cloudfront_logs
  ) AS cf
JOIN
  log_data AS ld ON cf.request_ip = ld.source;
