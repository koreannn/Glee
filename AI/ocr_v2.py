import os
import sys

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from pathlib import Path

import requests
import uuid
import time
import json
import random
from dotenv import load_dotenv
import yaml


from loguru import logger

from app.core.settings import settings
from utils.deduplicate_sentence import deduplicate_sentences
from utils.get_headers_payloads import get_headers_payloads
from services.title_suggestion import CLOVA_AI_Title_Suggestions


def load_config(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


load_dotenv("../.env")  # .env 파일 로드


# -------------------------------------------------------------------
# 1) CLOVA OCR 호출 함수
# def CLOVA_OCR(image_files: list[UploadFile]) -> str:
def CLOVA_OCR(image_files: list[tuple[str, bytes]]) -> str:
    """
    여러 이미지 파일 경로 리스트를 받아, 각 파일에 대해 OCR 요청을 개별적으로 보내고,
    그 결과를 합쳐서 반환합니다.
    """
    URL = os.getenv("CLOVA_OCR_URL")
    SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY")

    if not URL or not SECRET_KEY:
        URL = settings.CLOVA_OCR_URL
        SECRET_KEY = settings.CLOVA_OCR_SECRET_KEY

        if not URL or not SECRET_KEY:
            logger.error("OCR API URL 또는 SECRET_KEY가 설정되지 않았습니다.")
            return ""

    headers = {"X-OCR-SECRET": SECRET_KEY}
    total_extracted_text = ""

    # 입력된 파일 수를 로그에 기록
    logger.info(f"총 {len(image_files)}개의 파일을 처리합니다.")

    for file_name, file_data in image_files:
        file_ext = file_name.split(".")[-1].lower()

        # 단일 이미지 객체만 포함하도록 JSON 생성
        request_json = {
            "images": [{"format": file_ext, "name": "demo"}],
            "requestId": str(uuid.uuid4()),
            "version": "V2",
            "timestamp": int(round(time.time() * 1000)),
        }

        payload = {"message": json.dumps(request_json).encode("UTF-8")}

        try:
            # with open(file_path, "rb") as f:
            files_data = [("file", (file_name, file_data, f"image/{file_ext}"))]
            response = requests.post(URL, headers=headers, data=payload, files=files_data, json=request_json)
        except Exception as e:
            logger.error(f"파일 업로드 오류({file_name}): {e}")
            continue

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

            # 각 파일의 OCR 결과를 로그에 출력
            logger.info(f"[{os.path.basename(file_name)}] 추출된 텍스트: {extracted_text.strip()}")
            total_extracted_text += extracted_text.strip() + "\n"
        else:
            logger.error(f"Error: {response.status_code} - {response.text} for file {file_name}")

    return total_extracted_text.strip()


# -------------------------------------------------------------------
# 2) 상황 뱉어내는 함수
def CLOVA_AI_Situation_Summary(conversation: str) -> str:
    # (2) .env에서 불러오기

    URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"

    BASE_DIR = Path(__file__).resolve().parent

    # config 파일의 절대 경로 설정
    config_path = BASE_DIR / "config" / "config_Situation_Summary.yaml"
    headers, payload = get_headers_payloads(str(config_path), "아 배고프다")

    response = requests.post(URL, headers=headers, json=payload, stream=True)
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
        result_text = deduplicate_sentences(result_text)
        logger.info(f"상황 요약: {result_text}")
        return result_text
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return ""


# -------------------------------------------------------------------
# 3) 제목 지어주는 AI
# def CLOVA_AI_Title_Suggestions(input_text: str) -> str:

#     # (2) .env에서 불러오기
#     BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
#     BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
#     REQUEST_ID = os.getenv("CLOVA_REQ_ID_TITLE")

#     if not BEARER_TOKEN or not REQUEST_ID:
#         BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
#         REQUEST_ID = settings.CLOVA_REQ_ID_REPLY_SUMMARY

#     BASE_DIR = Path(__file__).resolve().parent

#     # config 파일의 절대 경로 설정
#     config_path = BASE_DIR / "config" / "config_Title_Suggestion.yaml"
#     headers, payload = get_headers_payloads(str(config_path), input_text)
#     config = load_config(config_path)

#     suggestions = []

#     for _ in range(3):  # 새로 고침 하면 새로운 생성을 만들어내도록 수정
#         headers, payload = get_headers_payloads(str(config_path), input_text)

#         response = requests.post(BASE_URL, headers=headers, json=payload, stream=True)
#         if response.status_code == 200:
#             title_text = ""
#             for line in response.iter_lines(decode_unicode=True):
#                 if line and line.startswith("data:"):
#                     data_str = line[len("data:") :].strip()
#                     try:
#                         data_json = json.loads(data_str)
#                         token = data_json.get("message", {}).get("content", "")
#                         title_text += token
#                     except Exception:
#                         continue
#             suggestions.append(title_text)
#         else:
#             suggestions.append(f"Error: {response.status_code} - {response.text}")
#         logger.info(f"생성된 내용:\n {title_text}")
#     return suggestions


# -------------------------------------------------------------------
# 4) 사진에 대한 답장 AI
def CLOVA_AI_Reply_Suggestions(situation_text: str) -> list[str]:

    BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
    REQUEST_ID = os.getenv("CLOVA_REQ_ID_OLD_REPLY")

    if not BEARER_TOKEN or not REQUEST_ID:
        BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
        REQUEST_ID = settings.CLOVA_REQ_ID_REPLY_SUMMARY

    BASE_DIR = Path(__file__).resolve().parent

    # config 파일의 절대 경로 설정
    config_path = BASE_DIR / "config" / "config_Reply_Suggestions.yaml"
    config = load_config(config_path)

    suggestions = []

    for _ in range(3):
        headers, payload = get_headers_payloads(str(config_path), situation_text, random_seed=True)

        response = requests.post(BASE_URL, headers=headers, json=payload, stream=True)
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
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
        logger.info(f"생성된 내용:\n{reply_text}")
    return suggestions


# -------------------------------------------------------------------
# 5) 이런 느낌으로 써주는 답장 AI (사진 기반으로 상황, 말투, 용도 분석 -> 답변 생성)
def CLOVA_AI_New_Reply_Suggestions(
    situation_text: str, accent: str = None, purpose: str = None, detailed_description: str = "없음"
) -> list[str]:
    # 기존 CLOVA AI 로직 사용
    BASE_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
    REQUEST_ID = os.getenv("CLOVA_REQ_ID_NEW_REPLY")

    if not BEARER_TOKEN or not REQUEST_ID:
        BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
        REQUEST_ID = settings.CLOVA_REQ_ID_REPLY_SUMMARY

    BASE_DIR = Path(__file__).resolve().parent

    # config 파일의 절대 경로 설정
    config_path = BASE_DIR / "config" / "config_New_Reply_Suggestions.yaml"
    config = load_config(config_path)

    # 상황, 말투, 용도 정보를 포함한 입력 텍스트 생성
    input_text = f"상황: {situation_text}"
    if accent and purpose:
        input_text += f"\n말투: {accent}\n용도: {purpose}"
    if detailed_description != "없음":
        input_text += f"\n사용자가 추가적으로 제공하는 디테일한 내용: {detailed_description}"

    suggestions = []

    for _ in range(3):
        seed = random.randint(0, 10000)
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "messages": [
                {"role": "system", "content": config["SYSTEM_PROMPT"]},
                {
                    "role": "user",
                    "content": situation_text + "\n사용자가 추가적으로 제공하는 디테일한 내용:" + detailed_description,
                },
            ],
            "topP": config["HYPER_PARAM"]["topP"],
            "topK": config["HYPER_PARAM"]["topK"],
            "maxTokens": config["HYPER_PARAM"]["maxTokens"],
            "temperature": config["HYPER_PARAM"]["temperature"],
            "repeatPenalty": config["HYPER_PARAM"]["repeatPenalty"],
            "stopBefore": config["HYPER_PARAM"]["stopBefore"],
            "includeAiFilters": config["HYPER_PARAM"]["includeAiFilters"],
            "seed": seed,
        }
        response = requests.post(BASE_URL, headers=headers, json=payload, stream=True)
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
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
        logger.info(f"느낌을 파악하고 생성한 결과:\n{reply_text}")
    return suggestions


