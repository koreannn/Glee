import os
import sys
import random
import uuid
import time
import json
from dotenv import load_dotenv
import re
import requests
from loguru import logger

import tempfile


# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from app.core.settings import settings
from pathlib import Path
from PIL import Image, ImageOps
import hashlib
from io import BytesIO
from typing import List, Tuple, Dict, Optional, Union


load_dotenv()  # .env 파일 로드

# 상대 경로로 임포트 변경
from services.Generation.reply_seggestion import ReplySuggestion
from services.OCR.get_ocr_text import CLOVA_OCR
from services.Analysis.analyze_situation import Analyze
from services.Generation.title_suggestion import TitleSuggestion
from services.videosearch_service import VideoSearchService

ocr_service = CLOVA_OCR()
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
video_search_service = VideoSearchService()


# 1. 상황, 말투, 용도 파싱하는 부분
# 2. 제목, 답변 파싱하는 부분 이렇게 두 가지 확읺해야함


def parse_style_analysis(result: str) -> Tuple[str, str, str]:
    """스타일 분석 결과에서 상황, 말투, 용도를 추출합니다."""
    situation = ""
    accent = ""
    purpose = ""

    for line in result.strip().split("\n"):
        line = line.strip()
        if line.startswith("상황:"):
            situation = line.replace("상황:", "").strip()
        elif line.startswith("말투:"):
            accent = line.replace("말투:", "").strip()
        elif line.startswith("용도:"):
            purpose = line.replace("용도:", "").strip()

    return situation, accent, purpose


def parse_suggestion(suggestion: str) -> Tuple[str, str]:
    """제안 텍스트에서 제목과 내용을 추출합니다."""
    title = ""
    content = suggestion

    if "제목:" in suggestion:
        parts = suggestion.split("제목:", 1)
        if len(parts) > 1:
            content = parts[0].strip()
            title = parts[1].strip()

    return title, content


# 헬퍼 함수: OCR 결과 JSON에서 텍스트 추출
def extract_text_from_ocr_result(ocr_result) -> str:
    """OCR 결과에서 텍스트를 추출합니다."""
    if isinstance(ocr_result, str):
        return ocr_result

    try:
        if isinstance(ocr_result, dict) and "images" in ocr_result:
            extracted_text = ""
            for image in ocr_result["images"]:
                if "fields" in image:
                    for field in image["fields"]:
                        if "inferText" in field:
                            extracted_text += field["inferText"] + " "
            return extracted_text.strip()
    except Exception as e:
        logger.error(f"OCR 결과 파싱 중 오류 발생: {e}")

    return ""


# -------------------------------------------------------------------
# [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
def analyze_situation(image_files: List[Tuple[str, bytes]]) -> str:
    if not image_files:
        return ""

    # OCR 에이전트를 사용하여 텍스트 추출
    ocr_agent = OcrAgent()
    image_text = ocr_agent.run(image_files)

    # 상황 요약 에이전트를 사용하여 상황 분석
    summarizer_agent = SummarizerAgent()
    situation_string = summarizer_agent.run(image_text)

    return situation_string


# [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
def analyze_situation_accent_purpose(image_files: List[Tuple[str, bytes]]) -> Tuple[str, str, str]:
    if not image_files:
        return "", "", ""

    # OCR 에이전트를 사용하여 텍스트 추출
    ocr_agent = OcrAgent()
    image_text = ocr_agent.run(image_files)

    # 스타일 분석 에이전트를 사용하여 스타일 분석
    style_agent = StyleAnalysisAgent()
    _, situation, accent, purpose = style_agent.run(image_text)

    return situation, accent, purpose


# -------------------------------------------------------------------
# [3] 상황만을 기반으로 글 제안을 생성하는 함수
def generate_suggestions_situation(situation: str) -> tuple[list[str], list[str]]:
    agent = OrchestratorAgent()
    result = agent.run_reply_mode(situation)
    return result["replies"], result["titles"]


# -------------------------------------------------------------------
# [4] 상황, 말투, 용도를 기반으로 글 제안을 생성하는 함수
def generate_reply_suggestions_accent_purpose(situation: str, accent: str, purpose: str) -> tuple[list[str], list[str]]:
    agent = OrchestratorAgent()
    result = agent.run_manual_mode(situation, accent, purpose, "")
    return result["replies"], result["titles"]


# -------------------------------------------------------------------
# [5] 상황, 말투, 용도, 상세 설명을 기반으로 글 제안을 생성하는 함수
def generate_reply_suggestions_detail(
    situation: str, accent: str, purpose: str, detailed_description: str
) -> tuple[list[str], list[str]]:
    agent = OrchestratorAgent()
    result = agent.run_manual_mode(situation, accent, purpose, detailed_description)
    return result["replies"], result["titles"]


if __name__ == "__main__":
    # 테스트 코드
    ocr = OcrAgent()
    with open("AI/OCR_Test1.png", "rb") as f:
        file_data = f.read()
        result = ocr.run([("AI/OCR_Test1.png", file_data)])
        print(result)
