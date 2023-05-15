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