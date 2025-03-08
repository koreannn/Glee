import os
import sys
from dotenv import load_dotenv
from loguru import logger
from AI.services.Agent.ocr_agent import OcrAgent
from AI.services.Agent.orchestrator_agent import OrchestratorAgent
from AI.services.Agent.style_analysis_agent import StyleAnalysisAgent
from AI.services.Agent.summarizer_agent import SummarizerAgent

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import List, Tuple

load_dotenv()  # .env 파일 로드


class GleeAgent:

    ocr_agent = OcrAgent()

    @classmethod
    async def parse_suggestion(cls, suggestion: str) -> Tuple[str, str]:
        """제안 텍스트에서 제목과 내용을 추출합니다."""
        title = ""
        content = suggestion

        if "제목:" in suggestion:
            parts = suggestion.split("제목:", 1)
            if len(parts) > 1:
                content = parts[0].strip()
                title = parts[1].strip()

        return title, content

    # -------------------------------------------------------------------
    # [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
    @classmethod
    async def analyze_situation(cls, image_files: List[Tuple[str, bytes]]) -> str:
        if not image_files:
            raise ValueError("No image files provided.")

        # OCR 에이전트를 사용하여 텍스트 추출
        image_text = await cls.ocr_agent.run(image_files)

        # 상황 요약 에이전트를 사용하여 상황 분석
        summarizer_agent = SummarizerAgent()
        situation_string = summarizer_agent.run(image_text)

        return situation_string

    # [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
    @classmethod
    async def analyze_situation_accent_purpose(cls, image_files: List[Tuple[str, bytes]]) -> Tuple[str, str, str]:
        if not image_files:
            return "", "", ""

        # OCR 에이전트를 사용하여 텍스트 추출
        image_text = cls.ocr_agent.run(image_files)

        # 스타일 분석 에이전트를 사용하여 스타일 분석
        style_agent = StyleAnalysisAgent()
        _, situation, accent, purpose = style_agent.run(image_text)

        return situation, accent, purpose

    # -------------------------------------------------------------------
    # [3] 상황만을 기반으로 글 제안을 생성하는 함수
    @classmethod
    async def generate_suggestions_situation(cls, situation: str) -> tuple[[str], list[str]]:
        agent = OrchestratorAgent()
        result = agent.run_reply_mode(situation)
        return result["replies"], result["titles"]

    # -------------------------------------------------------------------
    # [4] 상황, 말투, 용도를 기반으로 글 제안을 생성하는 함수
    @classmethod
    async def generate_reply_suggestions_accent_purpose(
        cls, situation: str, accent: str, purpose: str
    ) -> tuple[list[str], list[str]]:
        agent = OrchestratorAgent()
        result = agent.run_manual_mode(situation, accent, purpose, "")
        return result["replies"], result["titles"]

    # -------------------------------------------------------------------
    # [5] 상황, 말투, 용도, 상세 설명을 기반으로 글 제안을 생성하는 함수
    @classmethod
    async def generate_reply_suggestions_detail(
        cls, situation: str, accent: str, purpose: str, detailed_description: str
    ) -> tuple[list[str], list[str]]:
        agent = OrchestratorAgent()
        result = agent.run_manual_mode(situation, accent, purpose, detailed_description)
        return result["replies"], result["titles"]
