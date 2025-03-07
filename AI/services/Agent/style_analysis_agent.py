class StyleAnalysisAgent:
    def run(self, input_text: str):
        style_result = situation_service.style_analysis(input_text)
        situation, accent, purpose = parse_style_analysis(style_result)
        return style_result, situation, accent, purpose