import requests
import uuid
import time
import json

api_url = "https://whh0dl4f9y.apigw.ntruss.com/custom/v1/38974/2cd995e5d2f00862d51113bac30d5f64ac58855e430cc9d1e7b7241f9ac05efb/general"
secret_key = "YlJqSGpCT3dWTUt4SEhtd3JjdUhvVERtVVpRY3BLZEs="
image_file = "./AI/OCR_Test1.png"

request_json = {
    "images": [{"format": "png", "name": "demo"}],
    "requestId": str(uuid.uuid4()),
    "version": "V2",
    "timestamp": int(round(time.time() * 1000)),
}

payload = {"message": json.dumps(request_json).encode("UTF-8")}
files = [("file", open(image_file, "rb"))]
headers = {"X-OCR-SECRET": secret_key}

response = requests.request("POST", api_url, headers=headers, data=payload, files=files)

print(response.text.encode("utf8"))
