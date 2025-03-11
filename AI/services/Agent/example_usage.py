import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(root_dir))

from AI.services.Agent.orchestrator_agent import OrchestratorAgent
from loguru import logger


async def example_reply_with_video_info():
    """
    자막 정보를 활용한 답변 생성 예제
    """
    try:
        agent = OrchestratorAgent()

        # 사용자 입력 예시
        user_input = "면접에서 자기소개를 어떻게 하면 좋을까요?"

        print(f"사용자 입력: {user_input}")
        print("=" * 50)

        # 자막 정보를 활용한 답변 생성
        result = await agent.run_reply_with_video_info(user_input)

        # 결과 출력
        print(f"상황 요약: {result['situation']}")
        print(f"참고 자료: {result.get('reference', {}).get('video_title', '없음')}")
        print(f"참고 URL: {result.get('reference', {}).get('video_url', '없음')}")
        print(f"유사도: {result.get('reference', {}).get('similarity', 0.0)}")
        print("\n제목 제안:")
        for i, title in enumerate(result["titles"], 1):
            print(f"{i}. {title}")

        print("\n답변 제안:")
        for i, reply in enumerate(result["replies"], 1):
            print(f"{i}. {reply}")

        print("=" * 50)
        return True
    except Exception as e:
        logger.error(f"자막 정보를 활용한 답변 생성 중 오류 발생: {e}")
        return False


async def example_style_with_video_info():
    """
    스타일 분석과 자막 정보를 활용한 답변 생성 예제
    """
    try:
        agent = OrchestratorAgent()

        # 사용자 입력 예시
        user_input = """
        면접에서 자기소개를 어떻게 하면 좋을지 알려주세요.
        저는 IT 회사에 지원하는 신입 개발자입니다.
        친절하고 전문적인 말투로 알려주세요.
        """

        print(f"사용자 입력: {user_input}")
        print("=" * 50)

        # 스타일 분석과 자막 정보를 활용한 답변 생성
        result = await agent.run_style_with_video_info(user_input)

        # 결과 출력
        print(f"상황: {result['situation']}")
        print(f"말투: {result['accent']}")
        print(f"용도: {result['purpose']}")
        print(f"스타일 분석: {result['style_analysis']}")
        print(f"참고 자료: {result.get('reference', {}).get('video_title', '없음')}")
        print(f"참고 URL: {result.get('reference', {}).get('video_url', '없음')}")
        print(f"유사도: {result.get('reference', {}).get('similarity', 0.0)}")

        print("\n제목 제안:")
        for i, title in enumerate(result["titles"], 1):
            print(f"{i}. {title}")

        print("\n답변 제안:")
        for i, reply in enumerate(result["replies"], 1):
            print(f"{i}. {reply}")

        print("=" * 50)
        return True
    except Exception as e:
        logger.error(f"스타일 분석과 자막 정보를 활용한 답변 생성 중 오류 발생: {e}")
        return False


async def example_manual_with_video_info():
    """
    수동 입력과 자막 정보를 활용한 답변 생성 예제
    """
    try:
        agent = OrchestratorAgent()

        # 수동 입력 예시
        situation = "면접에서 자기소개를 어떻게 하면 좋을지 알려주세요."
        accent = "친절하고 전문적인 말투"
        purpose = "면접 준비 조언"
        details = "IT 회사에 지원하는 신입 개발자입니다."

        print(f"상황: {situation}")
        print(f"말투: {accent}")
        print(f"용도: {purpose}")
        print(f"추가 설명: {details}")
        print("=" * 50)

        # 수동 입력과 자막 정보를 활용한 답변 생성
        result = await agent.run_manual_with_video_info(situation, accent, purpose, details)

        # 결과 출력
        print(f"참고 자료: {result.get('reference', {}).get('video_title', '없음')}")
        print(f"참고 URL: {result.get('reference', {}).get('video_url', '없음')}")
        print(f"유사도: {result.get('reference', {}).get('similarity', 0.0)}")

        print("\n제목 제안:")
        for i, title in enumerate(result["titles"], 1):
            print(f"{i}. {title}")

        print("\n답변 제안:")
        for i, reply in enumerate(result["replies"], 1):
            print(f"{i}. {reply}")

        print("=" * 50)
        return True
    except Exception as e:
        logger.error(f"수동 입력과 자막 정보를 활용한 답변 생성 중 오류 발생: {e}")
        return False


async def main():
    """
    예제를 하나씩 실행합니다.
    """
    print("1. 자막 정보를 활용한 답변 생성 예제")
    success1 = await example_reply_with_video_info()

    if success1:
        print("\n첫 번째 예제가 성공적으로 실행되었습니다.")
    else:
        print("\n첫 번째 예제 실행 중 오류가 발생했습니다.")

    print("\n2. 스타일 분석과 자막 정보를 활용한 답변 생성 예제")
    success2 = await example_style_with_video_info()

    if success2:
        print("\n두 번째 예제가 성공적으로 실행되었습니다.")
    else:
        print("\n두 번째 예제 실행 중 오류가 발생했습니다.")

    print("\n3. 수동 입력과 자막 정보를 활용한 답변 생성 예제")
    success3 = await example_manual_with_video_info()

    if success3:
        print("\n세 번째 예제가 성공적으로 실행되었습니다.")
    else:
        print("\n세 번째 예제 실행 중 오류가 발생했습니다.")


if __name__ == "__main__":
    asyncio.run(main())
