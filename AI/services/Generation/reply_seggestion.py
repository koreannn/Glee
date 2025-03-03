import os
from pathlib import Path
import yaml
import requests
import json

from loguru import logger
from app.core.settings import settings
from AI.utils.get_headers_payloads import get_headers_payloads
from AI.utils.deduplicate_sentence import deduplicate_sentences


class ReplySuggestion:
    def __init__(self):
        self.BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
        self.BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN") or settings.CLOVA_AI_BEARER_TOKEN
        # AI 디렉토리 경로로 수정
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent

    def _load_config(self, config_name: str) -> dict:
        config_path = self.BASE_DIR / "config" / config_name
        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    # config 바탕으로 답변 생성하는 함수
    def _generate_suggestions(self, input_text: str, config_name: str, num_suggestions: int = 3) -> list[str]:
        """공통 답변 생성 로직"""
        suggestions = []
        config = self._load_config(config_name)

        for _ in range(num_suggestions):
            headers, payload = get_headers_payloads(
                str(self.BASE_DIR / "config" / config_name), input_text, random_seed=True
            )
            response = requests.post(self.BASE_URL, headers=headers, json=payload, stream=True)

            if response.status_code == 200:
                reply_text = self._process_stream_response(response)
                reply_text = deduplicate_sentences(reply_text)
                suggestions.append(reply_text)
                logger.info(f"생성된 내용:\n{reply_text}")
            else:
                suggestions.append(f"Error: {response.status_code} - {response.text}")
        return suggestions

    # 스트림 응답을 처리하여 텍스트를 추출하는 함수
    def _process_stream_response(self, response) -> str:
        """스트림 응답을 처리하여 텍스트를 추출합니다."""
        reply_text = ""
        previous_token = ""  # 이전 토큰 저장용

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")

                    # 이전 토큰과 현재 토큰이 같지 않을 때만 추가
                    if token != previous_token:
                        reply_text += token
                        previous_token = token
                except Exception as e:
                    logger.error(f"Error processing stream response: {e}")
                    continue

        return reply_text.strip()  # 앞뒤 공백 제거

    def generate_basic_reply(self, situation_text: str) -> list[str]:  # 상황 -> 답변 생성 함수
        reply = self._generate_suggestions(situation_text, "config_Reply_Suggestions.yaml")
        return reply

    def generate_detailed_reply(  # 상황, 말투, 용도, 디테일한 내용 -> 답변 생성 함수
        self, situation_text: str, accent: str = None, purpose: str = None, detailed_description: str = "없음"
    ) -> list[str]:

        # 입력 텍스트 구성
        input_text = f"상황: {situation_text}"
        if accent and purpose:
            input_text += f"\n말투: {accent}\n용도: {purpose}"
        if detailed_description != "없음":
            input_text += f"\n사용자가 추가적으로 제공하는 디테일한 내용: {detailed_description}"

        reply = self._generate_suggestions(input_text, "config_New_Reply_Suggestions.yaml")
        return reply
