## case5 : 상황, 말투, 용도, 상세 설명 → 글 제안 생성
import os
import requests
import json

from utils.deduplicate_sentence import deduplicate_sentences

# 사용자 설정 글 제안 AI
def clova_ai_glee(prompt: str) -> str:

    url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_glee")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    system_msg = "사용자가 선택하거나 입력한 내용을 보고 글을 제안해줘"
    payload = {
        "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 256,
        "temperature": 0.5,
        "repeatPenalty": 5.0,
        "stopBefore": [],
        "includeAiFilters": True,
        "seed": 0,
    }

    response = requests.post(url, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:") :].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")
                    result_text += token
                except Exception:
                    continue
        return deduplicate_sentences(result_text)
    else:
        return f"Error: {response.status_code} - {response.text}"


# 제목 생성 AI
def clova_ai_title_suggestions(input_text: str) -> list:

    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_TITLE")

    suggestions = []
    system_msg = (
        "사용자가 입력한 내용에 맞는 제목과 부연 설명을 작성해줘. "
        "제목은 '제목:'으로, 내용은 '내용:'으로 시작하도록 해줘."
    )

    for _ in range(3):
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": input_text}],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 72,
            "temperature": 0.5,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": 0,
        }

        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            title_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        title_text += token
                    except Exception:
                        continue
            title_text = deduplicate_sentences(title_text)
            suggestions.append(title_text)
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
    return suggestions


# ai case 5, 호출할 함수
def case_5(situation: str, tone: str, platform: str, details: str) -> str:

    prompt = f"상황: {situation}\n" f"말투: {tone}\n" f"사용처: {platform}\n" f"추가 디테일: {details}"

    # 3가지 글 제안
    proposal1 = clova_ai_glee(prompt)
    proposal2 = clova_ai_glee(prompt)
    proposal3 = clova_ai_glee(prompt)

    # 각 제안에 대해 제목 생성
    title_list1 = clova_ai_title_suggestions(proposal1)
    title1 = title_list1[0] if title_list1 else "제목 없음"

    title_list2 = clova_ai_title_suggestions(proposal2)
    title2 = title_list2[0] if title_list2 else "제목 없음"

    title_list3 = clova_ai_title_suggestions(proposal3)
    title3 = title_list3[0] if title_list3 else "제목 없음"

    # 결과
    result = (
        f"글 제안 1:\n제목: {title1}\n내용: {proposal1}\n\n"
        f"글 제안 2:\n제목: {title2}\n내용: {proposal2}\n\n"
        f"글 제안 3:\n제목: {title3}\n내용: {proposal3}"
    )

    return result
