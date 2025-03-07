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


# ----------------------------
# 이미지 전처리를 위한 클래스
class ImagePreprocessor:
    def preprocess(self, image_bytes: bytes) -> bytes:
        """이미지 전처리를 수행합니다."""
        try:
            # 이미지 로드 및 전처리
            image = Image.open(BytesIO(image_bytes))

            # 이미지 정규화 (크기 조정, 회전 등)
            image = ImageOps.exif_transpose(image)  # EXIF 정보에 따라 이미지 회전

            # 결과 이미지를 바이트로 변환
            output_buffer = BytesIO()
            image.save(output_buffer, format=image.format or "PNG")
            return output_buffer.getvalue()
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_bytes


# ----------------------------
# OCR 결과 캐싱 (같은 이미지에 대해 중복 호출 방지)
class OcrCache:
    def __init__(self):
        self.cache = {}

    def get_hash(self, filedata: bytes) -> str:
        return hashlib.md5(filedata).hexdigest()

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value: str):
        self.cache[key] = value


ocr_cache = OcrCache()


# ----------------------------
# OcrPostProcessingAgent
class OcrPostProcessingAgent:
    def run(self, ocr_text: str) -> str:
        cleaned_text = ocr_text
        cleaned_text = re.sub(r"[^가-힣a-zA-Z0-9\s.,?!]", "", cleaned_text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        logger.info(f"Text after cleaning:\n{cleaned_text}")

        return cleaned_text


# OcrAgent
class OcrAgent:
    """OCR 처리를 담당하는 에이전트"""

    def __init__(self, max_retries=2):
        self.max_retries = max_retries
        self.post_processor = OcrPostProcessingAgent()
        self.preprocessor = ImagePreprocessor()

    def run(self, image_files: List[Tuple[str, bytes]]) -> str:
        """이미지 파일에서 텍스트를 추출합니다."""
        aggregated_text = []
        temp_files = []  # 임시 파일 경로 저장 리스트

        try:
            for filename, filedata in image_files:
                # 이미지 전처리 적용
                processed_bytes = self.preprocessor.preprocess(filedata)

                # 캐시 확인
                file_hash = ocr_cache.get_hash(processed_bytes)
                cached_result = ocr_cache.get(file_hash)
                if cached_result:
                    logger.info(f"Using cached OCR result for {filename}")
                    aggregated_text.append(cached_result)
                    continue

                # 임시 파일 생성
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                    temp_file.write(processed_bytes)
                    temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)  # 임시 파일 경로 저장

                # OCR 처리
                retry = 0
                while retry <= self.max_retries:
                    # 파일 경로 리스트만 전달
                    ocr_result = ocr_service.CLOVA_OCR([temp_file_path])
                    if isinstance(ocr_result, str) and ocr_result.startswith("Error"):
                        logger.error(ocr_result)
                        aggregated_text.append("")
                        break
                    extracted_text = extract_text_from_ocr_result(ocr_result)
                    if len(extracted_text.strip()) < 5 and retry < self.max_retries:
                        retry += 1
                        continue
                    else:
                        aggregated_text.append(extracted_text)
                        ocr_cache.set(file_hash, extracted_text)
                        break

            raw_text = "\n".join(aggregated_text)
            processed_text = self.post_processor.run(raw_text)
            return processed_text

        finally:
            # 모든 임시 파일 삭제
            for temp_file_path in temp_files:
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.error(f"임시 파일 삭제 중 오류 발생: {e}")


class SummarizerAgent:
    def __init__(self, max_retries=2):
        self.max_retries = max_retries

    def run(self, input_text: str):
        retry = 0
        summary = ""
        while retry <= self.max_retries:
            summary = situation_service.situation_summary(input_text)
            if len(summary.strip()) < 10 and retry < self.max_retries:
                input_text += "\n좀 더 자세히 요약해줘."
                retry += 1
                continue
            else:
                break
        return summary


