## amazon ec2 instance userdata
```sh
#!/bin/bash
yum install python3-pip
yum install httpd -y
pip3 install boto3
systemctl restart httpd
```
->> Use the 'aws configure' command later to set the region

recodes.py
```sh
import boto3
import time
import json
import string
import random
import os

delivery_stream_name = "kine-data-stream"

firehose_client = boto3.client('firehose')

def get_random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

while True:
    # access_log 파일 내용이 빈 값인지 확인하고, 빈 값이면 프로그램 종료
    if os.path.getsize('/var/log/httpd/access_log') == 0:
        print("access_log file is empty. Stopping the program...")
        break

    # 로그 파일 읽기
    with open('/var/log/httpd/access_log', 'r') as f:
        logs = f.readlines()

    # 로그를 레코드로 변환하여 Delivery Stream에 전송
    records = []
    for log in logs:
        if "127.0.0.1" in log:
            source = "localhost"
        else:
            source = "externalhost"
        record = {
            "timestamp": str(time.time()),
            "log": log,
            "source": source
        }
        records.append({"Data": json.dumps(record)})

    response = firehose_client.put_record_batch(
        DeliveryStreamName=delivery_stream_name,
        Records=records
    )

    print(response['ResponseMetadata']['HTTPStatusCode'])
    print(response)
        
    # access_log 파일 내용을 빈 값으로 대체
    open('/var/log/httpd/access_log', 'w').close()
```

The command
```
python3 recodes.py
```

----
## Creating S3 and Uploading Files

It is assumed that a directory called data/ was created in s3://aws-data-demo-bucket.

- Upload the following file.
```bash
aws s3 cp sample-cloudfront-access-logs s3://aws-data-demo-bucket/data/
```
----------
## Lambda

sample lambda code

-> Replace all contents of the log column with capital letters.

```py
import base64
import json

def lambda_handler(event, context):
    transformed_records = []

    for record in event['records']:
        payload = base64.b64decode(record['data'])
        data = json.loads(payload)

        # 데이터 변형 로직을 적용
        transformed_data = transform_data(data)

        # 변형된 데이터를 다시 인코딩
        transformed_payload = json.dumps(transformed_data).encode('utf-8')
        transformed_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(transformed_payload).decode('utf-8')
        }
        transformed_records.append(transformed_record)

    return {'records': transformed_records}

def transform_data(data):
    # 데이터 변형 로직을 구현
    transformed_data = {
        'timestamp': data['timestamp'],
        'log': data['log'].upper(),  # 예시로 로그를 대문자로 변환
        'source': data['source']
    }

    return transformed_data

```
-----
## Kinesis firehose

1. Creates a transmission stream
2. Enables lambda record conversion.
3. Performs dynamic partitioning.
- enable json inline parsing
- key: source
- value: .source
4. output prefix
- output/!{partitionKeyFromQuery:source}/

---

## Athena

1. Creating a cloudfront table
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS default.cloudfront_logs (
  `date` DATE,
  time STRING,
  location STRING,
  bytes BIGINT,
  request_ip STRING,
  method STRING,
  host STRING,
  uri STRING,
  status INT,
  referrer STRING,
  user_agent STRING,
  query_string STRING,
  cookie STRING,
  result_type STRING,
  request_id STRING,
  host_header STRING,
  request_protocol STRING,
  request_bytes BIGINT,
  time_taken FLOAT,
  xforwarded_for STRING,
  ssl_protocol STRING,
  ssl_cipher STRING,
  response_result_type STRING,
  http_version STRING,
  fle_status STRING,
  fle_encrypted_fields INT,
  c_port INT,
  time_to_first_byte FLOAT,
  x_edge_detailed_result_type STRING,
  sc_content_type STRING,
  sc_content_len BIGINT,
  sc_range_start BIGINT,
  sc_range_end BIGINT
)
ROW FORMAT DELIMITED 
FIELDS TERMINATED BY '\t'
LOCATION 's3://aws-data-demo-bucket/data/'
TBLPROPERTIES ( 'skip.header.line.count'='2' )

```

2. Creating a log table

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS log_data (
  `timestamp` STRING,
  `log` STRING,
  `source` STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://aws-data-demo-bucket/output/'
```

3. Creating a join table

```
Only some columns were selected in the cloudfront table, and the value of requests_ip in the cloudfront was replaced with localhost, and the log_data table was joined
```

```sql
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
```