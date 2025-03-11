from ai.services.analysis.analyze_situation import Analyze
from ai.services.generation.reply_seggestion import ReplySuggestion
from ai.services.generation.title_suggestion import TitleSuggestion
from ai.services.ocr.clova_ocr import ClovaOcr


ocr_service = ClovaOcr()
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
