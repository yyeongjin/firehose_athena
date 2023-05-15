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
