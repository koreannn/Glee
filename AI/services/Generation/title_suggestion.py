import os
import requests
import json
from pathlib import Path

from loguru import logger
from AI.utils.get_headers_payloads import get_headers_payloads
from AI.utils.get_headers_payloads import get_headers_payloads
from app.core.settings import settings

from AI.utils.deduplicate_sentence import deduplicate_sentences


class TitleSuggestion:
    def __init__(self):
        self.BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
        self.BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
        self.REQUEST_ID = os.getenv("CLOVA_REQ_ID_TITLE")

        if not self.BEARER_TOKEN or not self.REQUEST_ID:
            self.BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
            self.REQUEST_ID = settings.CLOVA_REQ_ID_TITLE

        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent

    def _generate_title_suggestions(self, input_text: str) -> list[str]:
        # (2) .env에서 불러오기
        BASE_URL = self.BASE_URL
        # BEARER_TOKEN = self.BEARER_TOKEN
        # REQUEST_ID = self.REQUEST_ID

        BASE_DIR = self.BASE_DIR

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
