import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form

from AI.ocr_v2 import analyze_situation, analyze_situation_accent_purpose
from app.suggester.suggester_request import (
    GenerateSuggestionRequest,
    SuggestionRequest,
    UpdateSuggestionTagsRequest,
)
from app.suggester.suggester_response import (
    AnalyzeImagesConversationResponse,
    SuggestionResponse,
    GetMySuggestionsResponse,
    DeleteSuggestionResponse,
    GenerateSuggestionsResponse,
    GenerateSuggestion,
)
from app.core.enums import PurposeType
from app.suggester.suggester_service import SuggesterService
from app.user.user_document import UserDocument
from app.utils.jwt_handler import JwtHandler

router = APIRouter(prefix="/suggester", tags=["suggester"])
logger = logging.getLogger(__name__)


@router.post(
    "/analyze/image",
    summary="최대 사진 4장까지 보내면 AI 상황을 분석하여 대답함",
    response_model=AnalyzeImagesConversationResponse,
)
async def analyze_images(
    purpose: PurposeType = Form(...),
    image_file_1: Optional[UploadFile] = File(None),
    image_file_2: Optional[UploadFile] = File(None),
    image_file_3: Optional[UploadFile] = File(None),
    image_file_4: Optional[UploadFile] = File(None),
) -> AnalyzeImagesConversationResponse:

    image_files = [file for file in [image_file_1, image_file_2, image_file_3, image_file_4] if file is not None]
    if len(image_files) > 4:
        raise HTTPException(status_code=400, detail="You can only upload up to 4 images.")

    elif len(image_files) == 0:
        raise HTTPException(status_code=400, detail="You must upload at least one image.")

    files_data = [(file.filename, await file.read()) for file in image_files]

    if purpose == PurposeType.PHOTO_RESPONSE:
        situation = analyze_situation(files_data)
        tone = ""
        usage = ""

    elif purpose == PurposeType.SIMILAR_VIBE_RESPONSE:
        situation, tone, usage = analyze_situation_accent_purpose(files_data)
    else:
        raise HTTPException(status_code=400, detail="Invalid purpose.")

    return AnalyzeImagesConversationResponse(situation=situation, tone=tone, usage=usage, purpose=purpose)


@router.post(
    "/generate",
    summary="상황, 말투, 용도, 상세 정보를 받아 AI 글을 생성하여 반환",
    response_model=GenerateSuggestionsResponse,
)
async def generate_suggestion(
    request: GenerateSuggestionRequest,
) -> GenerateSuggestionsResponse:

    # TODO AI API 호출해서 올리는거
    suggestions, titles = await SuggesterService.generate_suggestions(
        situation=request.situation, tone=request.tone, usage=request.usage, detail=request.detail
    )

    result = [GenerateSuggestion(title=title, content=suggestion) for title, suggestion in zip(titles, suggestions)]
    return GenerateSuggestionsResponse(suggestions=result)


@router.post("", response_model=SuggestionResponse, summary="유저가 생성한 글제안 - 저장")
async def save_suggestion(
    request: SuggestionRequest,
    user: UserDocument = Depends(JwtHandler.get_current_user),  # ✅ JWT 인증된 사용자
) -> SuggestionResponse:
    new_suggestion = await SuggesterService.create_suggestion(user.id, request.title, request.suggestion, request.tags)

    return SuggestionResponse(
        id=str(new_suggestion.id),
        title=new_suggestion.title,
        tags=new_suggestion.tag,
        suggestion=new_suggestion.suggestion,
        updated_at=new_suggestion.updated_at,
        created_at=new_suggestion.created_at,
    )


@router.get("/{suggestion_id}", response_model=SuggestionResponse, summary="글 제안 가져오기")
async def get_suggestion(
    suggestion_id: str,
    user: UserDocument = Depends(JwtHandler.get_current_user),  # ✅ JWT 인증된 사용자
) -> SuggestionResponse:
    """ID를 기반으로 AI 추천 데이터를 가져옴"""
    suggestion = await SuggesterService.get_suggestion_by_id(suggestion_id)

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # ✅ 사용자가 자신의 데이터만 조회할 수 있도록 제한
    if suggestion.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return SuggestionResponse(
        id=str(suggestion.id),
        title=suggestion.title,
        tags=suggestion.tag,
        suggestion=suggestion.suggestion,
        updated_at=suggestion.updated_at,
        created_at=suggestion.created_at,
    )


