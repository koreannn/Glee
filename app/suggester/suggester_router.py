import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form

from app.suggester.suggester_request import GenerateSuggestionRequest
from app.suggester.suggester_response import AnalyzeImagesConversationResponse, GenerateSuggestionResponse
from app.suggester.enums import PurposeType
from app.user.user_document import UserDocument
from app.utils.jwt_handler import JwtHandler

router = APIRouter(prefix="/suggester", tags=["Analyze"])
logger = logging.getLogger(__name__)


@router.post(
    "/analyze/image",
    summary="최대 사진 4장까지 보내면 AI 상황을 분석하여 대답함",
    response_model=AnalyzeImagesConversationResponse,
)
async def analyze_images(
    purpose: PurposeType = Form(...),
    image_file_1: Optional[UploadFile] = File(...),
    image_file_2: Optional[UploadFile] = File(...),
    image_file_3: Optional[UploadFile] = File(...),
    image_file_4: Optional[UploadFile] = File(...),
    user: UserDocument = Depends(JwtHandler.get_current_user),
) -> AnalyzeImagesConversationResponse:
    image_files = [file for file in [image_file_1, image_file_2, image_file_3, image_file_4] if file is not None]
    if len(image_files) > 4:
        raise HTTPException(status_code=400, detail="You can only upload up to 4 images.")

    elif len(image_files) == 0:
        raise HTTPException(status_code=400, detail="You must upload at least one image.")

    # TODO AI API 호출해서 올리는거
    purpose = purpose
    situation = "상황"
    tone = "말투"
    usage = "용도"
    return AnalyzeImagesConversationResponse(situation=situation, tone=tone, usage=usage, purpose=purpose)


@router.post(
    "/generate/",
    summary="상황, 말투, 용도, 상세 정보를 받아 AI 글을 생성하여 반환",
    response_model=GenerateSuggestionResponse,
)
async def generate_suggestion(
    request: GenerateSuggestionRequest,
    user: UserDocument = Depends(JwtHandler.get_current_user),
) -> GenerateSuggestionResponse:

    # TODO AI API 호출해서 올리는거
    suggestion = "suggestion"
    return GenerateSuggestionResponse(suggestion=suggestion)
