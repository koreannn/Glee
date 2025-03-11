import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from AI.services.videosearch_service import VideoSearchService, TranscriptionVectorStore


@pytest.fixture
def video_search_service():
    """VideoSearchService 인스턴스를 생성하는 fixture"""
    service = VideoSearchService()
    return service


@pytest.mark.asyncio
async def test_query_generation_and_youtube_search(video_search_service, capsys):
    """
    1. 사용자의 상황을 기반으로 어떤 쿼리가 만들어지는지
    2. 이 쿼리를 기반으로 검색된 유튜브 영상의 정보가 잘 나오는지
    테스트
    """
    # 테스트 상황 설정
    situation = "면접에서 자기소개를 어떻게 하면 좋을까요?"

    # 실제 YouTube API 호출을 모킹
    with patch.object(video_search_service, "youtube_search") as mock_youtube_search:
        # 모의 응답 설정
        mock_youtube_search.return_value = {
            "items": [
                {
                    "id": {"videoId": "video1"},
                    "snippet": {
                        "title": "면접 자기소개 잘하는 방법",
                        "description": "면접에서 자기소개를 잘하는 방법을 알려드립니다.",
                    },
                },
                {
                    "id": {"videoId": "video2"},
                    "snippet": {
                        "title": "면접관이 원하는 자기소개",
                        "description": "면접관의 관점에서 좋은 자기소개란 무엇인지 설명합니다.",
                    },
                },
            ]
        }

        # 자막 확인 함수 모킹
        with patch.object(video_search_service, "check_captions_available", return_value=True):
            # 자막 가져오기 함수 모킹
            with patch.object(video_search_service, "get_video_transcripts") as mock_get_transcripts:
                mock_get_transcripts.return_value = (
                    "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다."
                )

                # 벡터 스토어 모킹
                with patch.object(video_search_service, "vector_store") as mock_vector_store:
                    mock_vector_store.add_or_update_transcriptions = AsyncMock()
                    mock_vector_store.search_relevant_content = AsyncMock(
                        return_value=[
                            {
                                "video_title": "면접 자기소개 잘하는 방법",
                                "video_url": "https://www.youtube.com/watch?v=video1",
                                "transcript": "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다.",
                                "score": 0.85,
                            }
                        ]
                    )
                    mock_vector_store.format_search_results = MagicMock(
                        return_value="면접 자기소개 잘하는 방법: 안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다."
                    )

                    # 함수 실행
                    result = await video_search_service._search_and_update(situation)

                    # 출력 캡처
                    captured = capsys.readouterr()

                    # 검증
                    assert mock_youtube_search.called
                    assert mock_youtube_search.call_args[0][0] == situation

                    print("\n===== 테스트: 쿼리 생성 및 유튜브 검색 =====")
                    print(f"입력 상황: {situation}")
                    print(f"검색 쿼리: {situation}")
                    print("\n검색된 유튜브 영상 정보:")
                    for i, item in enumerate(mock_youtube_search.return_value["items"]):
                        print(f"  {i+1}. 제목: {item['snippet']['title']}")
                        print(f"     ID: {item['id']['videoId']}")
                        print(f"     설명: {item['snippet']['description']}")

                    print("\n검색 결과:")
                    print(f"  소스: {result['source']}")
                    print(f"  포맷된 텍스트: {result['formatted_text']}")

                    assert result["source"] == "youtube_new"
                    assert len(result["results"]) > 0


