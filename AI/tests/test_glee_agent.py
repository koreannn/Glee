import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from pathlib import Path
from typing import List


from unittest.mock import Mock, patch

# 상대 경로로 임포트 변경
from AI.glee_agent import (
    OrchestratorAgent,
    OcrAgent,
    SummarizerAgent,
    TitleSuggestionAgent,
    ReplySuggestionAgent,
    StyleAnalysisAgent,
    parse_style_analysis,
    parse_suggestion,
)


@pytest.fixture
def test_image_files() -> List[str]:
    """테스트용 이미지 파일 경로를 반환하는 fixture"""
    base_path = Path(__file__).parent.parent
    return [
        str(base_path / "OCR_Test1.png"),
        str(base_path / "OCR_Test2.png"),
        str(base_path / "OCR_Test3.png"),
        str(base_path / "OCR_Test4.png"),
    ]


@pytest.fixture
def sample_text():
    return "레몬 한 개에는 레몬 한 개 만큼의 비타민C가 포함되어있습니다."


def test_parse_style_analysis():  # 원하는 형태로 파싱하는지를 테스트
    test_input = """
    상황: 친구와 대화
    말투: 친근한
    용도: 일상대화
    """
    situation, accent, purpose = parse_style_analysis(test_input)
    assert situation == "친구와 대화"
    assert accent == "친근한"
    assert purpose == "일상대화"


def test_parse_suggestion():
    test_input = "제목: 테스트 제목"
    result, _ = parse_suggestion(test_input)
    assert result == "테스트 제목"


class TestOcrAgent:  # Test: 1. 문자열을 반환하는지 2. 빈 문자열을 반환하지 않는지
    def test_run_success(self, test_image_files):
        # 파일 경로를 튜플 리스트로 변환
        image_tuples = [(path, b"dummy_image_data") for path in test_image_files]

        with patch("AI.glee_agent.CLOVA_OCR") as mock_ocr:
            # 유효한 OCR 결과를 반환하도록 설정
            mock_ocr.return_value = {"images": [{"fields": [{"inferText": "OCR결과 테스트"}]}]}

            # extract_text_from_ocr_result 함수도 모킹
            with patch("AI.glee_agent.extract_text_from_ocr_result") as mock_extract:
                mock_extract.return_value = "OCR결과 테스트"

                ocr_agent = OcrAgent()
                result = ocr_agent.run(image_tuples)
                assert isinstance(result, str)
                assert len(result.strip()) > 0


class TestSummarizerAgent:
    def test_run_success(self, sample_text):
        with patch("AI.glee_agent.Analyze.situation_summary") as mock_summary:
            mock_summary.return_value = "상황 요약 테스트"
            summarizer = SummarizerAgent()
            result = summarizer.run(sample_text)
            assert isinstance(result, str)
            assert len(result.strip()) > 0


class TestStyleAnalyzer:
    """
    1. 리턴값 전부 온전히 반환하는지: 1) (상황, 말투, 용도 전체 분석결과) 2) 상황 3) 말투 4) 용도
    2. 리턴값 타입이 모두 문자열인지
    """

    def test_run_success(self, sample_text):
        example_result = """
        상황: 테스트 상황
        말투: 친근한
        용도: 일상 대화
        """
        with patch("AI.glee_agent.Analyze.style_analysis") as mock_analysis:
            mock_analysis.return_value = example_result
            analyzer = StyleAnalysisAgent()
            result = analyzer.run(sample_text)
            assert isinstance(result, tuple)
            assert len(result) == 4
            assert isinstance(result[0], str)  # 상황~말투~용도 의 텍스트
            assert isinstance(result[1], str)  # 상황 텍스트
            assert isinstance(result[2], str)  # 말투 텍스트
            assert isinstance(result[3], str)  # 용도 텍스트


class TestOrchestratorAgent:
    def test_run_reply_mode_success(self, sample_text):
        orchestrator = OrchestratorAgent()
        with patch.multiple(orchestrator, summarizer_agent=Mock(), title_agent=Mock(), reply_agent_old=Mock()):
            orchestrator.summarizer_agent.run.return_value = "상황 요약"
            orchestrator.title_agent.run.return_value = ["제목 제안1", "제목 제안2"]
            orchestrator.reply_agent_old.run.return_value = ["답변 제안1", "답변 제안2"]

            result = orchestrator.run_reply_mode(sample_text)
            assert isinstance(result, dict)
            assert "situation" in result
            assert "accent" in result
            assert "purpose" in result
            assert "titles" in result
            assert "replies" in result

    def test_run_style_mode_success(self, sample_text):
        orchestrator = OrchestratorAgent()
        with patch.multiple(orchestrator, style_agent=Mock(), title_agent=Mock(), reply_agent_new=Mock()):
            # 4개의 값을 반환하도록 수정 (전체 결과, 상황, 말투, 용도)
            orchestrator.style_agent.run.return_value = ("전체 분석 결과", "상황 분석", "말투 분석", "용도 분석")
            orchestrator.title_agent.run.return_value = ["제목 제안1", "제목 제안2"]
            orchestrator.reply_agent_new.run.return_value = ["답변 제안1", "답변 제안2"]

            result = orchestrator.run_style_mode(sample_text)
            assert isinstance(result, dict)
            assert "situation" in result
            assert "titles" in result
            assert "replies" in result

    def test_run_manual_mode_success(self, sample_text):
        orchestrator = OrchestratorAgent()
        with patch.multiple(orchestrator, title_agent=Mock(), reply_agent_new=Mock()):
            orchestrator.title_agent.run.return_value = ["제목 제안1", "제목 제안2"]
            orchestrator.reply_agent_new.run.return_value = ["답변 제안1", "답변 제안2"]

            # 필요한 매개변수 추가
            situation = "테스트 상황"
            accent = "친근한"
            purpose = "일상 대화"
            details = "추가 세부 정보"

            result = orchestrator.run_manual_mode(situation, accent, purpose, details)
            assert isinstance(result, dict)
            assert "situation" in result
            assert "titles" in result
            assert "replies" in result
