import asyncio
import os
import httpx
import json
from pathlib import Path
from httpx import AsyncClient
from loguru import logger

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

    async def fetch_title(self, client: AsyncClient, input_text: str, config_path: str) -> str:
        """비동기 요청을 보내고 제목을 생성"""
        headers, payload = get_headers_payloads(config_path, input_text)

        try:
            response = await client.post(self.BASE_URL, headers=headers, json=payload)
            if response.status_code == 200:
                title_text = ""
                async for line in response.aiter_lines():
                    if line and line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        try:
                            data_json = json.loads(data_str)
                            token = data_json.get("message", {}).get("content", "")
                            title_text += token
                        except Exception:
                            continue
                return deduplicate_sentences(title_text)
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"API 요청 중 오류 발생: {e}")
            return f"Error: {str(e)}"



    async def generate_title_suggestions(self, input_text: str) -> list[str]:
        """비동기로 여러 제목을 생성"""
        BASE_DIR = self.BASE_DIR
        config_path = str(BASE_DIR / "config" / "config_Title_Suggestion.yaml")

        async with httpx.AsyncClient() as client:
            tasks = [self.fetch_title(client, input_text, config_path) for _ in range(3)]
            titles = await asyncio.gather(*tasks)

        for title in titles:
            logger.info(f"생성된 제목: {title}")

        return titles