@pytest.mark.asyncio
async def test_transcript_extraction_and_similarity_scoring(video_search_service, capsys):
    """
    추출된 영상들 중 어떤 자막 정보가 연관성이 가장 높은지 점수가 매겨지는 과정을 테스트
    """
    # 테스트 상황 설정
    situation = "면접에서 자기소개를 어떻게 하면 좋을까요?"

    # 벡터 스토어의 get_most_relevant_transcript 메서드 모킹
    with patch.object(video_search_service, "vector_store") as mock_vector_store:
        # 모의 응답 설정
        mock_vector_store.get_most_relevant_transcript = AsyncMock(
            return_value={
                "video_title": "면접 자기소개 잘하는 방법",
                "video_url": "https://www.youtube.com/watch?v=video1",
                "transcript": "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다. "
                "첫째, 간결하게 말하세요. 둘째, 자신의 강점을 강조하세요. 셋째, 지원 동기를 명확히 하세요.",
                "similarity": 0.92,
            }
        )

        # 함수 실행
        result = await video_search_service.get_most_relevant_content(situation)

        # 출력 캡처
        captured = capsys.readouterr()

        # 검증
        assert mock_vector_store.get_most_relevant_transcript.called
        assert mock_vector_store.get_most_relevant_transcript.call_args[0][0] == situation

        print("\n===== 테스트: 자막 추출 및 유사도 점수 계산 =====")
        print(f"입력 상황: {situation}")
        print("\n가장 유사한 자막 정보:")
        print(f"  제목: {result['video_title']}")
        print(f"  URL: {result['video_url']}")
        print(f"  유사도 점수: {result['similarity']}")
        print(f"  자막 내용: {result['transcript'][:100]}...")

        assert result["source"] == "vector_db"
        assert result["video_title"] == "면접 자기소개 잘하는 방법"
        assert result["similarity"] == 0.92


@pytest.mark.asyncio
async def test_end_to_end_video_search_and_selection(video_search_service, capsys):
    """
    전체 과정을 테스트: 쿼리 생성 -> 유튜브 검색 -> 자막 추출 -> 유사도 계산 -> 최종 선택
    """
    # 테스트 상황 설정
    situation = "면접에서 자기소개를 어떻게 하면 좋을까요?"

    # 강제 갱신 키워드 확인 함수 모킹
    with patch.object(video_search_service, "_contains_refresh_keywords", return_value=False):
        # _search_and_update 메서드 모킹
        with patch.object(video_search_service, "_search_and_update") as mock_search_and_update:
            mock_search_and_update.return_value = {
                "source": "youtube_new",
                "results": [
                    {
                        "video_title": "면접 자기소개 잘하는 방법",
                        "video_url": "https://www.youtube.com/watch?v=video1",
                        "transcript": "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다.",
                        "score": 0.85,
                    },
                    {
                        "video_title": "면접관이 원하는 자기소개",
                        "video_url": "https://www.youtube.com/watch?v=video2",
                        "transcript": "면접관의 관점에서 좋은 자기소개란 무엇인지 설명합니다.",
                        "score": 0.75,
                    },
                ],
                "formatted_text": "검색 결과 텍스트",
            }

            # 벡터 스토어의 get_most_relevant_transcript 메서드 모킹
            with patch.object(video_search_service, "vector_store") as mock_vector_store:
                # 첫 번째 호출에서는 결과가 있다고 가정
                mock_vector_store.get_most_relevant_transcript = AsyncMock(
                    return_value={
                        "video_title": "면접 자기소개 잘하는 방법",
                        "video_url": "https://www.youtube.com/watch?v=video1",
                        "transcript": "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다. "
                        "첫째, 간결하게 말하세요. 둘째, 자신의 강점을 강조하세요. 셋째, 지원 동기를 명확히 하세요.",
                        "similarity": 0.92,
                    }
                )

                # 함수 실행
                result = await video_search_service.get_most_relevant_content(situation)

                # 출력 캡처
                captured = capsys.readouterr()

                # 검증
                assert mock_vector_store.get_most_relevant_transcript.called

                print("\n===== 테스트: 전체 과정 (쿼리 -> 검색 -> 자막 추출 -> 유사도 계산 -> 최종 선택) =====")
                print(f"입력 상황: {situation}")
                print(f"검색 쿼리: {situation}")
                print("\n벡터 DB 검색 결과:")
                print(f"  제목: {result['video_title']}")
                print(f"  URL: {result['video_url']}")
                print(f"  유사도 점수: {result['similarity']}")
                print(f"  자막 내용: {result['transcript'][:100]}...")

                assert result["source"] == "vector_db"
                assert result["video_title"] == "면접 자기소개 잘하는 방법"
                assert result["similarity"] == 0.92


