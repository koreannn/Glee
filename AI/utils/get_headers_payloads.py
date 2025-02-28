import json
import os
import sys
import yaml
from typing import Optional, Union, Dict, Any

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from dotenv import load_dotenv
from app.core.settings import settings

load_dotenv()

def load_config(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def get_headers_payloads(config_path: Union[str, Dict[str, Any]], conversation: Optional[str] = None):
    # config_path가 문자열이면 파일에서 로드, 딕셔너리면 그대로 사용
    if isinstance(config_path, str):
        config = load_config(config_path)
    else:
        config = config_path
    
    BEARER_TOKEN = os.getenv("CLOVA_AI_BEARER_TOKEN")
    REQUEST_ID = os.getenv("CLOVA_REQ_ID_REPLY_SUMMARY")

    if not BEARER_TOKEN or not REQUEST_ID:
        BEARER_TOKEN = settings.CLOVA_AI_BEARER_TOKEN
        REQUEST_ID = settings.CLOVA_REQ_ID_REPLY_SUMMARY
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    
    # conversation이 None이 아닐 때만 messages에 user content 추가
    messages = [{"role": "system", "content": config["SYSTEM_PROMPT"]}]
    if conversation is not None:
        messages.append({"role": "user", "content": conversation})
    
    payload = {
        # "messages": [{"role": "system", "content": config["SYSTEM_PROMPT"]}, {"role": "user", "content": conversation}],
        "messages": messages,
        "topP": config["HYPER_PARAM"]["topP"],
        "topK": config["HYPER_PARAM"]["topK"],
        "maxTokens": config["HYPER_PARAM"]["maxTokens"],
        "temperature": config["HYPER_PARAM"]["temperature"],
        "repeatPenalty": config["HYPER_PARAM"]["repeatPenalty"],
        "stopBefore": config["HYPER_PARAM"]["stopBefore"],
        "includeAiFilters": config["HYPER_PARAM"]["includeAiFilters"],
        "seed": config["HYPER_PARAM"]["seed"],
    }
    
    return headers, payload