# import os
# from typing import Optional, Dict
# from loguru import logger
# from youtube_transcript_api import YouTubeTranscriptApi
# from googleapiclient.discovery import build
# from urllib.parse import urlparse, parse_qs
# from datetime import datetime
# import asyncio
# import sys
#
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
# # 이후 절대 경로 임포트 사용
#
#
# class TranscriptionProcessor:
#     def __init__(self):
#         # 텍스트 분할기 초기화 - 1000자 단위로 분할하고 200자 오버랩
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200,
#             length_function=len,
#         )
#
#     def process_transcription(self, transcription: list) -> list:
#         docs = []
#
#         for item in transcription:
#             video_title = item.get("video_title", "")
#             video_url = item.get("video_url", "")
#             transcript_text = item.get("transcript", "")
#             video_id = self.extract_video_id(video_url) if video_url else ""
#
#             metadata = {
#                 "source": "youtube",
#                 "video_id": video_id,
#                 "video_title": video_title,
#                 "video_url": video_url,
#                 "stored_at": datetime.now().isoformat(),
#             }
#
#             chunks = self.text_splitter.split_text(transcript_text)
#             for i, chunk in enumerate(chunks):
#                 doc = Document(
#                     page_content=chunk,
#                     metadata={
#                         **metadata,
#                         "chunk": i,
#                         "total_chunks": len(chunks),
#                     },
#                 )
#                 docs.append(doc)
#
#         return docs
#
#     def extract_video_id(self, url: str) -> str:  # 유튜브 URL에서 비디오 ID 추출
#         if "youtube.com/watch?v=" in url:
#             return url.split("youtube.com/watch?v=")[1].split("&")[0]
#         elif "youtu.be/" in url:
#             return url.split("youtu.be/")[1].split("?")[0]
#         return ""
#
#
# class TranscriptionVectorStore:
#     def __init__(self, persistent_directory: str):
#         # self.processor = TranscriptionProcessor()
#         # self.embeddings = CustomEmbeddings()
#         self.persistent_directory = persistent_directory
#         self.vector_store = None
#         self._initialize_vector_store()
#
#     def _initialize_vector_store(self):  # 벡터 저장소 초기화(또는 로드)
#         try:
#             # 임베딩 모델 차원 변경 감지를 위한 플래그 파일 경로
#             dimension_file = os.path.join(self.persistent_directory, "embedding_dimension.txt")
#             current_dimension = self.embeddings.embed_query("테스트")
#             current_dimension_size = len(current_dimension)
#
#             force_recreate = False
#
#             # 기존 차원 정보 확인
#             if os.path.exists(dimension_file):
#                 with open(dimension_file, "r") as f:
#                     stored_dimension = int(f.read().strip())
#                 if stored_dimension != current_dimension_size:
#                     logger.info(
#                         f"임베딩 차원이 변경되었습니다 ({stored_dimension} -> {current_dimension_size}). 벡터 스토어를 재생성합니다."
#                     )
#                     force_recreate = True
#
#             if os.path.exists(self.persistent_directory) and not force_recreate:
#                 logger.info(f"기존 벡터 스토어를 로드합니다. ({self.persistent_directory})")
#                 self.vector_store = Chroma(
#                     persist_directory=self.persistent_directory,
#                     embedding_function=self.embeddings,
#                 )
#             else:
#                 # 기존 벡터 스토어가 있으면 백업
#                 if os.path.exists(self.persistent_directory):
#                     import shutil
#                     import time
#
#                     backup_dir = f"{self.persistent_directory}_backup_{int(time.time())}"
#                     shutil.copytree(self.persistent_directory, backup_dir)
#                     logger.info(f"기존 벡터 스토어를 {backup_dir}에 백업했습니다.")
#                     shutil.rmtree(self.persistent_directory)
#
#                 logger.info(f"새로운 벡터 스토어를 생성합니다.")
#                 os.makedirs(self.persistent_directory, exist_ok=True)
#
#                 # 현재 임베딩 차원 정보 저장
#                 with open(dimension_file, "w") as f:
#                     f.write(str(current_dimension_size))
#                 logger.info(f"임베딩 차원 정보 저장 완료: {current_dimension_size}")
#
#         except Exception as e:
#             logger.error(f"벡터 스토어 초기화 중 오류 발생: {e}")
#             raise e
#
#     async def add_or_update_transcriptions(self, transcriptions: list):  # 자막 정보를 벡터 스토어에 추가(또는 업데이트)
#         try:
#             docs = self.processor.process_transcription(transcriptions)
#
#             if not docs:
#                 logger.warning("처리할 자막 정보가 없습니다.")
#                 return
#
#             if self.vector_store is None:
#                 logger.info("새로운 벡터 스토어를 생성합니다.")
#                 self.vector_store = Chroma.from_documents(
#                     documents=docs,
#                     embedding=self.embeddings,
#                     persist_directory=self.persistent_directory,
#                 )
#             else:
#                 for doc in docs:
#                     video_id = doc.metadata.get("video_id")
#                     if video_id:
#                         self.vector_store.delete(where={"video_id": video_id})
#
#                 logger.info(f"{len(docs)}개의 문서를 벡터 스토어에 추가합니다.")
#                 self.vector_store.add_documents(docs)
#
#             # 최신 버전의 Chroma에서는 persist() 메소드가 없을 수 있으므로 조건부로 호출하지 않음
#             # 최신 버전의 Chroma는 자동으로 저장됨
#             logger.info(f"벡터 스토어 업데이트 완료")
#
#         except Exception as e:
#             logger.error(f"자막 정보 추가 중 오류 발생: {e}")
#
#     async def search_relevant_content(self, query: str, k: int = 3):  # query와 관련된 영상 검색
#         if self.vector_store is None:
#             logger.warning("벡터 스토어가 초기화되지 않았습니다.")
#             return []
#
#         try:  # MMR 검색 알고리즘으로 다양성 확보
#             results = self.vector_store.max_marginal_relevance_search(query, k=k, fetch_k=k * 2, lambda_mult=0.7)
#             return results
#         except Exception as e:
#             logger.error(f"관련 컨텐츠 검색 중 오류 발생: {e}")
#             return []
#
#     async def get_most_relevant_transcript(self, query: str) -> dict:
#         """
#         쿼리와 가장 유사도가 높은 영상의 자막 정보만 추출합니다.
#
#         Args:
#             query: 검색 쿼리
#
#         Returns:
#             가장 유사도가 높은 영상의 자막 정보를 담은 딕셔너리
#             {
#                 "video_title": 영상 제목,
#                 "video_url": 영상 URL,
#                 "transcript": 자막 텍스트,
#                 "similarity": 유사도 점수
#             }
#         """
#         if self.vector_store is None:
#             logger.warning("벡터 스토어가 초기화되지 않았습니다.")
#             return {}
#
#         try:
#             # 가장 유사도가 높은 문서 1개만 검색
#             results = self.vector_store.similarity_search_with_score(query, k=1)
#
#             if not results:
#                 logger.warning("유사한 자막 정보를 찾지 못했습니다.")
#                 return {}
#
#             document, score = results[0]
#
#             # 유사도 점수 변환 (점수가 낮을수록 유사도가 높음)
#             similarity = 1.0 - min(score, 1.0)
#
#             return {
#                 "video_title": document.metadata.get("video_title", ""),
#                 "video_url": document.metadata.get("video_url", ""),
#                 "transcript": document.page_content,
#                 "similarity": similarity,
#             }
#         except Exception as e:
#             logger.error(f"가장 유사한 자막 정보 검색 중 오류 발생: {e}")
#             return {}
#
#     def format_search_results(self, results: list) -> str:
#         if not results:
#             return ""
#
#         formatted_text = "다음은 상황과 관련된 유튜브 영상의 자막 정보입니다.\n\n"
#
#         for i, result in enumerate(results, 1):
#             content = result.page_content
#             metadata = result.metadata
#
#             formatted_text += f"참고 자료 {i}: '{metadata.get('video_title', '제목 없음')}'\n"
#             formatted_text += f"출처: {metadata.get('video_url', '링크 없음')}\n"
#             formatted_text += f"내용: {content}\n\n"
#
#         return formatted_text
#
#
# class VideoSearchService:
#     def __init__(self):
#         self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
#         # YouTube API 클라이언트 초기화
#         self.youtube = build("youtube", "v3", developerKey=self.youtube_api_key)
#         self.next_page_token = None  # 클래스 변수로 선언
#
#         self.vector_store = TranscriptionVectorStore(persistent_directory="./vector_store")
#         self.search_threshold = 0.7  # 검색 결과 관련성 임계값
#
#     async def get_or_fetch_relevant_content(
#         self, situation: str, max_contents: int = 3, force_refresh: bool = False
#     ) -> dict:
#         try:
#             # 1st. 강제 옵션 확인
#             if force_refresh or self._contains_refresh_keywords(situation):
#                 logger.info("강제 갱신 또는 최신 정보 키워드 감지 - 유튜브에서 새로 검색합니다.")
#                 return await self._search_and_update(situation, max_contents)
#
#             # 2nd. 벡터 DB에서 검색
#             logger.info(f"벡터 DB에서 '{situation}' 관련 컨텐츠 검색 중 ..")
#             relevant_chunks = await self.vector_store.search_relevant_content(situation, k=max_contents)
#
#             # 3rd. 검색 결과 평가
#             if len(relevant_chunks) >= 3:
#                 logger.info(
#                     f"벡터 DB에 이미 컨텐츠가 충분히 많네요. 유튜브 검색 없이 종료합니다. (찾은 컨텐츠: {len(relevant_chunks)}개)"
#                 )
#                 formatted_results = self.vector_store.format_search_results(relevant_chunks)
#                 return {"source": "vector_db", "results": relevant_chunks, "formatted_text": formatted_results}
#
#             # 4th. 유튜브 검색 (벡터 DB에서 충분한 정보를 얻지 못한 경우)
#             logger.info("벡터 DB에 충분한 컨텐츠가 없네요. 유튜브 검색을 시작합니다.")
#             return await self._search_and_update(situation, max_contents)
#
#         except Exception as e:
#             logger.error(f"관련 컨텐츠 검색 중 오류 발생: {e}")
#             return {"source": "error", "results": [], "formatted_text": "", "error": str(e)}
#
#     def _contains_refresh_keywords(self, text: str) -> bool:  # 최신 정보가 필요한지 판단하는 키워드 확인
#         refresh_keywords = ["최신", "최근", "최근 정보", "최근 뉴스", "최근 트렌드"]
#         return any(keyword in text for keyword in refresh_keywords)
#
#     async def _search_and_update(self, situation: str, max_contents: int = 3) -> dict:
#         try:
#             logger.info("유튜브에서 최신 영상 검색 시작")
#             youtube_results = self.youtube_search(
#                 situation, max_results=max_contents * 5
#             )  # 더 많은 결과를 가져와서 자막 있는 영상을 찾을 확률 높임
#
#             if not youtube_results or not youtube_results.get("items", []):
#                 logger.warning("유튜브 검색 결과가 없습니다.")
#                 return {"source": "youtube", "results": [], "formatted_text": ""}
#
#             # 자막 정보 추출
#             transcripts_data = []
#
#             # 비동기 처리를 위한 작업 목록 생성
#             video_check_tasks = []
#             for item in youtube_results.get("items", []):
#                 video_id = item["id"]["videoId"]
#
#                 if not self.check_captions_available(video_id):  # 자막없는 영상일 경우, 재시도
#                     continue
#
#                 video_info = {
#                     "video_id": video_id,
#                     "video_title": item["snippet"]["title"],
#                     "title": item["snippet"]["title"],
#                     "description": item["snippet"]["description"],
#                     "video_url": f"https://www.youtube.com/watch?v={video_id}",
#                 }
#                 # 자막 확인 및 가져오기 작업을 목록에 추가
#                 video_check_tasks.append((video_id, video_info))
#
#             # 최대 max_contents*2개의 비디오만 병렬 처리 (너무 많은 요청을 동시에 보내지 않도록)
#             max_parallel = min(max_contents * 2, len(video_check_tasks))
#             processed_count = 0
#
#             # 병렬 처리를 위한 세마포어 생성
#             semaphore = asyncio.Semaphore(max_parallel)
#
#             async def process_video(video_id, video_info):
#                 async with semaphore:
#                     # 자막 확인
#                     if not await self.check_captions_available(video_id):
#                         return None
#
#                     # 자막 가져오기
#                     transcript = await self.get_video_transcripts(video_info)
#                     if transcript:
#                         return {
#                             "video_title": video_info["video_title"],
#                             "video_url": video_info["video_url"],
#                             "transcript": transcript,
#                         }
#                     return None
#
#             # 병렬로 처리할 작업 생성
#             tasks = []
#             for video_id, video_info in video_check_tasks:
#                 tasks.append(asyncio.create_task(process_video(video_id, video_info)))
#
#                 # 충분한 자막 데이터를 찾았으면 중단
#                 processed_count += 1
#                 if processed_count >= max_contents * 3:  # 최대 max_contents*3개까지만 처리
#                     break
#
#             # 모든 작업 완료 대기
#             results = await asyncio.gather(*tasks)
#
#             # None이 아닌 결과만 필터링
#             transcripts_data = [result for result in results if result is not None]
#
#             # 최대 max_contents개까지만 사용
#             transcripts_data = transcripts_data[:max_contents]
#
#             if not transcripts_data:
#                 logger.warning("자막 있는 영상을 찾지 못했습니다.")
#                 return {"source": "no_transcripts", "results": [], "formatted_text": ""}
#
#             # 자막 정보 벡터 DB에 추가
#             await self.vector_store.add_or_update_transcriptions(transcripts_data)
#
#             relevant_chunks = await self.vector_store.search_relevant_content(situation, k=max_contents)
#             formatted_results = self.vector_store.format_search_results(relevant_chunks)
#
#             return {"source": "youtube_new", "results": relevant_chunks, "formatted_text": formatted_results}
#
#         except Exception as e:
#             logger.error(f"유튜브 검색 및 자막 추가 중 오류 발생: {e}")
#             return {"source": "error", "results": [], "formatted_text": "", "error": str(e)}
#
#     # 검색어(쿼리)를 받아서 관련 영상 정보(id, title, description, url)를 반환
#     # description은 영상 설명란에 있는 설명
#     def youtube_search(self, query: str, max_results: int = 50, page_token: str = None) -> Dict:
#         try:
#             # API 키 확인
#             if not self.youtube_api_key:
#                 logger.error("YouTube API 키가 설정되지 않았습니다.")
#                 return {"items": []}
#
#             # 검색어 확인
#             if not query.strip():
#                 logger.error("검색어가 비어있습니다.")
#                 return {"items": []}
#
#             # YouTube 검색 수행
#             search_response = (
#                 self.youtube.search()
#                 .list(
#                     q=query,
#                     part="id,snippet",
#                     maxResults=max_results,
#                     type="video",
#                     relevanceLanguage="ko",
#                     safeSearch="none",
#                     pageToken=page_token,
#                 )
#                 .execute()
#             )
#
#             # 검색 결과 처리
#             valid_items = []
#             for item in search_response.get("items", []):
#                 try:
#                     if item["id"]["kind"] == "youtube#video":
#                         video_info = {
#                             "id": {"videoId": item["id"]["videoId"]},
#                             "snippet": {
#                                 "title": item["snippet"]["title"],
#                                 "description": item["snippet"]["description"],
#                             },
#                         }
#
#                         if all([item["id"]["videoId"], item["snippet"]["title"], item["snippet"]["description"]]):
#                             valid_items.append(video_info)
#                             logger.info(
#                                 f"검색 결과: {{'id': '{item['id']['videoId']}', 'title': '{item['snippet']['title']}', 'description': '{item['snippet']['description'][:50]}...'}}"
#                             )
#                 except Exception as e:
#                     logger.error(f"영상 정보 추출 중 누락된 필드가 있습니다: {e}")
#                     continue
#
#             return {"items": valid_items}
#
#         except Exception as e:
#             logger.error(f"YouTube 검색 중 오류 발생: {e}")
#             return {"items": []}
#
#     async def check_captions_available(self, video_id: str) -> bool:
#         try:
#             # 비동기 실행을 위해 ThreadPoolExecutor 사용
#             loop = asyncio.get_event_loop()
#             return await loop.run_in_executor(None, self._check_captions_available_sync, video_id)
#         except Exception as e:
#             logger.error(f"자막 확인 중 오류 발생: {e}")
#             return False
#
#     def _check_captions_available_sync(self, video_id: str) -> bool:
#         try:
#             transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
#             # 한국어 자막 우선 확인, 없으면 영어 자막 확인
#             try:
#                 transcript_list.find_transcript(["ko"])
#                 logger.info(f"한국어 자막이 있는 영상입니다 - (video_id: {video_id})")
#                 return True
#             except:
#                 try:
#                     transcript_list.find_transcript(["en"])
#                     logger.info(f"영어 자막이 있는 영상입니다 - (video_id: {video_id})")
#                     return True
#                 except:
#                     logger.info(f"자막을 지원하지 않는 영상입니다 - (video_id: {video_id})")
#                     return False
#         except:
#             logger.info(f"자막을 지원하지 않는 영상입니다 - (video_id: {video_id})")
#             return False
#
#     # 영상에 대한 url을 받아서 video id를 추출
#     def extract_video_id(self, url: str) -> Optional[str]:
#         try:
#             parsed_url = urlparse(url)
#             video_id = None
#
#             if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
#                 if parsed_url.path == "/watch":
#                     video_id = parse_qs(parsed_url.query)["v"][0]
#             elif parsed_url.hostname == "youtu.be":
#                 video_id = parsed_url.path[1:]
#
#             if video_id:
#                 logger.info(f"추출된 비디오 ID: {video_id}")
#                 return video_id
#             else:
#                 logger.warning(f"비디오 ID를 추출할 수 없는 URL 형식입니다: {url}")
#                 return None
#
#         except Exception as e:
#             logger.error(f"비디오 ID 추출 중 오류 발생: {e}")
#             return None
#
#     # 자막 추출 (영상 정보(id, title, description, url) -> 자막 텍스트)
#     async def get_video_transcripts(self, video_info: Dict) -> str:
#         try:
#             # 비동기 실행을 위해 ThreadPoolExecutor 사용
#             loop = asyncio.get_event_loop()
#             return await loop.run_in_executor(None, self._get_video_transcripts_sync, video_info)
#         except Exception as e:
#             logger.error(f"자막 추출 중 오류 발생: {e}")
#             return ""
#
#     def _get_video_transcripts_sync(self, video_info: Dict) -> str:
#         try:
#             # video_id 키가 있으면 그것을 사용하고, 없으면 id 키를 사용
#             video_id = video_info.get("video_id", video_info.get("id"))
#
#             # id가 딕셔너리인 경우 (YouTube API 응답 형식)
#             if isinstance(video_id, dict) and "videoId" in video_id:
#                 video_id = video_id["videoId"]
#
#             if not video_id:
#                 logger.error("비디오 ID를 찾을 수 없습니다.")
#                 return ""
#
#             transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
#
#             # 한국어 자막 우선 시도, 없으면 영어 자막 시도
#             try:
#                 transcript = transcript_list.find_transcript(["ko"])
#                 logger.info("한국어 자막을 사용합니다.")
#             except:
#                 try:
#                     transcript = transcript_list.find_transcript(["en"])
#                     logger.info("영어 자막을 사용합니다.")
#                 except:
#                     logger.error("사용 가능한 자막이 없습니다.")
#                     return ""
#
#             if transcript:
#                 transcript_pieces = transcript.fetch()
#                 full_transcript = " ".join([piece["text"] for piece in transcript_pieces])
#
#                 # 영상 제목과 설명 추출
#                 title = video_info.get("title", video_info.get("video_title", ""))
#                 description = video_info.get("description", "")
#
#                 # snippet 키가 있는 경우 (YouTube API 응답 형식)
#                 if "snippet" in video_info:
#                     title = title or video_info["snippet"].get("title", "")
#                     description = description or video_info["snippet"].get("description", "")
#
#                 # 영상 제목과 설명도 포함
#                 full_text = f"제목: {title}\n설명: {description}\n내용: {full_transcript}"
#                 logger.info(f"영상정보:\n{full_text[:200]}...\n")
#                 logger.info(f"자막:\n{full_transcript[:200]}...")
#                 return full_transcript
#
#         except Exception as e:
#             logger.error(f"자막 추출 중 오류 발생 (비디오 ID: {video_id}): {e}")
#             return ""
#
#     async def get_most_relevant_content(self, situation: str, force_refresh: bool = False) -> dict:
#         """
#         쿼리와 가장 유사도가 높은 영상의 자막 정보만 추출합니다.
#
#         Args:
#             situation: 검색 쿼리
#             force_refresh: 강제 갱신 여부
#
#         Returns:
#             가장 유사도가 높은 영상의 자막 정보를 담은 딕셔너리
#         """
#         try:
#             # 1st. 강제 옵션 확인
#             if force_refresh or self._contains_refresh_keywords(situation):
#                 logger.info("강제 갱신 또는 최신 정보 키워드 감지 - 유튜브에서 새로 검색합니다.")
#                 await self._search_and_update(situation, max_contents=3)
#
#             # 2nd. 벡터 DB에서 가장 유사한 자막 정보 검색
#             logger.info(f"벡터 DB에서 '{situation}'와 가장 유사한 자막 정보 검색 중..")
#             most_relevant = await self.vector_store.get_most_relevant_transcript(situation)
#
#             if not most_relevant:
#                 logger.warning("유사한 자막 정보를 찾지 못했습니다. 유튜브 검색을 시작합니다.")
#                 await self._search_and_update(situation, max_contents=3)
#                 most_relevant = await self.vector_store.get_most_relevant_transcript(situation)
#
#             if not most_relevant:
#                 return {"source": "no_results", "video_title": "", "video_url": "", "transcript": "", "similarity": 0.0}
#
#             logger.info(f"가장 유사한 자막 정보를 찾았습니다. (유사도: {most_relevant.get('similarity', 0.0):.2f})")
#             return {"source": "vector_db", **most_relevant}
#
#         except Exception as e:
#             logger.error(f"가장 유사한 자막 정보 검색 중 오류 발생: {e}")
#             return {
#                 "source": "error",
#                 "video_title": "",
#                 "video_url": "",
#                 "transcript": "",
#                 "similarity": 0.0,
#                 "error": str(e),
#             }
#
#
# async def main():
#     # 서비스 초기화
#     video_service = VideoSearchService()
#
#     # 상황 예시
#     situation = "면접 관련 꿀팁"
#     print(f"검색어: '{situation}'로 관련 영상 검색 중...")
#
#     # 관련 자막 정보 가져오기 (강제 갱신 옵션 활성화)
#     result = await video_service.get_or_fetch_relevant_content(situation, force_refresh=True)
#
#     print("\n===== 검색 결과 =====")
#     print(f"소스: {result['source']}")
#
#     if result["source"] == "error":
#         print(f"오류: {result.get('error', '알 수 없는 오류')}")
#     elif result["source"] == "no_transcripts":
#         print("자막이 있는 영상을 찾지 못했습니다.")
#     else:
#         print(f"포맷된 텍스트:\n{result['formatted_text']}")
#
#     # 가장 유사한 자막 정보 가져오기
#     print("\n===== 가장 유사한 자막 정보 =====")
#     most_relevant = await video_service.get_most_relevant_content(situation)
#
#     if most_relevant["source"] == "error":
#         print(f"오류: {most_relevant.get('error', '알 수 없는 오류')}")
#     elif most_relevant["source"] == "no_results":
#         print("유사한 자막 정보를 찾지 못했습니다.")
#     else:
#         print(f"영상 제목: {most_relevant['video_title']}")
#         print(f"영상 URL: {most_relevant['video_url']}")
#         print(f"유사도: {most_relevant.get('similarity', 0.0):.2f}")
#         print(f"자막 내용 (일부):\n{most_relevant['transcript'][:300]}...")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
