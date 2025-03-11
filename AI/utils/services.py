from AI.services.agent.ocr_cache import OcrCache
from AI.services.analysis.analyze_situation import Analyze
from AI.services.generation.reply_seggestion import ReplySuggestion
from AI.services.generation.title_suggestion import TitleSuggestion
from AI.services.ocr.clova_ocr import ClovaOcr


ocr_service = ClovaOcr()
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
ocr_cache = OcrCache()
