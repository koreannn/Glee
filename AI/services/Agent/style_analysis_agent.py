from AI.glee_agent import parse_style_analysis, situation_service

class StyleAnalysisAgent:
    def run(self, input_text: str):
        style_result = situation_service._make_api_request("config_Style_Analysis.yaml", input_text, random_seed=True)
        situation, accent, purpose = parse_style_analysis(style_result)
        return style_result, situation, accent, purpose
