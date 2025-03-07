class OcrPostProcessingAgent:
    def run(self, ocr_text: str) -> str:
        cleaned_text = ocr_text
        cleaned_text = re.sub(r"[^가-힣a-zA-Z0-9\s.,?!]", "", cleaned_text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        logger.info(f"Text after cleaning:\n{cleaned_text}")

        return cleaned_text