import sys
import os

from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from AI.services.Generation.reply_seggestion import ReplySuggestion
from AI.services.OCR.clova_ocr import ClovaOcr
from AI.services.Analysis.analyze_situation import Analyze
from AI.services.Generation.title_suggestion import TitleSuggestion
from AI.services.videosearch_service import VideoSearchService

"""
직접 출력 테스트
"""
test_image_files = ["./AI/OCR_Test1.png", "./AI/OCR_Test2.png", "./AI/OCR_Test3.png", "./AI/OCR_Test4.png"]
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
ocr_service = ClovaOcr()
video_search_service = VideoSearchService()


# # [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
# def analyze_situation(image_files: list[str]) -> str:
#     # 이미지 파일들을 읽어서 튜플 리스트로 변환
#     image2text = ocr_service.CLOVA_OCR(image_files)
#     situation = situation_service.situation_summary(image2text)
#     return situation

# analyze_situation(test_image_files)

# # -------------------------------------------------------------------
# # [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
# def analyze_situation_accent_purpose(image_files: list[tuple[str, bytes]]) -> tuple[str, str, str]:
#     image_tuples = []
#     for file_path in image_files:
#         with open(file_path, 'rb') as f:
#             image_data = f.read()
#             image_tuples.append((file_path, image_data))

#     image2text = CLOVA_OCR(image_tuples)
#     situation = situation_service.situation_summary(image2text)
#     accent, purpose = situation_service.style_analysis(image2text)
#     return situation, accent, purpose
# analyze_situation_accent_purpose(test_image_files)


# # -------------------------------------------------------------------
# # [3] [1]의 상황을 기반으로 글 제안을 생성하는 함수
# def generate_suggestions_situation(situation: str) -> tuple[list[str], list[str]]:
#     suggestions = reply_service.generate_basic_reply(situation)
#     title = title_service._generate_title_suggestions(situation)
#     return suggestions, title
# situation = situation_service.situation_summary(CLOVA_OCR(test_image_files))
# generate_suggestions_situation(situation)

# # -------------------------------------------------------------------
# # [4] [2]의 상황, 말투, 용도를 기반으로 글 제안을 생성하는 함수
# def generate_reply_suggestions_accent_purpose(situation: str, accent: str, purpose: str) -> tuple[list[str], list[str]]:
#     suggestions = reply_service.generate_detailed_reply(situation, accent, purpose)
#     title = title_service._generate_title_suggestions(situation)
#     return suggestions, title
# situation = situation_service.situation_summary(CLOVA_OCR(test_image_files))
# generate_reply_suggestions_accent_purpose(situation, "귀엽고 사랑스러운 말투", "카카오톡")

# # -------------------------------------------------------------------
# # [5] 상황, 말투, 용도, 상세 설명을 기반으로 글 제안을 생성하는 함수
# def generate_reply_suggestions_detail(
#     situation: str, accent: str, purpose: str, detailed_description: str
# ) -> tuple[list[str], list[str]]:
#     suggestions = reply_service.generate_detailed_reply(situation, accent, purpose, detailed_description)
#     title = title_service._generate_title_suggestions(situation)
#     return suggestions, title
# situation = situation_service.situation_summary(CLOVA_OCR(test_image_files))
# generate_reply_suggestions_detail(situation, "귀엽고 사랑스러운 말투", "카카오톡", "친구들과 함께 카카오톡을 사용하는 경우")

"""
youtube 영상 검색 테스트
"""
# 로거 설정
logger.add("logs/app.log", rotation="500 MB")

# # test1: URL로 비디오 ID 추출 테스트
# # test2: 해당 영상이 자막 정보를 제공하는지 여부 확인 동작 테스트
# test_url = "https://www.youtube.com/watch?v=P9qmSnsyFS0"
# video_id = video_search_service.extract_video_id(test_url)
# captions_available = video_search_service.check_captions_available(video_id)
# logger.info(f"추출된 비디오 ID: {video_id}")
# logger.info(f"자막 유무 정보: {captions_available}")

# test3: 검색 쿼리로 영상 검색 테스트
# test4: 영상에 대한 자막 텍스트 추출 테스트
test_query = "랄로"
video_info = video_search_service.youtube_search(test_query)
video_caption = video_search_service.get_video_transcripts(video_info)


