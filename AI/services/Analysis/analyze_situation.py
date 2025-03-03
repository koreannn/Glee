from pathlib import Path

import requests
import json

from loguru import logger

from AI.utils.deduplicate_sentence import deduplicate_sentences
from AI.utils.get_headers_payloads import get_headers_payloads


def CLOVA_AI_Situation_Summary(conversation: str) -> str:
    # (2) .env에서 불러오기

    URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"

    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    # config 파일의 절대 경로 설정
    config_path = BASE_DIR / "config" / "config_Situation_Summary.yaml"
    headers, payload = get_headers_payloads(str(config_path), conversation)

    response = requests.post(URL, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")
                    result_text += token
                except Exception:
                    continue
        result_text = deduplicate_sentences(result_text)
        logger.info(f"상황 요약: {result_text}")
        return result_text
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return ""
