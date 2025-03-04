import os
import random
import uuid
import time
import json
from dotenv import load_dotenv
import re
import requests
from loguru import logger
import tempfile
#from app.core.settings import settings
from pathlib import Path
from PIL import Image, ImageOps
import hashlib
from io import BytesIO


load_dotenv()  # .env 파일 로드

## CLOVA_REQ_ID_glee_agent 추가(노션에 값 추가했습니다!)

# 중복 문장 제거
def deduplicate_sentences(text):
    text = text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    dedup_lines = []
    for line in lines:
        if not dedup_lines or dedup_lines[-1] != line:
            dedup_lines.append(line)
    new_text = "\n".join(dedup_lines)
    if new_text:
        half = len(new_text) // 2
        if len(new_text) % 2 == 0 and new_text[:half] == new_text[half:]:
            return new_text[:half].strip()
    return new_text

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
    
    #if not URL or not SECRET_KEY:
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
        "Accept": "text/event-stream"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "사용자가 입력한 내용을 보고 상황을 자세하게 요약해줘."},
            {"role": "user", "content": conversation}
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 500,
        "temperature": 0.3,
        "repeatPenalty": 1.0,
        "stopBefore": [],
        "includeAiFilters": True,
        "seed": 0
    }
    response = requests.post(url, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:"):].strip()
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
    system_msg = ("사용자가 입력한 내용에 맞는 제목을 작성해줘.\n 이때 간결하고 짧게 제목만 출력해줘.\n 제목은 10글자 이내로 요약해서 작성해줘")
    for _ in range(3):
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": input_text}
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 30,
            "temperature": 0.5,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": 0
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            title_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
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
            "Accept": "text/event-stream"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": situation_text}
            ],
            "topP": 1,
            "topK": 0,
            "maxTokens": 350,
            "temperature": 0.7,
            "repeatPenalty": 3.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": seed
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            reply_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
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
            "Accept": "text/event-stream"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": input_text}
            ],
            "topP": 1,
            "topK": 0,
            "maxTokens": 350,
            "temperature": 0.7,
            "repeatPenalty": 3.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": seed
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            reply_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
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
        "Accept": "text/event-stream"

    }
    system_msg = "사용자가 입력한 내용을 보고 상황, 말투, 용도를 각각 자세하게 출력해줘."

    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": conversation}
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 256,
        "temperature": 0.3,
        "repeatPenalty": 5.0,
        "stopBefore": [],
        "includeAiFilters": True,
        "seed": 0
    }
    response = requests.post(url, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:"):].strip()
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

#########################################
# Glee 에이전트 클래스
#########################################

# 헬퍼 함수: OCR 결과 JSON에서 텍스트 추출
def extract_text_from_ocr_result(ocr_result):
    text_list = []
    if isinstance(ocr_result, dict) and "images" in ocr_result:
        for image in ocr_result["images"]:
            if "fields" in image:
                for field in image["fields"]:
                    text_list.append(field.get("inferText", ""))
    return " ".join(text_list)

# ----------------------------
# 이미지 전처리를 위한 클래스 
class ImagePreprocessor:
    def preprocess(self, image_bytes: bytes) -> bytes:
        try:
            with BytesIO(image_bytes) as stream:
                image = Image.open(stream)
                # 그레이스케일 변환 및 대비 보정
                image = ImageOps.grayscale(image)
                image = ImageOps.autocontrast(image)
                output_stream = BytesIO()
                image.save(output_stream, format="JPEG")
                return output_stream.getvalue()
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
    def __init__(self):
        
        self.clova_ai_url = os.getenv("https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003")
        self.bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
        self.request_id = os.getenv("CLOVA_REQ_ID_glee_agent")

    def run(self, ocr_text: str) -> str:
        
        #cleaned_text = deduplicate_sentences(ocr_text) or ""
        #logger.info(f"Text before cleaning:\n{cleaned_text}")
        
        # 간단한 정규표현식을 사용하여 특수문자 제거 및 공백 정리
        cleaned_text = re.sub(r'[^가-힣a-zA-Z0-9\s.,?!]', '', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        logger.info(f"Text after cleaning:\n{cleaned_text}")
        
        return cleaned_text

# OcrAgent 
class OcrAgent:
    def __init__(self, max_retries=2):
        self.max_retries = max_retries
        self.post_processor = OcrPostProcessingAgent()
        self.preprocessor = ImagePreprocessor()

    def run(self, image_files: list[tuple[str, bytes]]) -> str:
        aggregated_text = []
        for (filename, filedata) in image_files:
            # 이미지 전처리 적용
            processed_bytes = self.preprocessor.preprocess(filedata)
            # 캐시 확인: 동일 이미지에 대한 OCR 결과 재사용
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
            try:
                retry = 0
                while retry <= self.max_retries:
                    ocr_result = CLOVA_OCR([(filename, processed_bytes)])
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
            finally:
                os.remove(temp_file_path)
        raw_text = "\n".join(aggregated_text)
        processed_text = self.post_processor.run(raw_text)
        return processed_text


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
                input_text += "\n좀 더 구체적으로, 길이를 늘려서 답변해줘."
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

    def run_reply_mode(self, input_text: str) -> dict:
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
            "replies": replies
        }

    def run_style_mode(self, input_text: str) -> dict:
        # 스타일 분석 (상황, 말투, 용도 추출)
        style_result, situation, tone, usage = self.style_agent.run(input_text)
        style_result = self.feedback_agent.check_and_improve(style_result, input_text, self.style_agent)
        
        # 제목 생성
        titles = self.title_agent.run(style_result)
        
        # 답장 제안 생성 (상세)
        replies = self.reply_agent_new.run(style_result)
        replies = [self.feedback_agent.check_and_improve(reply, style_result, self.reply_agent_new) for reply in replies]
        
        return {
            "situation": situation,
            "accent": tone,
            "purpose": usage,
            "titles": titles,
            "replies": replies,
            "style_analysis": style_result
        }

    def run_manual_mode(self, situation: str, accent: str, purpose: str, details: str) -> dict:
        # 입력 정보에 기반하여 전체 프롬프트 생성
        prompt = (
            f"상황: {situation}\n"
            f"말투: {accent}\n"
            f"글 사용처: {purpose}\n"
            f"추가 디테일: {details}\n"
            "위 내용을 바탕으로 자연스러운 답장을 작성해줘."
        )
        # 제목 생성
        titles = self.title_agent.run(prompt)
        # 답장 제안 생성
        replies = self.reply_agent_new.run(prompt)
        replies = [self.feedback_agent.check_and_improve(reply, prompt, self.reply_agent_new) for reply in replies]
        
        return {
            "situation": situation,
            "accent": accent,
            "purpose": purpose,
            "titles": titles,
            "replies": replies,
            "prompt": prompt
        }

#####################################################################
# -------------------------------------------------------------------
# [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
def analyze_situation(image_files: list[tuple[str, bytes]]) -> str:
    if not image_files:
        return ""
    aggregated_text = []
    for (filename, filedata) in image_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(filedata)
            temp_file_path = temp_file.name
        try:
            with open(temp_file_path, "rb") as f:
                temp_file_data = f.read()
            ocr_result = CLOVA_OCR([(os.path.basename(temp_file_path), temp_file_data)])
            extracted_text = ocr_result
            aggregated_text.append(extracted_text)
        finally:
            os.remove(temp_file_path)
    image2text = "\n".join(aggregated_text)
    situation_string = clova_ai_reply_summary(image2text)
    return situation_string

# [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
def analyze_situation_accent_purpose(image_files: list[tuple[str, bytes]]) -> tuple[str, str, str]:
    if not image_files:
        return "", "", ""
    aggregated_text = []
    for (filename, filedata) in image_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(filedata)
            temp_file_path = temp_file.name
        try:
            with open(temp_file_path, "rb") as f:
                temp_file_data = f.read()
            ocr_result = CLOVA_OCR([(os.path.basename(temp_file_path), temp_file_data)])
            extracted_text = ocr_result  
            aggregated_text.append(extracted_text)
        finally:
            os.remove(temp_file_path)
    image2text = "\n".join(aggregated_text)
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
def generate_reply_suggestions_detail(situation: str, accent: str, purpose: str, detailed_description: str) -> tuple[list[str], list[str]]:
    agent = OrchestratorAgent()
    result = agent.run_manual_mode(situation, accent, purpose, detailed_description)
    return result["replies"], result["titles"]

#if __name__ == "__main__":
#    test_text = "test test test " 
#    summarizer = SummarizerAgent()
#    summary = summarizer.run(test_text)
#    print("SummarizerAgent 요약 결과:")
#    print(summary)

#if __name__ == "__main__":
#    test_text = "test test test"
#    title_agent = TitleSuggestionAgent()
#    titles = title_agent.run(test_text)
#    print("TitleSuggestionAgent 제목 제안 결과:")
#    for t in titles:
#        print("-", t)

#if __name__ == "__main__":
#    test_text = "test test test"
#    reply_agent = ReplySuggestionAgent(variant="old")
#    replies = reply_agent.run(test_text)
#    print("ReplySuggestionAgent 답변 제안 결과:")
#    for r in replies:
#        print("-", r)

#if __name__ == "__main__":
#    test_text = "test test test"
#    style_agent = StyleAnalysisAgent()
#    style_result, situation, tone, usage = style_agent.run(test_text)
#    print("StyleAnalysisAgent 분석 결과:")
#    print("전체 분석 결과:", style_result)
#    print("상황:", situation)
#    print("말투:", tone)
#    print("용도:", usage)

#if __name__ == "__main__":
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


#<test1>
# situation = "상사에게 보고하는 상황"
# accent = "예의바르고 정중하게"
# purpose = "이메일"
# detailed_description = "다음 주 개인 사정으로 인해 휴가 신청"
#상황 요약: 상사에게 보고하는 상황
#제목 제안: ['휴가 신청서 제출 드립니다.', '휴가 신청서 제출 드립니다.', '휴가 신청서 제출드립니다.']
#답변 제안:
#- 다음 주 제 개인적인 사정으로 인해 휴가를 신청하고자 합니다. 미리 일정 확인하시고 조정이 필요하시다면 말씀 부탁드립니다. 결재 서류는 오늘 중으로 제출 하겠습니다.
#- 제목 : 휴가 신청서 제출
#안녕하십니까, [상사 성함]님.
#다음 주 제 개인적인 사유로 인해 휴가를 신청하고자 합니다. 휴가는 일주일 정도가 될 것 같습니다. 이 기간 동안 업무에 공백이 생기지 않도록 사전에 일 처리를 완료하겠습니다.
#휴가 신청서와 관련하여 필요하신 정보나 조치가 있다면 언제든지 알려주시기 바랍니다. 미리 감사드립니다.
#감사합니다.
#[본인 이름]
#- 다음주 개인 사정으로 인해 휴가를 내고자 합니다. 미리 일정 조율을 위해 연락드립니다. 제가 없는 동안 업무에 차질이 생기지 않도록 필요한 서류나 절차가 있다면 알려주시기 바랍니다. 감사합니다.

#<test2>
# 상황 요약: 친구가 돈 빌려가고 안 갚는 상황
#제목 제안: ['[갚아줄래?]', '"돈 갚아"', '[제목] 돈 갚아']
#답변 제안:
#- 진짜 이번주까지 안갚으면 너랑 연 끊을거야
#- 너 진짜 너무한다. 빌린 돈 얼른 갚아라. 이번 주 안에 해결 못하면 나도 가만히 안 있을 거다.
#- "너 자꾸 이렇게 내 돈 안갚으면 나도 가만히 있지 않을거야. 이번주내로 꼭 보내."

if __name__ == "__main__":
    test_image_path = r"C:\Users\james\J_Ai_Lab\glee_agent\test222.png"
    with open(test_image_path, "rb") as f:
        image_bytes = f.read()
    # 파일 이름과 bytes를 튜플로 전달
    image_files = [(os.path.basename(test_image_path), image_bytes)]
    
    # OCR 및 상황 분석 테스트
    situation_summary = analyze_situation(image_files)
    print("=== 이미지 기반 상황 요약 ===")
    print(situation_summary)
    
    # 스타일 분석 테스트 (상황, 말투, 용도)
    situation, tone, usage = analyze_situation_accent_purpose(image_files)
    print("\n=== 이미지 기반 스타일 분석 ===")
    print("상황:", situation)
    print("말투:", tone)
    print("용도:", usage)
    
    # 추가 디테일
    detailed_description = "스스로 정보를 찾아서 알아서 잘했으면 좋겠음"
    
    # 상황, 말투, 용도, 디테일 기반 글 제안
    replies_detail, titles_detail = generate_reply_suggestions_detail(situation, tone, usage, detailed_description)
    print("\n=== 상황, 말투, 용도, 디테일 기반 글 제안 ===")
    for i, (title, reply) in enumerate(zip(titles_detail, replies_detail), 1):
        print(f"[제안 {i}] 제목: {title}")
        print(f"[제안 {i}] 내용: {reply}")
        print("-" * 40)

#[제안 3] 제목: jupyter 오류 해결 방법
#[제안 3] 내용: "오류 메시지를 알려주시면 더 정확하게 안내해 드릴 수 있을 것 같아요! 그리고 인터넷 검색이나 공식 문서를 참고하시면 문제를 해결하실 수 있을 거예요."