class TitleSuggestionAgent:
    def run(self, input_text: str):
        return title_service._generate_title_suggestions(input_text)


class ReplySuggestionAgent:
    def __init__(self, variant="old", max_retries=2):
        self.variant = variant
        self.max_retries = max_retries

    def run(self, input_text: str):
        retry = 0
        suggestions = []
        while retry <= self.max_retries:
            if self.variant == "old":
                suggestions = reply_service.generate_basic_reply(input_text)
            else:
                suggestions = reply_service.generate_detailed_reply(input_text)
            if suggestions and len(suggestions[0].strip()) < 10 and retry < self.max_retries:
                input_text += "\n좀 더 구체적으로, 길이를 늘려서 답변해줘."
                retry += 1
                continue
            else:
                break
        return suggestions


class StyleAnalysisAgent:
    def run(self, input_text: str):
        style_result = situation_service.style_analysis(input_text)
        situation, accent, purpose = parse_style_analysis(style_result)
        return style_result, situation, accent, purpose


class FeedbackAgent:
    def __init__(self, min_length=10, max_retries=2):
        self.min_length = min_length
        self.max_retries = max_retries

    def check_and_improve(self, output: str, original_input: str, agent):
        retries = 0
        improved_output = output

        # 리스트나 튜플인 경우 처리
        if isinstance(improved_output, (list, tuple)):
            if improved_output:
                if isinstance(improved_output, tuple):
                    # 튜플의 첫 번째 항목이 문자열인 경우 사용
                    improved_output = (
                        improved_output[0] if isinstance(improved_output[0], str) else str(improved_output[0])
                    )
                else:  # 리스트인 경우
                    improved_output = improved_output[0]
            else:
                improved_output = ""

        # 문자열이 아닌 경우 문자열로 변환
        if not isinstance(improved_output, str):
            improved_output = str(improved_output)

        while len(improved_output.strip()) < self.min_length and retries < self.max_retries:
            improved_input = original_input + "\n추가 상세 설명 부탁해."
            new_output = agent.run(improved_input)

            # 리스트나 튜플인 경우 처리
            if isinstance(new_output, (list, tuple)):
                if new_output:
                    if isinstance(new_output, tuple):
                        # 튜플의 첫 번째 항목이 문자열인 경우 사용
                        new_output = new_output[0] if isinstance(new_output[0], str) else str(new_output[0])
                    else:  # 리스트인 경우
                        new_output = new_output[0]
                else:
                    break

            # 문자열이 아닌 경우 문자열로 변환
            if not isinstance(new_output, str):
                new_output = str(new_output)

            improved_output = new_output
            retries += 1

        return improved_output


