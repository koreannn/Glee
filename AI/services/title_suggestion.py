import os
import requests
import json
from pathlib import Path

from loguru import logger
from AI.utils.get_headers_payloads import get_headers_payloads
from AI.utils.get_headers_payloads import get_headers_payloads
from app.core.settings import settings

# from AI.utils.deduplicate_sentence import deduplicate_sentences


# 중복 방지 -> 함수 추가했습니다.
def deduplicate_sentences(text):
    text = text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    dedup_lines = []
    for line in lines:
        if not dedup_lines or dedup_lines[-1] != line:
            dedup_lines.append(line)

    new_text = "\n".join(dedup_lines)

    if len(new_text) > 0:
        half = len(new_text) // 2
        if len(new_text) % 2 == 0 and new_text[:half] == new_text[half:]:
            return new_text[:half].strip()

    return new_text


def CLOVA_AI_Title_Suggestions(input_text: str) -> list[str]:

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

    titles = []

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
            title_text = deduplicate_sentences(title_text)
            titles.append(title_text)
        else:
            titles.append(f"Error: {response.status_code} - {response.text}")
        logger.info(f"생성된 내용:\n {title_text}")
    return titles