# -------------------------------------------------------------------
# 6) 상황 말투 용도 파악 AI
def CLOVA_AI_Style_Analysis(conversation: str) -> tuple[str, str]:
    URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
    REQUEST_ID = os.getenv("CLOVA_REQ_ID_STYLE")

    if not BEARER_TOKEN or not REQUEST_ID:
        BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
        REQUEST_ID = settings.CLOVA_REQ_ID_REPLY_SUMMARY

    BASE_DIR = Path(__file__).resolve().parent

    # config 파일의 절대 경로 설정
    config_path = BASE_DIR / "config" / "config_Style_Analysis.yaml"
    config = load_config(config_path)

    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    payload = {
        "messages": [{"role": "system", "content": config["SYSTEM_PROMPT"]}, {"role": "user", "content": conversation}],
        "topP": config["HYPER_PARAM"]["topP"],
        "topK": config["HYPER_PARAM"]["topK"],
        "maxTokens": config["HYPER_PARAM"]["maxTokens"],
        "temperature": config["HYPER_PARAM"]["temperature"],
        "repeatPenalty": config["HYPER_PARAM"]["repeatPenalty"],
        "stopBefore": config["HYPER_PARAM"]["stopBefore"],
        "includeAiFilters": config["HYPER_PARAM"]["includeAiFilters"],
        "seed": config["HYPER_PARAM"]["seed"],
    }
    response = requests.post(URL, headers=headers, json=payload, stream=True)
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

        tone = None
        use_case = None
        # result_text = deduplicate_sentences(result_text)
        # logger.info(f"분석 결과\n{result_text}")
        # return result_text
        try:
            if "말투" in result_text and "용도" in result_text:
                tone_start = result_text.find("말투:") + len("말투:")  # 말투 시작점("말투:" 부분 이후)
                tone_end = result_text.find("\n", tone_start)
                tone = result_text[tone_start:tone_end].strip()

                use_case_start = result_text.find("용도:") + len("용도:")
                use_case_end = result_text.find("\n", use_case_start)
                use_case = result_text[use_case_start:use_case_end].strip()

                logger.info(f"말투: {tone}\n용도: {use_case}")

                return tone, use_case
        except Exception as e:
            logger.error(f"오류 발생: {e}")
            return "기본 말투", "일반적인 용도"
    else:
        logger.warning(f"Error: {response.status_code} - {response.text}")
        return "기본 말투", "일반적인 용도"


