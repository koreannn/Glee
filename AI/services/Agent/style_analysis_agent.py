from typing import Tuple

from AI.utils.services import situation_service


class StyleAnalysisAgent:
    def parse_style_analysis(self, result: str) -> Tuple[str, str, str]:
        """스타일 분석 결과에서 상황, 말투, 용도를 추출합니다."""
        situation = ""
        accent = ""
        purpose = ""

        for line in result.strip().split("\n"):
            line = line.strip()
            if line.startswith("상황"):
                situation = line.replace("상황:", "").strip()
            elif line.startswith("말투"):
                accent = line.replace("말투:", "").strip()
            elif line.startswith("용도"):
                purpose = line.replace("용도:", "").strip()

        return situation, accent, purpose

    async def run(self, input_text: str):
        style_result = await situation_service.make_api_request(
            "config_Style_Analysis.yaml", input_text, random_seed=True
        )
        situation, accent, purpose = self.parse_style_analysis(style_result)
        return style_result, situation, accent, purpose
