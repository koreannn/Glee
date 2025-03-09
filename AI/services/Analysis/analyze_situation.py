from pathlib import Path

import httpx
import json
import os
import yaml

from loguru import logger

from app.core.settings import settings
from AI.utils.deduplicate_sentence import deduplicate_sentences
from AI.utils.get_headers_payloads import get_headers_payloads


class Analyze:
    def __init__(self):
        self.BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
        self.BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN") or settings.CLOVA_AI_BEARER_TOKEN
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent

    def _load_config(self, config_name: str) -> dict:
        config_path = self.BASE_DIR / "config" / config_name
        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _process_stream_response(self, response_text: str) -> str:
        # 스트림 응답 처리 -> 텍스트 추출
        result_text = ""
        previous_token = ""

        for line in response_text.splitlines():
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")

                    if token != previous_token:
                        result_text += token
                        previous_token = token
                except Exception as e:
                    logger.error(f"Error processing stream response: {e}")
                    continue

        return result_text.strip()

    async def make_api_request(self, config_name: str, input_text: str, random_seed: bool = False) -> str:
        # API 요청(+응답 처리)
        config_path = self.BASE_DIR / "config" / config_name
        headers, payload = get_headers_payloads(str(config_path), input_text, random_seed=random_seed)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                return self._process_stream_response(response.text)
        except httpx.RequestError as e:
            logger.error(f"API request failed: {e}")
            raise httpx.RequestError
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e}")
            raise httpx.HTTPStatusError

    def parse_style_analysis(self, result_text: str) -> tuple[str, str]:
        # 스타일 분석 결과 파싱
        try:
            if "말투" in result_text and "용도" in result_text:
                tone_start = result_text.find("말투:") + len("말투:")
                tone_end = result_text.find("\n", tone_start)
                tone = result_text[tone_start:tone_end].strip()

                use_case_start = result_text.find("용도:") + len("용도:")
                use_case_end = result_text.find("\n", use_case_start)
                use_case = result_text[use_case_start:use_case_end].strip()

                logger.info(f"\n말투: {tone}\n용도: {use_case}")
                return tone, use_case
        except Exception as e:
            logger.error(f"스타일 분석 파싱 오류: {e}")

        return "기본 말투", "일반적인 용도"

    async def situation_summary(self, conversation: str) -> str:  # 상황 요약
        result = await self.make_api_request("config_Situation_Summary.yaml", conversation)
        if result:
            result = deduplicate_sentences(result)
            logger.info(f"상황 요약: {result}")
            return result
        return ""

    async def style_analysis(self, conversation: str) -> tuple[str, str]:  # 말투, 용도 분석
        result = await self.make_api_request("config_Style_Analysis.yaml", conversation, random_seed=True)
        if result:
            return self.parse_style_analysis(result)
        return "기본 말투", "일반적인 용도"