import os
import requests
import json
from pathlib import Path

from loguru import logger
from utils.get_headers_payloads import get_headers_payloads
from app.core.settings import settings


def CLOVA_AI_Title_Suggestions(input_text: str) -> str:

    # (2) .env에서 불러오기
    BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
    REQUEST_ID = os.getenv("CLOVA_REQ_ID_TITLE")

    if not BEARER_TOKEN or not REQUEST_ID:
        BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
        REQUEST_ID = settings.CLOVA_REQ_ID_REPLY_SUMMARY

    BASE_DIR = Path(__file__).resolve().parent.parent

    # config 파일의 절대 경로 설정
    config_path = BASE_DIR / "config" / "config_Title_Suggestion.yaml"
    headers, payload = get_headers_payloads(str(config_path), input_text)
    # config = load_config(config_path)

    suggestions = []

    for _ in range(3):  # 새로 고침 하면 새로운 생성을 만들어내도록 수정
        headers, payload = get_headers_payloads(str(config_path), input_text)
        
        response = requests.post(BASE_URL, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            title_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        title_text += token
                    except Exception:
                        continue
            suggestions.append(title_text)
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
        logger.info(f"생성된 내용:\n {title_text}")
    return suggestions