from AI.services.Agent.ocr_cache import OcrCache
from AI.services.Analysis.analyze_situation import Analyze
from AI.services.Generation.reply_seggestion import ReplySuggestion
from AI.services.Generation.title_suggestion import TitleSuggestion
from AI.services.OCR.get_ocr_text import CLOVA_OCR
from AI.services.videosearch_service import VideoSearchService

ocr_service = CLOVA_OCR()
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
video_search_service = VideoSearchService()
ocr_cache = OcrCache()