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

from utils.deduplicate_sentence import deduplicate_sentences

# from app.core.settings import settings
from pathlib import Path

load_dotenv()  # .env 파일 로드

## CLOVA_REQ_ID_glee_agent 추가(노션에 값 추가했습니다!)


# # 중복 문장 제거
# def deduplicate_sentences(text):
#     text = text.strip()
#     lines = [line.strip() for line in text.splitlines() if line.strip()]
#     dedup_lines = []
#     for line in lines:
#         if not dedup_lines or dedup_lines[-1] != line:
#             dedup_lines.append(line)
#     new_text = "\n".join(dedup_lines)
#     if new_text:
#         half = len(new_text) // 2
#         if len(new_text) % 2 == 0 and new_text[:half] == new_text[half:]:
#             return new_text[:half].strip()
#     return new_text


# ----------------------------
## API 호출 함수들
# 1) CLOVA OCR 호출 함수
def CLOVA_OCR(image_files: list[tuple[str, bytes]]) -> str:

    URL = os.getenv("CLOVA_OCR_URL")
    SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY")

    logger.info(f"URL: {URL}")
    logger.info(f"SECRET_KEY: {SECRET_KEY}")

    if not URL or not SECRET_KEY:
        logger.error("OCR API URL 또는 SECRET_KEY가 설정되지 않았습니다.")
        return ""

    # if not URL or not SECRET_KEY:
    #    URL = settings.CLOVA_OCR_URL
    #    SECRET_KEY = settings.CLOVA_OCR_SECRET_KEY
    #    logger.info(f"settings에서 읽은 URL: {URL}")
    #    logger.info(f"settings에서 읽은 SECRET_KEY: {SECRET_KEY}")

    #    if not URL or not SECRET_KEY:
    #        logger.error("OCR API URL 또는 SECRET_KEY가 설정되지 않았습니다.")
    #        return ""

    headers = {"X-OCR-SECRET": SECRET_KEY}
    total_extracted_text = ""

    logger.info(f"총 {len(image_files)}개의 파일을 처리합니다.")

    for file_name, file_data in image_files:
        file_ext = file_name.split(".")[-1].lower()
        request_json = {
            "images": [{"format": file_ext, "name": "demo"}],
            "requestId": str(uuid.uuid4()),
            "version": "V2",
            "timestamp": int(round(time.time() * 1000)),
        }
        payload = {"message": json.dumps(request_json).encode("UTF-8")}
        files_data = [("file", (file_name, file_data, f"image/{file_ext}"))]
        response = requests.post(URL, headers=headers, data=payload, files=files_data, json=request_json)

        if response.status_code == 200:
            result = response.json()
            if "images" not in result or not result["images"]:
                logger.error(f"OCR 결과에 'images' 키가 없습니다: {result}")
                continue
            if "fields" not in result["images"][0]:
                logger.error(f"OCR 결과에 'fields' 키가 없습니다: {result}")
                continue

            extracted_text = ""
            for field in result["images"][0]["fields"]:
                extracted_text += field["inferText"] + " "
            logger.info(f"[{os.path.basename(file_name)}] 추출된 텍스트: {extracted_text.strip()}")
            total_extracted_text += extracted_text.strip() + "\n"
        else:
            logger.error(f"Error: {response.status_code} - {response.text} for file {file_name}")

    return total_extracted_text.strip()


