from typing import Dict, List, Union
from AI.glee_agent import OcrAgent, SummarizerAgent, TitleSuggestionAgent, ReplySuggestionAgent, StyleAnalysisAgent, FeedbackAgent

class OrchestratorAgent:
    def __init__(self):
        self.ocr_agent = OcrAgent()
        self.summarizer_agent = SummarizerAgent()
        self.title_agent = TitleSuggestionAgent()
        self.reply_agent_old = ReplySuggestionAgent(variant="old")
        self.reply_agent_new = ReplySuggestionAgent(variant="new")
        self.style_agent = StyleAnalysisAgent()
        self.feedback_agent = FeedbackAgent()

    def run_reply_mode(self, input_text: str) -> Dict[str, Union[str, List[str]]]:
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
            "replies": replies,
        }

    def run_style_mode(self, input_text: str) -> Dict[str, Union[str, List[str]]]:
        # 스타일 분석 (상황, 말투, 용도 추출)
        style_result, situation, tone, usage = self.style_agent.run(input_text)
        style_result = self.feedback_agent.check_and_improve(style_result, input_text, self.style_agent)

        # 제목 제안 생성
        titles = self.title_agent.run(situation)

        # 답변 제안 생성 (말투, 용도 정보 활용)
        detailed_input = f"상황: {situation}\n말투: {tone}\n용도: {usage}"
        replies = self.reply_agent_new.run(detailed_input)
        replies = [
            self.feedback_agent.check_and_improve(reply, detailed_input, self.reply_agent_new) for reply in replies
        ]

        return {
            "situation": situation,
            "accent": tone,
            "purpose": usage,
            "titles": titles,
            "replies": replies,
            "style_analysis": style_result,
        }

    def run_manual_mode(
        self, situation: str, accent: str, purpose: str, details: str
    ) -> Dict[str, Union[str, List[str]]]:
        # 입력 정보에 기반하여 전체 프롬프트 생성 (수동 입력으로 받을 경우)
        detailed_input = f"상황: {situation}\n말투: {accent}\n용도: {purpose}\n추가 설명: {details}"

        # 제목 제안 생성
        titles = self.title_agent.run(situation)

        # 답변 제안 생성 (말투, 용도, 추가 설명 정보 활용)
        replies = self.reply_agent_new.run(detailed_input)
        replies = [
            self.feedback_agent.check_and_improve(reply, detailed_input, self.reply_agent_new) for reply in replies
        ]

        return {
            "situation": situation,
            "accent": accent,
            "purpose": purpose,
            "details": details,
            "titles": titles,
            "replies": replies,
        }