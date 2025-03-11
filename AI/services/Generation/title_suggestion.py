import asyncio
import os
import httpx
import json
from pathlib import Path
from httpx import AsyncClient, ConnectTimeout, ReadTimeout
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
        # 대체 제목 목록 추가
        self.fallback_titles = [
            "이 내용이 도움이 될 거예요",
            "이런 방법을 시도해보세요",
            "전문가의 조언을 참고하세요",
            "이 팁이 문제 해결에 도움이 됩니다",
            "이 정보가 유용할 것입니다"
        ]

    async def fetch_title(self, client: AsyncClient, input_text: str, config_path: str) -> str:
        """비동기 요청을 보내고 제목을 생성"""
        headers, payload = get_headers_payloads(config_path, input_text)

        try:
            # 타임아웃 설정 추가 (10초)
            response = await client.post(
                self.BASE_URL, 
                headers=headers, 
                json=payload, 
                timeout=10.0
            )
            response.raise_for_status()
            title_text = ""

            async for line in response.aiter_lines():
                if line and line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        title_text += token
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 디코딩 오류 발생: {e}, 원본 데이터: {data_str}")
                        continue  # JSON 파싱 오류 발생 시 무시하고 계속 진행

            if not title_text:
                logger.warning("서버 응답이 비어 있음.")
                return self._get_fallback_title(input_text)

            return deduplicate_sentences(title_text)
            
        except (ConnectTimeout, ReadTimeout) as e:
            logger.error(f"API 연결 시간 초과: {e}")
            return self._get_fallback_title(input_text)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 오류: {e}")
            return self._get_fallback_title(input_text)
        except Exception as e:
            logger.error(f"제목 생성 중 예상치 못한 오류 발생: {e}")
            return self._get_fallback_title(input_text)

    def _get_fallback_title(self, input_text: str) -> str:
        """API 연결 실패 시 대체 제목 반환"""
        import random
        fallback_title = random.choice(self.fallback_titles)
        logger.info(f"대체 제목 사용: {fallback_title}")
        return fallback_title

    async def generate_title_suggestions(self, input_text: str) -> list[str]:
        """비동기로 여러 제목을 생성"""
        BASE_DIR = self.BASE_DIR
        config_path = str(BASE_DIR / "config" / "config_Title_Suggestion.yaml")

        try:
            # 타임아웃 설정 추가 (30초)
            async with httpx.AsyncClient(timeout=30.0) as client:
                tasks = [self.fetch_title(client, input_text, config_path) for _ in range(3)]
                titles = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외 처리: 예외가 발생한 경우 대체 제목으로 교체
            processed_titles = []
            for title in titles:
                if isinstance(title, Exception):
                    logger.error(f"제목 생성 중 오류 발생: {title}")
                    processed_titles.append(self._get_fallback_title(input_text))
                else:
                    processed_titles.append(title)
            
            # 중복 제거
            unique_titles = list(dict.fromkeys(processed_titles))
            
            # 제목이 3개 미만인 경우 대체 제목으로 채우기
            while len(unique_titles) < 3:
                fallback = self._get_fallback_title(input_text)
                if fallback not in unique_titles:
                    unique_titles.append(fallback)

            for title in unique_titles:
                logger.info(f"생성된 제목: {title}")

            return unique_titles[:3]  # 최대 3개 반환
            
        except Exception as e:
            logger.error(f"제목 생성 중 예상치 못한 오류 발생: {e}")
            # 모든 API 호출이 실패한 경우 대체 제목 3개 반환
            fallback_titles = []
            for _ in range(3):
                fallback_titles.append(self._get_fallback_title(input_text))
            return list(dict.fromkeys(fallback_titles))  # 중복 제거
