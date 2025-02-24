from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form

from app.analyze.analyze_response import AnalyzeImagesConversationResponse
from app.analyze.enums import PurposeType
from app.user.user_document import UserDocument
from app.utils.jwt_handler import JwtHandler

router = APIRouter(prefix="/analyze", tags=["Analyze"])


@router.post(
    "/image/conversation",
    summary="최대 사진 4장까지 보내면 AI 상황을 분석하여 대답함",
    response_model=AnalyzeImagesConversationResponse,
)
async def analyze_images_conversation(
    purpose: PurposeType = Form(..., description="분석 목적 (예: 일반 대화 분석, 감성 분석 등)"),
    files: list[UploadFile] = File(..., description="Maximum of 4 image files"),
    user: UserDocument = Depends(JwtHandler.get_current_user),
) -> AnalyzeImagesConversationResponse:

    if len(files) > 4:
        raise HTTPException(status_code=400, detail="You can only upload up to 4 images.")

    # TODO AI API 호출해서 올리는거

    situation = "상황"
    tone = "말투"
    usage = "용도"
    purpose = purpose

    return AnalyzeImagesConversationResponse(situation=situation, tone=tone, usage=usage, purpose=purpose)