# 검색어(쿼리)를 받아서 관련 영상 정보(id, title, description, url)를 반환
    # description은 영상 설명란에 있는 설명
    def youtube_search(self, query: str, max_results: int = 50, page_token: str = None) -> Dict:
        try:
            # API 키 확인
            if not self.youtube_api_key:
                logger.error("YouTube API 키가 설정되지 않았습니다.")
                return {}

            # 검색어 확인
            if not query.strip():
                logger.error("검색어가 비어있습니다.")
                return {}

            while True:  # 유효한 결과를 찾을 때까지 계속 검색
                # YouTube 검색 수행
                search_response = (
                    self.youtube.search()
                    .list(
                        q=query,
                        part="id,snippet",
                        maxResults=max_results,
                        type="video",
                        relevanceLanguage="ko",
                        safeSearch="none",
                        pageToken=page_token,
                    )
                    .execute()
                )

                # 검색 결과 처리
                for item in search_response.get("items", []):
                    try:
                        if item["id"]["kind"] == "youtube#video":
                            video_info = {
                                "id": item["id"]["videoId"],
                                "title": item["snippet"]["title"],
                                "description": item["snippet"]["description"],
                                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                            }

                            if all(video_info.values()):
                                logger.info(f"검색 결과: {video_info}")
                                return video_info
                            else:
                                logger.debug("검색 결과값이 불완전합니다. 다음 영상을 참조합니다.")
                                continue
                    except Exception as e:
                        logger.error(f"영상 정보 추출 중 누락된 필드가 있습니다. 다음 영상을 참조합니다.: {e}")
                        continue

                # 다음 페이지 토큰이 있는지 확인
                page_token = search_response.get("nextPageToken")
                if not page_token:
                    logger.warning("더 이상 검색할 결과가 없습니다.")
                    break
                logger.info(f"다음 페이지 검색을 시작합니다. (page_token: {page_token})")

            return {}

        except Exception as e:
            logger.error(f"YouTube 검색 중 오류 발생: {e}")
            return {}

    def check_captions_available(self, video_id: str) -> bool:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # 한국어 자막 우선 확인, 없으면 영어 자막 확인
            try:
                transcript_list.find_transcript(["ko"])
                logger.info(f"한국어 자막이 있는 영상입니다 - (video_id: {video_id})")
                return True
            except:
                try:
                    transcript_list.find_transcript(["en"])
                    logger.info(f"영어 자막이 있는 영상입니다 - (video_id: {video_id})")
                    return True
                except:
                    logger.info(f"자막을 지원하지 않는 영상입니다 - (video_id: {video_id})")
                    return False
        except:
            logger.info(f"자막을 지원하지 않는 영상입니다 - (video_id: {video_id})")
            return False

    # 영상에 대한 url을 받아서 video id를 추출
    def extract_video_id(self, url: str) -> Optional[str]:
        try:
            parsed_url = urlparse(url)
            video_id = None

            if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
                if parsed_url.path == "/watch":
                    video_id = parse_qs(parsed_url.query)["v"][0]
            elif parsed_url.hostname == "youtu.be":
                video_id = parsed_url.path[1:]

            if video_id:
                logger.info(f"추출된 비디오 ID: {video_id}")
                return video_id
            else:
                logger.warning(f"비디오 ID를 추출할 수 없는 URL 형식입니다: {url}")
                return None

        except Exception as e:
            logger.error(f"비디오 ID 추출 중 오류 발생: {e}")
            return None

    # 자막 추출 (영상 정보(id, title, description, url) -> 자막 텍스트)
    def get_video_transcripts(self, video_info: Dict) -> str:
        try:
            video_id = video_info["id"]
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 한국어 자막 우선 시도, 없으면 영어 자막 시도
            try:
                transcript = transcript_list.find_transcript(["ko"])
                logger.info("한국어 자막을 사용합니다.")
            except:
                try:
                    transcript = transcript_list.find_transcript(["en"])
                    logger.info("영어 자막을 사용합니다.")
                except:
                    logger.error("사용 가능한 자막이 없습니다.")
                    return ""

            if transcript:
                transcript_pieces = transcript.fetch()
                full_transcript = " ".join([piece["text"] for piece in transcript_pieces])

                # 영상 제목과 설명도 포함
                full_text = f"제목: {video_info['title']}\n설명: {video_info['description']}\n내용: {full_transcript}"
                logger.info(f"영상정보:\n{full_text}\n")
                logger.info(f"자막:\n{full_transcript}")
                return full_transcript

        except Exception as e:
            logger.error(f"자막 추출 중 오류 발생 (비디오 ID: {video_info['id']}): {e}")
            return ""