# -------------------------------------------------------------------
# [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
def analyze_situation(image_files: list[tuple[str, bytes]]) -> str:
    image2text = CLOVA_OCR(image_files)
    situation_string = CLOVA_AI_Situation_Summary(image2text)
    return situation_string


# -------------------------------------------------------------------
# [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
def analyze_situation_accent_purpose(image_files: list[tuple[str, bytes]]) -> tuple[str, str, str]:
    image2text = CLOVA_OCR(image_files)
    situation = CLOVA_AI_Situation_Summary(image2text)
    accent, purpose = CLOVA_AI_Style_Analysis(image2text)
    return situation, accent, purpose


# -------------------------------------------------------------------
# [3] [1]의 상황을 기반으로 글 제안을 생성하는 함수
def generate_suggestions_situation(situation: str) -> list[str]:
    suggestions = CLOVA_AI_Reply_Suggestions(situation)
    title = CLOVA_AI_Title_Suggestions(situation)
    return suggestions, title


# -------------------------------------------------------------------
# [4] [2]의 상황, 말투, 용도를 기반으로 글 제안을 생성하는 함수
def generate_reply_suggestions_accent_purpose(situation: str, accent: str, purpose: str) -> list[str]:
    suggestions = CLOVA_AI_New_Reply_Suggestions(situation, accent, purpose)
    title = CLOVA_AI_Title_Suggestions(situation)
    return suggestions, title


# -------------------------------------------------------------------
# [5] 상황, 말투, 용도, 상세 설명을 기반으로 글 제안을 생성하는 함수
def New_Reply_Suggestions_Detailed(
    situation: str, accent: str, purpose: str, detailed_description: str
) -> list[str, str, str]:
    suggestions = CLOVA_AI_New_Reply_Suggestions(situation, accent, purpose, detailed_description)
    title = CLOVA_AI_Title_Suggestions(situation)
    return suggestions, title
