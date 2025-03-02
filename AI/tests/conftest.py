import os
import sys
from pathlib import Path

# AI 모듈을 import할 수 있도록 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv() 