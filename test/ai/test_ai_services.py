# import pytest
# from pathlib import Path
# from typing import List
#
# from loguru import logger
# from ai.services.ocr.clova_ocr import ClovaOcr
# from ai.services.analysis.analyze_situation import Analyze
# from ai.services.generation.reply_seggestion import ReplySuggestion
# from ai.services.generation.title_suggestion import TitleSuggestion
#

#
#
# @pytest.fixture
# def test_image_files() -> List[str]:
#     """테스트용 이미지 파일 경로를 반환하는 fixture"""
#     base_path = Path(__file__).parent.parent
#     return [
#         str(base_path / "ocr_test1.png"),
#         str(base_path / "ocr_test2.png"),
#         str(base_path / "ocr_test3.png"),
#         str(base_path / "ocr_test4.png"),
#     ]
#
#
# @pytest.fixture
# def services():
#     """서비스 인스턴스들을 반환하는 fixture"""
#     return {"situation": Analyze(), "reply": ReplySuggestion(), "title": TitleSuggestion()}
#
#
# def test_ocr_service(test_image_files):  # ocr 테스트
#     logger.info("\n1. ocr 텍스트 인식 테스트")
#     result = ClovaOcr(test_image_files)
#     assert isinstance(result, str)
#     assert len(result) > 0
#
#
# def test_analyze_situation(test_image_files, services):  # 상황 분석 테스트
#     logger.info("\n2. 상황 분석 테스트")
#     # ocr 텍스트 추출
#     image2text = ClovaOcr(test_image_files)
#     assert image2text, "ocr 텍스트가 추출되지 않았습니다"
#
#     # 상황 요약
#     situation = services["situation"].situation_summary(image2text)
#     assert isinstance(situation, str)
#     assert len(situation) > 0, "상황 요약이 생성되지 않았습니다"
#
#
# def test_analyze_situation_with_style(test_image_files, services):  # 말투, 용도 분석 테스트
#     logger.info("\n3. 말투, 용도 분석 테스트")
#     # ocr 텍스트 추출
#     image2text = ClovaOcr(test_image_files)
#     assert image2text, "ocr 텍스트가 추출되지 않았습니다"
#
#     # 상황 요약
#     situation = services["situation"].situation_summary(image2text)
#     assert isinstance(situation, str)
#     assert len(situation) > 0
#
#     # 말투, 용도 분석
#     accent, purpose = services["situation"].style_analysis(image2text)
#     assert isinstance(accent, str)
#     assert isinstance(purpose, str)
#     assert len(accent) > 0
#     assert len(purpose) > 0
#
#
# def test_generate_suggestions(test_image_files, services):  # 상황 -> 답변 생성 테스트
#     logger.info("\n4. 상황 -> 답변 생성 테스트")
#     # 상황 분석
#     image2text = ClovaOcr(test_image_files)
#     situation = services["situation"].situation_summary(image2text)
#
#     # 답변 생성
#     suggestions = services["reply"].generate_basic_reply(situation)
#     assert isinstance(suggestions, list)
#     assert len(suggestions) > 0
#     assert all(isinstance(s, str) for s in suggestions)
#
#     # 제목 생성
#     titles = services["title"].generate_title_suggestions(situation)
#     assert isinstance(titles, list)
#     assert len(titles) > 0
#     assert all(isinstance(t, str) for t in titles)
#
#
# def test_generate_detailed_suggestions(test_image_files, services):  # 상황, 말투, 용도 -> 상세 답변 생성 테스트
#     logger.info("\n5. 상황, 말투, 용도 -> 상세 답변 생성 테스트")
#     # 상황 분석
#     image2text = ClovaOcr(test_image_files)
#     situation = services["situation"].situation_summary(image2text)
#
#     # 테스트용 파라미터
#     test_accent = "귀엽고 사랑스러운 말투"
#     test_purpose = "카카오톡"
#     test_description = "친구들과 함께 카카오톡을 사용하는 경우"
#
#     # 상세 답변 생성
#     suggestions = services["reply"].generate_detailed_reply(situation, test_accent, test_purpose, test_description)
#     assert isinstance(suggestions, list)
#     assert len(suggestions) > 0
#     assert all(isinstance(s, str) for s in suggestions)
#
#     # 제목 생성
#     titles = services["title"].generate_title_suggestions(situation)
#     assert isinstance(titles, list)
#     assert len(titles) > 0
#     assert all(isinstance(t, str) for t in titles)
#
#
# @pytest.mark.parametrize(
#     "invalid_input",
#     [
#         None,
#         [],
#         ["non_existent_file.png"],
#     ],
# )
# def test_ocr_service_invalid_input(invalid_input):
#     """ocr 서비스 에러 케이스 테스트"""
#     with pytest.raises(Exception):
#         ClovaOcr(invalid_input)
#
#
# @pytest.mark.parametrize(
#     "invalid_text",
#     [
#         None,
#         "",
#         "   ",
#     ],
# )
# def test_services_invalid_input(services, invalid_text):
#     """각 서비스의 에러 케이스 테스트"""
#     # 상황 요약 테스트
#     result = services["situation"].situation_summary(invalid_text)
#     assert result == "" or result is None
#
#     # 답변 생성 테스트
#     suggestions = services["reply"].generate_basic_reply(invalid_text)
#     assert isinstance(suggestions, list)
#     assert len(suggestions) == 0 or all(isinstance(s, str) for s in suggestions)
#
#     # 제목 생성 테스트
#     titles = services["title"].generate_title_suggestions(invalid_text)
#     assert isinstance(titles, list)
#     assert len(titles) == 0 or all(isinstance(t, str) for t in titles)