class OrchestratorAgent:
    def __init__(self):
        self.ocr_agent = OcrAgent()
        self.summarizer_agent = SummarizerAgent()
        self.title_agent = TitleSuggestionAgent()
        self.reply_agent_old = ReplySuggestionAgent(variant="old")
        self.reply_agent_new = ReplySuggestionAgent(variant="new")
        self.style_agent = StyleAnalysisAgent()
        self.feedback_agent = FeedbackAgent()

    def run_reply_mode(self, input_text: str) -> Dict[str, Union[str, List[str]]]:
        # 상황 요약 생성
        summary = self.summarizer_agent.run(input_text)
        summary = self.feedback_agent.check_and_improve(summary, input_text, self.summarizer_agent)

        # 제목 생성
        titles = self.title_agent.run(summary)

        # 답장 제안 생성 (기본)
        replies = self.reply_agent_old.run(summary)
        replies = [self.feedback_agent.check_and_improve(reply, summary, self.reply_agent_old) for reply in replies]

        return {
            "situation": summary,
            "accent": "기본 말투",
            "purpose": "일반 답변",
            "titles": titles,
            "replies": replies,
        }

    def run_style_mode(self, input_text: str) -> Dict[str, Union[str, List[str]]]:
        # 스타일 분석 (상황, 말투, 용도 추출)
        style_result, situation, tone, usage = self.style_agent.run(input_text)
        style_result = self.feedback_agent.check_and_improve(style_result, input_text, self.style_agent)

        # 제목 제안 생성
        titles = self.title_agent.run(situation)

        # 답변 제안 생성 (말투, 용도 정보 활용)
        detailed_input = f"상황: {situation}\n말투: {tone}\n용도: {usage}"
        replies = self.reply_agent_new.run(detailed_input)
        replies = [
            self.feedback_agent.check_and_improve(reply, detailed_input, self.reply_agent_new) for reply in replies
        ]

        return {
            "situation": situation,
            "accent": tone,
            "purpose": usage,
            "titles": titles,
            "replies": replies,
            "style_analysis": style_result,
        }

    def run_manual_mode(
        self, situation: str, accent: str, purpose: str, details: str
    ) -> Dict[str, Union[str, List[str]]]:
        # 입력 정보에 기반하여 전체 프롬프트 생성 (수동 입력으로 받을 경우)
        detailed_input = f"상황: {situation}\n말투: {accent}\n용도: {purpose}\n추가 설명: {details}"

        # 제목 제안 생성
        titles = self.title_agent.run(situation)

        # 답변 제안 생성 (말투, 용도, 추가 설명 정보 활용)
        replies = self.reply_agent_new.run(detailed_input)
        replies = [
            self.feedback_agent.check_and_improve(reply, detailed_input, self.reply_agent_new) for reply in replies
        ]

        return {
            "situation": situation,
            "accent": accent,
            "purpose": purpose,
            "details": details,
            "titles": titles,
            "replies": replies,
        }


#####################################################################
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


# if __name__ == "__main__":
#    test_text = "test test test "
#    summarizer = SummarizerAgent()
#    summary = summarizer.run(test_text)
#    print("SummarizerAgent 요약 결과:")
#    print(summary)

# if __name__ == "__main__":
#    test_text = "test test test"
#    title_agent = TitleSuggestionAgent()
#    titles = title_agent.run(test_text)
#    print("TitleSuggestionAgent 제목 제안 결과:")
#    for t in titles:
#        print("-", t)

# if __name__ == "__main__":
#    test_text = "test test test"
#    reply_agent = ReplySuggestionAgent(variant="old")
#    replies = reply_agent.run(test_text)
#    print("ReplySuggestionAgent 답변 제안 결과:")
#    for r in replies:
#        print("-", r)

# if __name__ == "__main__":
#    test_text = "test test test"
#    style_agent = StyleAnalysisAgent()
#    style_result, situation, tone, usage = style_agent.run(test_text)
#    print("StyleAnalysisAgent 분석 결과:")
#    print("전체 분석 결과:", style_result)
#    print("상황:", situation)
#    print("말투:", tone)
#    print("용도:", usage)

# if __name__ == "__main__":
#    situation = "친구가 돈 빌려가고 안 갚는 상황"
#    accent = "짜증내는 어투"
#    purpose = "카카오톡"
#    detailed_description = "이번 주 안에 갚았으면 함. 상대방이 문자를 보고 위협을 느꼈으면 함"

#    orchestrator = OrchestratorAgent()
#    result = orchestrator.run_manual_mode(situation, accent, purpose, detailed_description)
#    print("OrchestratorAgent 통합 결과 (Reply Mode):")
#    print("상황 요약:", result["situation"])
#    print("제목 제안:", result["titles"])
#    print("답변 제안:")
#    for reply in result["replies"]:
#        print("-", reply)


