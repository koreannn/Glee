from AI.utils.services import reply_service


class ReplySuggestionAgent:
    def __init__(self, variant="old", max_retries=2):
        self.variant = variant
        self.max_retries = max_retries

    async def run(self, input_text: str):
        retry = 0
        suggestions = []
        while retry <= self.max_retries:
            if self.variant == "old":
                suggestions = await reply_service.generate_basic_reply(input_text)
            else:
                suggestions = await reply_service.generate_detailed_reply(input_text)
            if suggestions and len(suggestions[0].strip()) < 10 and retry < self.max_retries:
                input_text += "\n좀 더 구체적으로, 길이를 늘려서 답변해줘."
                retry += 1
                continue
            else:
                break
        return suggestions
