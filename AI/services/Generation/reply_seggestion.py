import os
import json
import yaml
import httpx
import asyncio
from pathlib import Path
from loguru import logger

from app.core.settings import settings
from AI.utils.get_headers_payloads import get_headers_payloads
from AI.utils.deduplicate_sentence import deduplicate_sentences


class ReplySuggestion:
    def __init__(self):
        self.BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
        self.BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN") or settings.CLOVA_AI_BEARER_TOKEN
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent

    def _load_config(self, config_name: str) -> dict:
        config_path = self.BASE_DIR / "config" / config_name
        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    async def _fetch_reply(self, client: httpx.AsyncClient, input_text: str, config_name: str) -> str:
        """비동기적으로 AI API 요청을 보내고 응답을 처리"""
        headers, payload = get_headers_payloads(
            str(self.BASE_DIR / "config" / config_name), input_text, random_seed=True
        )

        try:
            response = await client.post(self.BASE_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return await self._process_stream_response(response)
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"API 요청 중 오류 발생: {e}")
            return f"Error: {str(e)}"

    async def generate_suggestions(self, input_text: str, config_name: str, num_suggestions: int = 3) -> list[str]:
        """비동기로 여러 개의 답변을 생성"""
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_reply(client, input_text, config_name) for _ in range(num_suggestions)]
            suggestions = await asyncio.gather(*tasks)

        for suggestion in suggestions:
            logger.info(f"생성된 답변: {suggestion}")

        return suggestions

    async def _process_stream_response(self, response: httpx.Response) -> str:
        """비동기적으로 스트림 응답을 처리하여 텍스트 추출"""
        reply_text = ""
        previous_token = ""

        async for line in response.aiter_lines():
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")

                    if token != previous_token:
                        reply_text += token
                        previous_token = token
                except Exception as e:
                    logger.error(f"스트림 응답 처리 중 오류 발생: {e}")
                    continue

        return deduplicate_sentences(reply_text.strip())

    async def generate_basic_reply(self, situation_text: str) -> list[str]:
        """상황 -> 답변 생성 함수 (비동기)"""
        return await self.generate_suggestions(situation_text, "config_Reply_Suggestions.yaml")

    async def generate_detailed_reply(
        self, situation_text: str, accent: str = None, purpose: str = None, detailed_description: str = "없음"
    ) -> list[str]:
        """상황, 말투, 용도, 추가 설명을 포함한 답변 생성 함수 (비동기)"""
        input_text = f"상황: {situation_text}"
        if accent and purpose:
            input_text += f"\n말투: {accent}\n용도: {purpose}"
        if detailed_description != "없음":
            input_text += f"\n사용자가 추가적으로 제공하는 디테일한 내용: {detailed_description}"

        return await self.generate_suggestions(input_text, "config_Reply_Suggestions_accent_purpose.yaml")
