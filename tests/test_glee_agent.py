import pytest
from unittest.mock import Mock, patch
from AI.glee_agent import (
    OcrProcessor,
    TextSummarizer,
    TitleGenerator,
    ReplyGenerator,
    StyleAnalyzer,
    MessageOrchestrator,
    parse_style_analysis,
    parse_suggestion,
)

@pytest.fixture
def sample_image():
    # 테스트용 이미지 데이터 준비
    return [("test_image.jpg", b"dummy_image_data")]

@pytest.fixture
def sample_text():
    return "안녕하세요. 이것은 테스트 텍스트입니다. 상황 분석과 답변 생성을 테스트하기 위한 예시 텍스트입니다."

class TestOcrProcessor:
    def test_run_success(self, sample_image):
        with patch('AI.glee_agent.CLOVA_OCR') as mock_ocr:
            mock_ocr.return_value = "테스트 OCR 결과"
            processor = OcrProcessor()
            result = processor.run(sample_image)
            assert isinstance(result, str)
            assert len(result) > 0

class TestTextSummarizer:
    def test_run_success(self, sample_text):
        with patch('AI.glee_agent.situation_service.situation_summary') as mock_summary:
            mock_summary.return_value = "요약된 테스트 텍스트"
            summarizer = TextSummarizer()
            result = summarizer.run(sample_text)
            assert isinstance(result, str)
            assert len(result) > 0

class TestStyleAnalyzer:
    def test_run_success(self, sample_text):
        expected_result = """
        상황: 테스트 상황
        말투: 친근한
        용도: 일상대화
        """
        with patch('AI.glee_agent.situation_service.style_analysis') as mock_style:
            mock_style.return_value = expected_result
            analyzer = StyleAnalyzer()
            result, situation, accent, purpose = analyzer.run(sample_text)
            assert isinstance(result, str)
            assert isinstance(situation, str)
            assert isinstance(accent, str)
            assert isinstance(purpose, str)

class TestMessageOrchestrator:
    def test_run_reply_mode(self, sample_text):
        orchestrator = MessageOrchestrator()
        with patch.multiple(orchestrator,
                          summarizer=Mock(),
                          title_generator=Mock(),
                          reply_generator_old=Mock()):
            orchestrator.summarizer.run.return_value = "요약"
            orchestrator.title_generator.run.return_value = ["제목1", "제목2"]
            orchestrator.reply_generator_old.run.return_value = ["답변1", "답변2"]
            
            result = orchestrator.run_reply_mode(sample_text)
            assert isinstance(result, dict)
            assert "situation" in result
            assert "titles" in result
            assert "replies" in result

def test_parse_style_analysis():
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