from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import uvicorn
from ocr_v2 import CLOVA_OCR  # CLOVA_OCR 함수는 동기(synchronous) 함수라고 가정
from loguru import logger

app = FastAPI()


@app.post("/uploadfiles/")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    여러 파일을 한번에 업로드 받아 CLOVA_OCR 함수로 전달한 후,
    OCR 처리된 결과를 JSON 형태로 반환합니다.
    """
    try:
        # CLOVA_OCR 함수가 동기 함수이므로, 직접 호출합니다.
        result_text = CLOVA_OCR(files)

        if not result_text:
            # OCR 결과가 없는 경우, 400 에러를 발생시킵니다.
            raise HTTPException(status_code=400, detail="OCR 결과가 없습니다.")

        return {"extracted_text": result_text}
    except Exception as e:
        logger.error(f"OCR 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {e}")


if __name__ == "__main__":
    # 파일명이 app.py인 경우 "app:app"으로 지정합니다.
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
