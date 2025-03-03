import os
import time
import json
import uuid
import requests

from loguru import logger
from app.core.settings import settings

def CLOVA_OCR(image_files: list[tuple[str, bytes]]) -> str:
    """
    여러 이미지 파일 경로 리스트를 받아, 각 파일에 대해 OCR 요청을 개별적으로 보내고,
    그 결과를 합쳐서 반환합니다.
    """
    URL = os.getenv("CLOVA_OCR_URL")
    SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY")

    logger.info(f"URL: {URL}")
    logger.info(f"SECRET_KEY: {SECRET_KEY}")

    if not URL or not SECRET_KEY:
        URL = settings.CLOVA_OCR_URL
        SECRET_KEY = settings.CLOVA_OCR_SECRET_KEY
        logger.info(f"settings에서 읽은 URL: {URL}")
        logger.info(f"settings에서 읽은 SECRET_KEY: {SECRET_KEY}")

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

        # with open(file_path, "rb") as f:
        files_data = [("file", (file_name, file_data, f"image/{file_ext}"))]
        response = requests.post(URL, headers=headers, data=payload, files=files_data, json=request_json)

        # logger.error(f"파일 업로드 오류({file_name}): {e}")
        # continue

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