@router.get("/user/me", response_model=GetMySuggestionsResponse, summary="내 글 제안 가져오기")
async def get_my_suggestions(
    user: UserDocument = Depends(JwtHandler.get_current_user),  # ✅ JWT 인증된 사용자
) -> GetMySuggestionsResponse:
    """현재 사용자의 AI 추천 데이터 목록을 가져옴"""
    my_suggestions = await SuggesterService.get_suggestions_by_user(user.id)
    suggestion_responses = [
        SuggestionResponse(
            id=str(my_suggestion.id),
            title=my_suggestion.title,
            tags=my_suggestion.tag,
            suggestion=my_suggestion.suggestion,
            updated_at=my_suggestion.updated_at,
            created_at=my_suggestion.created_at,
        )
        for my_suggestion in my_suggestions
    ]
    return GetMySuggestionsResponse(
        suggestions=suggestion_responses,
    )


@router.get("user/summary")
async def get_my_suggestions_summary(
    user: UserDocument = Depends(JwtHandler.get_current_user),  # ✅ JWT 인증된 사용자
) -> GetMySuggestionsResponse:
    my_suggestions = await SuggesterService.get_suggestions_by_user(user.id)
    suggestion_responses = [
        SuggestionResponse(
            id=str(my_suggestion.id),
            title=my_suggestion.title,
            tags=my_suggestion.tag,
            suggestion=my_suggestion.suggestion,
            updated_at=my_suggestion.updated_at,
            created_at=my_suggestion.created_at,
        )
        for my_suggestion in my_suggestions
    ]
    return GetMySuggestionsResponse(
        suggestions=suggestion_responses,
    )


@router.put("/{suggestion_id}", response_model=SuggestionResponse, summary="내 글 제안 수정")
async def update_suggestion(
    request: SuggestionRequest,
    suggestion_id: str,
    user: UserDocument = Depends(JwtHandler.get_current_user),  # ✅ JWT 인증된 사용자
) -> SuggestionResponse:
    suggestion = await SuggesterService.get_suggestion_by_id(suggestion_id)

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # ✅ 사용자가 자신의 데이터만 수정할 수 있도록 제한
    if suggestion.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated_suggestion = await SuggesterService.update_suggestion(
        suggestion_id, request.title, request.suggestion, request.tags
    )

    if not updated_suggestion:
        raise HTTPException(status_code=500, detail="Failed to delete suggestion")

    return SuggestionResponse(
        id=str(updated_suggestion.id),
        title=updated_suggestion.title,
        tags=updated_suggestion.tag,
        suggestion=updated_suggestion.suggestion,
        updated_at=updated_suggestion.updated_at,
        created_at=updated_suggestion.created_at,
    )


@router.delete("/{suggestion_id}", response_model=DeleteSuggestionResponse, summary="내 글 제안 삭제")
async def delete_suggestion(
    suggestion_id: str,
    user: UserDocument = Depends(JwtHandler.get_current_user),  # ✅ JWT 인증된 사용자
) -> DeleteSuggestionResponse:
    suggestion = await SuggesterService.get_suggestion_by_id(suggestion_id)

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # ✅ 사용자가 자신의 데이터만 삭제할 수 있도록 제한
    if suggestion.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    success = await SuggesterService.delete_suggestion(suggestion_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete suggestion")

    return DeleteSuggestionResponse(
        message="Suggestion deleted successfully",
        deleted_suggestion_id=suggestion_id,
    )


@router.put("/tag")
async def update_suggestion_tag(
    request: UpdateSuggestionTagsRequest, user: UserDocument = Depends(JwtHandler.get_current_user)
) -> SuggestionResponse:
    suggestion = await SuggesterService.get_suggestion_by_id(request.suggestion_id)

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if suggestion.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated_suggestion = await SuggesterService.update_suggestion_tags(request.suggestion_id, request.tags)

    return SuggestionResponse(
        id=str(updated_suggestion.id),
        title=updated_suggestion.title,
        tags=updated_suggestion.tag,
        suggestion=updated_suggestion.suggestion,
        updated_at=updated_suggestion.updated_at,
        created_at=updated_suggestion.created_at,
    )
