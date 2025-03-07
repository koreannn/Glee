import os
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock

# # AI 모듈을 import할 수 있도록 경로 추가
# sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def mock_response():
    class MockResponse:
        def __init__(self, status_code=200, text=""):
            self.status_code = status_code
            self.text = text

        def json(self):
            return {"text": self.text}

    return MockResponse


@pytest.fixture
def sample_image_bytes():
    return b"fake image data"


@pytest.fixture
def mock_settings():
    return {
        "CLOVA_AI_BEARER_TOKEN": "test_token",
        "CLOVA_REQ_ID_REPLY_SUMMARY": "test_req_id",
        "youtube_api_key": "test_youtube_key",
    }
