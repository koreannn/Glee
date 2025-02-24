import requests
import uuid
import time
import json
import yaml

def load_config(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config


config = load_config("./config_OCR.yaml")

api_url = config["API"]["APIGW_Invoke_URL"]
secret_key = config["API"]["SECRET_KEY"]
image_file = config["API"]["IMG_DIR"]

request_json = {
    'images': [
        {
            'format': 'png',
            'name': 'demo'
        }
    ],
    'requestId': str(uuid.uuid4()),
    'version': 'V2',
    'timestamp': int(round(time.time() * 1000))
}

payload = {'message': json.dumps(request_json).encode('UTF-8')}
files = [('file', open(image_file,'rb'))]
headers = {'X-OCR-SECRET': secret_key}

response = requests.request("POST", api_url, headers=headers, data=payload, files=files)
result = response.json()

# 결과를 JSON 파일로 저장
with open('result.json', 'w', encoding='utf-8') as make_file:
    json.dump(result, make_file, indent="\t", ensure_ascii=False)

# 텍스트 추출
text = ""
for field in result['images'][0]['fields']:
    text += field['inferText'] + " "
print(text)
