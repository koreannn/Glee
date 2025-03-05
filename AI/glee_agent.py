import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import random
import uuid
import time
import json
from dotenv import load_dotenv
import re
import requests
from loguru import logger

# from app.core.settings import settings
from pathlib import Path

load_dotenv()  # .env 파일 로드

from AI.utils.deduplicate_sentence import deduplicate_sentences
from AI.services.Generation.reply_seggestion import ReplySuggestion
from AI.services.OCR.get_ocr_text import CLOVA_OCR
from AI.services.Analysis.analyze_situation import Analyze
from AI.services.Generation.title_suggestion import TitleSuggestion
from AI.services.videosearch_service import VideoSearchService

## CLOVA_REQ_ID_glee_agent 추가(노션에 값 추가했습니다!)

ocr_service = CLOVA_OCR()
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
video_search_service = VideoSearchService()


# 1. 상황, 말투, 용도 파싱하는 부분
# 2. 제목, 답변 파싱하는 부분 이렇게 두 가지 확읺해야함

def parse_style_analysis(result: str): # -> analyze_situation._parse_style_analysis()
    situation, accent, purpose = "", "", ""
    lines = result.splitlines()
    for line in lines:
        if line.strip().startswith("상황"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                situation = parts[1].strip()
        elif line.strip().startswith("말투"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                accent = parts[1].strip()
        elif line.strip().startswith("용도"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                purpose = parts[1].strip()
    return situation, accent, purpose


def parse_suggestion(suggestion: str):
    cleaned = suggestion.strip()
    cleaned = re.sub(r"^(제목|답변)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace('"', "")
    n = len(cleaned)
    half = n // 2
    if n % 2 == 0 and cleaned[:half] == cleaned[half:]:
        cleaned = cleaned[:half].strip()
    return cleaned, "" # 빈 문자열은 왜 반환?


# ----------------------------
# Glee 에이전트 클래스
class OcrAgent:
    def __init__(self, max_retries=2):
        self.max_retries = max_retries

    def run(self, image_paths: list[tuple[str, bytes]]):
        aggregated_text = []
        for img in image_paths:
            retry = 0
            while retry <= self.max_retries:
                # 각 이미지(튜플)를 리스트에 담아 호출
                result_text = CLOVA_OCR([img])
                if len(result_text.strip()) < 5 and retry < self.max_retries: # 제대로 텍스트가 추출되지 않은 경우에 대한 재시도 처리?
                    retry += 1
                    continue
                else:
                    aggregated_text.append(result_text)
                    break
        return "\n".join(aggregated_text)


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
                input_text += "\n좀 더 구체적으로, 길이를 늘려서 답장해줘."
                retry += 1
                continue
            else:
                break
        return suggestions


class StyleAnalysisAgent:
    def run(self, input_text: str):
        result = situation_service.style_analysis(input_text)
        situation, accent, purpose = parse_style_analysis(result)
        return result, situation, accent, purpose # result 반환하고 나서 어디에 쓰임?


class FeedbackAgent:
    def __init__(self, min_length=10, max_retries=2):
        self.min_length = min_length
        self.max_retries = max_retries

    def check_and_improve(self, output: str, original_input: str, agent):
        retries = 0
        improved_output = output
        while len(improved_output.strip()) < self.min_length and retries < self.max_retries:
            improved_input = original_input + "\n추가 상세 설명 부탁해."
            improved_output = agent.run(improved_input)
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

    def run_reply_mode(self, input_text: str):
        summary = self.summarizer_agent.run(input_text)
        summary = self.feedback_agent.check_and_improve(summary, input_text, self.summarizer_agent)
        titles = self.title_agent.run(summary)
        replies = self.reply_agent_old.run(summary)
        replies = [self.feedback_agent.check_and_improve(reply, summary, self.reply_agent_old) for reply in replies]
        return {
            "situation": summary,
            "accent": "기본 말투",
            "purpose": "일반 답변",
            "titles": titles,
            "replies": replies,
        }

    def run_style_mode(self, input_text: str):
        style_result, situation, tone, usage = self.style_agent.run(input_text)
        style_result = self.feedback_agent.check_and_improve(style_result, input_text, self.style_agent)
        titles = self.title_agent.run(style_result)
        replies = self.reply_agent_new.run(style_result)
        replies = [
            self.feedback_agent.check_and_improve(reply, style_result, self.reply_agent_new) for reply in replies
        ]
        return {
            "situation": situation,
            "accent": tone,
            "purpose": usage,
            "titles": titles,
            "replies": replies,
            "style_analysis": style_result,
        }

    def run_manual_mode(self, situation: str, accent: str, purpose: str, details: str):
        prompt = (
            f"상황: {situation}\n"
            f"말투: {accent}\n"
            f"글 사용처: {purpose}\n"
            f"추가 디테일: {details}\n"
            "위 내용을 바탕으로 자연스러운 글 제안을 해줘."
        )
        titles = self.title_agent.run(prompt)
        replies = self.reply_agent_new.run(prompt)
        replies = [self.feedback_agent.check_and_improve(reply, prompt, self.reply_agent_new) for reply in replies]
        return {
            "situation": situation,
            "accent": accent,
            "purpose": purpose,
            "titles": titles,
            "replies": replies,
            "prompt": prompt,
        }


