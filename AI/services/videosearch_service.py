import os
from typing import Optional, Dict
from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs


class VideoSearchService:
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        # YouTube API 클라이언트 초기화
        self.youtube = build("youtube", "v3", developerKey=self.youtube_api_key)
        self.next_page_token = None  # 클래스 변수로 선언

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
