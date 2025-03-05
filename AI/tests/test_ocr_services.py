import pytest
import pytest_asyncio
from pathlib import Path
from ..ocr_v2 import (
    CLOVA_AI_Situation_Summary,
    CLOVA_AI_Title_Suggestions,
    CLOVA_AI_Reply_Suggestions,
    CLOVA_AI_New_Reply_Suggestions,
    CLOVA_AI_Style_Analysis,
    analyze_situation,
    analyze_situation_accent_purpose,
    generate_suggestions_situation,
    generate_reply_suggestions_accent_purpose,
    generate_reply_suggestions_detail,
    CLOVA_OCR,
)


@pytest.fixture
def test_image_files():
    """테스트용 이미지 파일 fixture"""
    image_files = []
    test_images = [
        "./AI/OCR_Test1.png",
        "./AI/OCR_Test2.png",
        "./AI/OCR_Test3.png",
        "./AI/OCR_Test4.png",
    ]

    for image_path in test_images:
        try:
            with open(image_path, "rb") as f:
                file_content = f.read()
                image_files.append((image_path, file_content))
        except Exception as e:
            pytest.skip(f"테스트 이미지를 불러올 수 없습니다: {e}")

    return image_files


def test_clova_ocr(test_image_files):
    """OCR 기능 테스트"""
    result = CLOVA_OCR(test_image_files)
    assert result != "", "OCR 결과가 비어있지 않아야 합니다"


def test_situation_summary():
    """상황 요약 기능 테스트"""
    test_text = "아, 배고프다."
    result = CLOVA_AI_Situation_Summary(test_text)
    assert result != "", "상황 요약 결과가 비어있지 않아야 합니다"


def test_title_suggestions():
    """제목 추천 기능 테스트"""
    test_text = "아, 배고프다."
    result = CLOVA_AI_Title_Suggestions(test_text)
    assert result != "", "제목 추천 결과가 비어있지 않아야 합니다"


def test_reply_suggestions():
    """답변 추천 기능 테스트"""
    test_text = "식사 시간이 다가오면 배고픔을 느끼는 것은 자연스러운 일이죠."
    result = CLOVA_AI_Reply_Suggestions(test_text)
    assert isinstance(result, list), "결과가 리스트 형태여야 합니다"
    assert len(result) > 0, "최소 하나 이상의 답변이 생성되어야 합니다"


def test_new_reply_suggestions():
    """새로운 답변 추천 기능 테스트"""
    result = CLOVA_AI_New_Reply_Suggestions(
        "배고픈 상황",
        "친절하게",
        "카카오톡",
        "친절하지만 퉁명스럽게 말해주세요"
    )
    assert isinstance(result, list), "결과가 리스트 형태여야 합니다"
    assert len(result) > 0, "최소 하나 이상의 답변이 생성되어야 합니다"


def test_style_analysis():
    """말투 분석 기능 테스트"""
    test_text = "아, 배고프다."
    tone, use_case = CLOVA_AI_Style_Analysis(test_text)
    assert tone is not None, "말투가 반환되어야 합니다"
    assert use_case is not None, "용도가 반환되어야 합니다"


def test_analyze_situation(test_image_files):
    """이미지 기반 상황 분석 테스트"""
    result = analyze_situation(test_image_files)
    assert result != "", "상황 분석 결과가 비어있지 않아야 합니다"


def test_analyze_situation_accent_purpose(test_image_files):
    """이미지 기반 상황/말투/용도 분석 테스트"""
    situation, accent, purpose = analyze_situation_accent_purpose(test_image_files)
    assert all([situation, accent, purpose]), "모든 결과값이 존재해야 합니다"


def test_generate_suggestions_situation():
    """상황 기반 제안 생성 테스트"""
    suggestions, title = generate_suggestions_situation("아, 자고싶다.")
    assert isinstance(suggestions, list), "suggestions가 리스트여야 합니다"
    assert title != "", "제목이 생성되어야 합니다"


def test_generate_reply_suggestions_accent_purpose():
    """상황/말투/용도 기반 답변 생성 테스트"""
    suggestions, title = generate_reply_suggestions_accent_purpose(
        "아, 자고싶다.", "친절하게", "카카오톡"
    )
    assert isinstance(suggestions, list), "suggestions가 리스트여야 합니다"
    assert title != "", "제목이 생성되어야 합니다"


def test_generate_reply_suggestions_detail():
    """상세 정보 포함 답변 생성 테스트"""
    suggestions, title = generate_reply_suggestions_detail(
        "아, 자고싶다.",
        "친절하게",
        "카카오톡",
        "자고싶다는 말을 친절하고 차분하게 전달하고싶어요"
    )
    assert isinstance(suggestions, list), "suggestions가 리스트여야 합니다"
    assert title != "", "제목이 생성되어야 합니다"