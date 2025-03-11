# # AI/utils/get_embeddings.py
#
# import os
# from typing import List, Optional, Dict, Any
# from loguru import logger
# import numpy as np
# from langchain_core.embeddings import Embeddings
#
#
# class LocalEmbeddings(Embeddings):
#     """로컬에서 실행되는 sentence-transformers 기반 임베딩 클래스"""
#
#     def __init__(
#         self,
#         model_name: str = "snunlp/KR-SBERT-V40K-klueNLI-augSTS",  # 한국어에 특화된 고성능 모델 (768 차원)
#         cache_folder: Optional[str] = None,  # 모델 캐시 폴더 경로
#         device: str = "mps",  # 실행 디바이스 (cpu 또는 cuda)
#     ):
#         try:
#             from sentence_transformers import SentenceTransformer
#
#             self.model = SentenceTransformer(model_name, cache_folder=cache_folder, device=device)
#             logger.info(f"임베딩 모델 '{model_name}' 로드 완료 (device: {device})")
#         except ImportError:
#             logger.error(
#                 "sentence-transformers 패키지가 설치되어 있지 않습니다. 'pip install sentence-transformers'를 실행하세요."
#             )
#             raise ImportError(
#                 "sentence-transformers 패키지가 필요합니다. 'pip install sentence-transformers'를 실행하세요."
#             )
#         except Exception as e:
#             logger.error(f"임베딩 모델 로드 중 오류 발생: {e}")
#             raise e
#
#         self.model_name = model_name
#         self.device = device
#
#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         """
#         문서 리스트를 임베딩 벡터 리스트로 변환
#
#         Args:
#             texts: 임베딩할 문서 리스트
#
#         Returns:
#             임베딩 벡터 리스트
#         """
#         try:
#             embeddings = self.model.encode(texts, convert_to_numpy=True)
#             return embeddings.tolist()
#         except Exception as e:
#             logger.error(f"문서 임베딩 생성 중 오류 발생: {e}")
#             raise e
#
#     def embed_query(self, text: str) -> List[float]:  # 쿼리 텍스트를 임베딩으로 변환
#         try:
#             embedding = self.model.encode(text, convert_to_numpy=True)
#             return embedding.tolist()
#         except Exception as e:
#             logger.error(f"쿼리 임베딩 생성 중 오류 발생: {e}")
#             raise e
#
#
# # 외부에서 사용할 수 있도록 CustomEmbeddings 이름으로 내보내기
# CustomEmbeddings = LocalEmbeddings
