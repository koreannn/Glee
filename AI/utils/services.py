from AI.services.Agent.ocr_cache import OcrCache
from AI.services.Analysis.analyze_situation import Analyze
from AI.services.Generation.reply_seggestion import ReplySuggestion
from AI.services.Generation.title_suggestion import TitleSuggestion
from AI.services.OCR.clova_ocr import ClovaOcr


ocr_service = ClovaOcr()
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
ocr_cache = OcrCache()
