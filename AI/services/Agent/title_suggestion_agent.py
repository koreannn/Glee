from AI.glee_agent import title_service


class TitleSuggestionAgent:
    def run(self, input_text: str):
        return title_service._generate_title_suggestions(input_text)