# 2) 상황 요약 함수
def clova_ai_reply_summary(conversation: str) -> str:
    url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_REPLY_SUMMARY")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "messages": [
            {"role": "system", "content": "사용자가 입력한 내용을 보고 상황을 자세하게 요약해줘."},
            {"role": "user", "content": conversation},
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 500,
        "temperature": 0.3,
        "repeatPenalty": 1.0,
        "stopBefore": [],
        "includeAiFilters": True,
        "seed": 0,
    }
    response = requests.post(url, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")
                    result_text += token
                except Exception:
                    continue
        return deduplicate_sentences(result_text)
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return ""


# 제목 함수
def clova_ai_title_suggestions(input_text: str) -> list[str]:
    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_TITLE")
    suggestions = []
    system_msg = "사용자가 입력한 내용에 맞는 제목을 작성해줘.\n 이때 간결하고 짧게 제목만 출력해줘.\n 제목은 10글자 이내로 요약해서 작성해줘"
    for _ in range(3):
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": input_text}],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 30,
            "temperature": 0.5,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": 0,
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
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
            title_text = re.sub(r"^제목\s*:\s*", "", title_text, flags=re.IGNORECASE)
            suggestions.append(title_text)
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
    return suggestions


# 글 제안 함수
def clova_ai_reply_suggestions(situation_text: str) -> list[str]:
    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_glee_agent")
    suggestions = []

    system_msg = (
        "사용자가 입력한 내용은 지금 사용자가 처한 상황이야.\n"
        "해당 상황에서 사용자가 상대방에게 어떻게 답장하면 좋을지 작성해줘.\n"
        "이때 답장 부분만 출력해줘. 출력값은 따옴표 없이 문장 그 자체만 포함해야 하며, 문장 외의 다른 설명을 절대 추가하지 마.\n"
    )

    for _ in range(3):
        seed = random.randint(0, 10000)
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": situation_text}],
            "topP": 1,
            "topK": 0,
            "maxTokens": 350,
            "temperature": 0.7,
            "repeatPenalty": 3.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": seed,
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            reply_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        reply_text += token
                    except Exception:
                        continue
            reply_text = deduplicate_sentences(reply_text)
            suggestions.append(reply_text)
            reply_text = re.sub(r"^답장\s*:\s*", "", reply_text, flags=re.IGNORECASE).strip()
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
        logger.info(f"생성된 내용:\n{reply_text}")
    return suggestions


# 글 제안 함수(2)
def clova_ai_new_reply_suggestions(
    situation_text: str, accent: str = None, purpose: str = None, detailed_description: str = "없음"
) -> list[str]:

    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_glee_agent")
    suggestions = []

    system_msg = (
        "사용자가 입력한 내용을 바탕으로 어떤 답장을 하면 좋을지 작성해줘.\n"
        "이때 답장 부분만 출력해줘.\n추가 디테일이 있다면 그 부분에 집중해서 답장을 써줘.\n"
        "출력값은 따옴표 없이 문장 그 자체만 포함해야 하며, 문장 외의 다른 설명을 절대 추가하지 마.\n"
    )

    # 상황, 말투, 용도, 상세 설명 정보를 포함한 입력 텍스트 생성
    input_text = f"상황: {situation_text}"
    if accent and purpose:
        input_text += f"\n말투: {accent}\n용도: {purpose}"
    if detailed_description != "없음":
        input_text += f"\n사용자가 추가적으로 제공하는 디테일한 내용: {detailed_description}"
    for _ in range(3):
        seed = random.randint(0, 10000)
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": input_text}],
            "topP": 1,
            "topK": 0,
            "maxTokens": 350,
            "temperature": 0.7,
            "repeatPenalty": 3.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": seed,
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            reply_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        reply_text += token
                    except Exception:
                        continue
            reply_text = deduplicate_sentences(reply_text)
            suggestions.append(reply_text)
            reply_text = re.sub(r"^답장\s*:\s*", "", reply_text, flags=re.IGNORECASE).strip()
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
        logger.info(f"느낌을 파악하고 생성한 결과:\n{reply_text}")
    return suggestions


# 상황 말투 용도 파악 함수
def clova_ai_style_analysis(conversation: str) -> str:

    url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_STYLE")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    system_msg = "사용자가 입력한 내용을 보고 상황, 말투, 용도를 각각 자세하게 출력해줘."

    payload = {
        "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": conversation}],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 256,
        "temperature": 0.3,
        "repeatPenalty": 5.0,
        "stopBefore": [],
        "includeAiFilters": True,
        "seed": 0,
    }
    response = requests.post(url, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")
                    result_text += token
                except Exception:
                    continue
        return deduplicate_sentences(result_text)
    else:
        logger.warning(f"Error: {response.status_code} - {response.text}")
        return "기본 말투, 일반적인 용도"


# 파싱
def parse_style_analysis(result: str):
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
    return cleaned, ""


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
                if len(result_text.strip()) < 5 and retry < self.max_retries:
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
            summary = clova_ai_reply_summary(input_text)
            if len(summary.strip()) < 10 and retry < self.max_retries:
                input_text += "\n좀 더 자세히 요약해줘."
                retry += 1
                continue
            else:
                break
        return summary


class TitleSuggestionAgent:
    def run(self, input_text: str):
        return clova_ai_title_suggestions(input_text)


class ReplySuggestionAgent:
    def __init__(self, variant="old", max_retries=2):
        self.variant = variant
        self.max_retries = max_retries

    def run(self, input_text: str):
        retry = 0
        suggestions = []
        while retry <= self.max_retries:
            if self.variant == "old":
                suggestions = clova_ai_reply_suggestions(input_text)
            else:
                suggestions = clova_ai_new_reply_suggestions(input_text)
            if suggestions and len(suggestions[0].strip()) < 10 and retry < self.max_retries:
                input_text += "\n좀 더 구체적으로, 길이를 늘려서 답장해줘."
                retry += 1
                continue
            else:
                break
        return suggestions


class StyleAnalysisAgent:
    def run(self, input_text: str):
        result = clova_ai_style_analysis(input_text)
        situation, accent, purpose = parse_style_analysis(result)
        return result, situation, accent, purpose


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


#####################################################################
# -------------------------------------------------------------------
# [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
def analyze_situation(image_files: list[tuple[str, bytes]]) -> str:
    if not image_files:
        return ""
    image2text = CLOVA_OCR(image_files)
    situation_string = clova_ai_reply_summary(image2text)
    return situation_string


# -------------------------------------------------------------------
# [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
def analyze_situation_accent_purpose(image_files: list[tuple[str, bytes]]) -> tuple[str, str, str]:
    if not image_files:
        return "", "", ""
    image2text = CLOVA_OCR(image_files)
    situation = clova_ai_reply_summary(image2text)
    style_result = clova_ai_style_analysis(image2text)
    _, tone, usage = parse_style_analysis(style_result)
    return situation, tone, usage


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