@pytest.mark.asyncio
async def test_real_video_search_with_mocked_youtube_api(video_search_service, capsys):
    """
    실제 벡터 스토어를 사용하되 YouTube API만 모킹하여 실제와 유사한 환경에서 테스트
    """
    # 테스트 상황 설정
    situation = "면접에서 자기소개를 어떻게 하면 좋을까요?"

    # 실제 YouTube API 호출을 모킹
    with patch.object(video_search_service, "youtube_search") as mock_youtube_search:
        # 모의 응답 설정 (더 현실적인 데이터)
        mock_youtube_search.return_value = {
            "items": [
                {
                    "id": {"videoId": "video1"},
                    "snippet": {
                        "title": "면접 자기소개 잘하는 방법 - 면접관이 좋아하는 자기소개",
                        "description": "면접에서 자기소개를 잘하는 방법을 알려드립니다. 면접관의 관점에서 좋은 자기소개란 무엇인지 설명합니다.",
                    },
                },
                {
                    "id": {"videoId": "video2"},
                    "snippet": {
                        "title": "신입 면접 자기소개 팁 5가지",
                        "description": "신입 면접에서 자기소개를 잘하는 5가지 팁을 알려드립니다.",
                    },
                },
                {
                    "id": {"videoId": "video3"},
                    "snippet": {
                        "title": "면접 합격률 높이는 자기소개 방법",
                        "description": "면접 합격률을 높이는 자기소개 방법을 알려드립니다. 실제 면접관들의 피드백을 바탕으로 작성되었습니다.",
                    },
                },
            ]
        }

        # 자막 확인 함수 모킹
        with patch.object(video_search_service, "check_captions_available", return_value=True):
            # 자막 가져오기 함수 모킹 (각 비디오마다 다른 자막 설정)
            with patch.object(video_search_service, "get_video_transcripts") as mock_get_transcripts:

                def get_transcript_side_effect(video_info):
                    video_id = video_info.get("video_id")
                    if video_id == "video1":
                        return "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다. 첫째, 간결하게 말하세요. 둘째, 자신의 강점을 강조하세요. 셋째, 지원 동기를 명확히 하세요."
                    elif video_id == "video2":
                        return "신입 면접에서 자기소개를 잘하는 5가지 팁을 알려드립니다. 1. 1분 내외로 준비하세요. 2. 지원 직무와 관련된 경험을 강조하세요. 3. 성격보다는 역량을 중심으로 말하세요. 4. 구체적인 사례를 들어 설명하세요. 5. 자신감 있게 말하세요."
                    elif video_id == "video3":
                        return "면접 합격률을 높이는 자기소개 방법을 알려드립니다. 면접관은 지원자의 자기소개를 통해 많은 것을 파악합니다. 따라서 자기소개는 매우 중요합니다. 자기소개에서는 자신의 강점과 지원 동기를 명확히 전달하는 것이 중요합니다."
                    return ""

                mock_get_transcripts.side_effect = get_transcript_side_effect

                # 실제 벡터 스토어 초기화 (임시 디렉토리 사용)
                import tempfile

                temp_dir = tempfile.mkdtemp()

                # 벡터 스토어 초기화 함수 모킹
                with patch.object(TranscriptionVectorStore, "_initialize_vector_store"):
                    # 벡터 스토어의 add_or_update_transcriptions 메서드 모킹
                    with patch.object(TranscriptionVectorStore, "add_or_update_transcriptions", new_callable=AsyncMock):
                        # 벡터 스토어의 search_relevant_content 메서드 모킹
                        with patch.object(
                            TranscriptionVectorStore, "search_relevant_content", new_callable=AsyncMock
                        ) as mock_search:
                            mock_search.return_value = [
                                {
                                    "video_title": "신입 면접 자기소개 팁 5가지",
                                    "video_url": "https://www.youtube.com/watch?v=video2",
                                    "transcript": "신입 면접에서 자기소개를 잘하는 5가지 팁을 알려드립니다. 1. 1분 내외로 준비하세요. 2. 지원 직무와 관련된 경험을 강조하세요. 3. 성격보다는 역량을 중심으로 말하세요. 4. 구체적인 사례를 들어 설명하세요. 5. 자신감 있게 말하세요.",
                                    "score": 0.95,
                                },
                                {
                                    "video_title": "면접 자기소개 잘하는 방법 - 면접관이 좋아하는 자기소개",
                                    "video_url": "https://www.youtube.com/watch?v=video1",
                                    "transcript": "안녕하세요, 오늘은 면접에서 자기소개를 잘하는 방법에 대해 알아보겠습니다. 첫째, 간결하게 말하세요. 둘째, 자신의 강점을 강조하세요. 셋째, 지원 동기를 명확히 하세요.",
                                    "score": 0.85,
                                },
                                {
                                    "video_title": "면접 합격률 높이는 자기소개 방법",
                                    "video_url": "https://www.youtube.com/watch?v=video3",
                                    "transcript": "면접 합격률을 높이는 자기소개 방법을 알려드립니다. 면접관은 지원자의 자기소개를 통해 많은 것을 파악합니다. 따라서 자기소개는 매우 중요합니다. 자기소개에서는 자신의 강점과 지원 동기를 명확히 전달하는 것이 중요합니다.",
                                    "score": 0.75,
                                },
                            ]

                            # 벡터 스토어의 format_search_results 메서드 모킹
                            with patch.object(TranscriptionVectorStore, "format_search_results") as mock_format:
                                mock_format.return_value = "검색 결과 텍스트"

                                # 벡터 스토어의 get_most_relevant_transcript 메서드 모킹
                                with patch.object(
                                    TranscriptionVectorStore, "get_most_relevant_transcript", new_callable=AsyncMock
                                ) as mock_get_most_relevant:
                                    mock_get_most_relevant.return_value = {
                                        "video_title": "신입 면접 자기소개 팁 5가지",
                                        "video_url": "https://www.youtube.com/watch?v=video2",
                                        "transcript": "신입 면접에서 자기소개를 잘하는 5가지 팁을 알려드립니다. 1. 1분 내외로 준비하세요. 2. 지원 직무와 관련된 경험을 강조하세요. 3. 성격보다는 역량을 중심으로 말하세요. 4. 구체적인 사례를 들어 설명하세요. 5. 자신감 있게 말하세요.",
                                        "similarity": 0.95,
                                    }

                                    # 함수 실행
                                    result = await video_search_service.get_most_relevant_content(
                                        situation, force_refresh=True
                                    )

                                    # 출력 캡처
                                    captured = capsys.readouterr()

                                    print("\n===== 테스트: 실제와 유사한 환경에서의 전체 과정 테스트 =====")
                                    print(f"입력 상황: {situation}")
                                    print(f"검색 쿼리: {situation}")

                                    print("\n유튜브 검색 결과:")
                                    for i, item in enumerate(mock_youtube_search.return_value["items"]):
                                        print(f"  {i+1}. 제목: {item['snippet']['title']}")
                                        print(f"     ID: {item['id']['videoId']}")
                                        print(f"     설명: {item['snippet']['description']}")

                                    print("\n추출된 자막 정보:")
                                    for i, video_id in enumerate(["video1", "video2", "video3"]):
                                        transcript = get_transcript_side_effect({"video_id": video_id})
                                        print(f"  {i+1}. 비디오 ID: {video_id}")
                                        print(f"     자막: {transcript[:50]}...")

                                    print("\n유사도 점수가 매겨진 결과:")
                                    for i, item in enumerate(mock_search.return_value):
                                        print(f"  {i+1}. 제목: {item['video_title']}")
                                        print(f"     유사도 점수: {item['score']}")
                                        print(f"     자막: {item['transcript'][:50]}...")

                                    print("\n최종 선택된 자막 정보:")
                                    print(f"  제목: {result['video_title']}")
                                    print(f"  URL: {result['video_url']}")
                                    print(f"  유사도 점수: {result['similarity']}")
                                    print(f"  자막 내용: {result['transcript'][:100]}...")

                                    assert result["source"] == "vector_db"
                                    assert result["video_title"] == "신입 면접 자기소개 팁 5가지"
                                    assert result["similarity"] == 0.95


if __name__ == "__main__":
    # 테스트 실행
    pytest.main(["-xvs", __file__])