# <test1>
# situation = "상사에게 보고하는 상황"
# accent = "예의바르고 정중하게"
# purpose = "이메일"
# detailed_description = "다음 주 개인 사정으로 인해 휴가 신청"
# 상황 요약: 상사에게 보고하는 상황
# 제목 제안: ['휴가 신청서 제출 드립니다.', '휴가 신청서 제출 드립니다.', '휴가 신청서 제출드립니다.']
# 답변 제안:
# - 다음 주 제 개인적인 사정으로 인해 휴가를 신청하고자 합니다. 미리 일정 확인하시고 조정이 필요하시다면 말씀 부탁드립니다. 결재 서류는 오늘 중으로 제출 하겠습니다.
# - 제목 : 휴가 신청서 제출
# 안녕하십니까, [상사 성함]님.
# 다음 주 제 개인적인 사유로 인해 휴가를 신청하고자 합니다. 휴가는 일주일 정도가 될 것 같습니다. 이 기간 동안 업무에 공백이 생기지 않도록 사전에 일 처리를 완료하겠습니다.
# 휴가 신청서와 관련하여 필요하신 정보나 조치가 있다면 언제든지 알려주시기 바랍니다. 미리 감사드립니다.
# 감사합니다.
# [본인 이름]
# - 다음주 개인 사정으로 인해 휴가를 내고자 합니다. 미리 일정 조율을 위해 연락드립니다. 제가 없는 동안 업무에 차질이 생기지 않도록 필요한 서류나 절차가 있다면 알려주시기 바랍니다. 감사합니다.

# <test2>
# 상황 요약: 친구가 돈 빌려가고 안 갚는 상황
# 제목 제안: ['[갚아줄래?]', '"돈 갚아"', '[제목] 돈 갚아']
# 답변 제안:
# - 진짜 이번주까지 안갚으면 너랑 연 끊을거야
# - 너 진짜 너무한다. 빌린 돈 얼른 갚아라. 이번 주 안에 해결 못하면 나도 가만히 안 있을 거다.
# - "너 자꾸 이렇게 내 돈 안갚으면 나도 가만히 있지 않을거야. 이번주내로 꼭 보내."

# if __name__ == "__main__":
#    test_image_path = r"C:\Users\james\J_Ai_Lab\glee_agent\test222.png"
#    with open(test_image_path, "rb") as f:
#        image_bytes = f.read()
#    # 파일 이름과 bytes를 튜플로 전달
#    image_files = [(os.path.basename(test_image_path), image_bytes)]

# OCR 및 상황 분석 테스트
#    situation_summary = analyze_situation(image_files)
#    print("=== 이미지 기반 상황 요약 ===")
#    print(situation_summary)

# 스타일 분석 테스트 (상황, 말투, 용도)
#    situation, tone, usage = analyze_situation_accent_purpose(image_files)
#    print("\n=== 이미지 기반 스타일 분석 ===")
#    print("상황:", situation)
#    print("말투:", tone)
#    print("용도:", usage)

# 추가 디테일
#  detailed_description = "스스로 정보를 찾아서 알아서 잘했으면 좋겠음"

# 상황, 말투, 용도, 디테일 기반 글 제안
#  replies_detail, titles_detail = generate_reply_suggestions_detail(situation, tone, usage, detailed_description)
#  print("\n=== 상황, 말투, 용도, 디테일 기반 글 제안 ===")
#  for i, (title, reply) in enumerate(zip(titles_detail, replies_detail), 1):
#      print(f"[제안 {i}] 제목: {title}")
#      print(f"[제안 {i}] 내용: {reply}")
#      print("-" * 40)

# [제안 3] 제목: jupyter 오류 해결 방법
# [제안 3] 내용: "오류 메시지를 알려주시면 더 정확하게 안내해 드릴 수 있을 것 같아요! 그리고 인터넷 검색이나 공식 문서를 참고하시면 문제를 해결하실 수 있을 거예요."


if __name__ == "__main__":
    # 테스트 코드
    ocr = OcrAgent()
    with open("AI/OCR_Test1.png", "rb") as f:
        file_data = f.read()
        result = ocr.run([("AI/OCR_Test1.png", file_data)])
        print(result)
