import os
import json
import requests
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv
import re

load_dotenv()  # .env 파일 로드

def deduplicate_sentences(text):
    text = text.strip()
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    dedup_lines = []
    for line in lines:
        if not dedup_lines or dedup_lines[-1] != line:
            dedup_lines.append(line)
    new_text = "\n".join(dedup_lines)
    
    if len(new_text) > 0:
        half = len(new_text) // 2
        if len(new_text) % 2 == 0 and new_text[:half] == new_text[half:]:
            return new_text[:half].strip()
    
    return new_text

# 사용자 선택 글제안 ai(노션에 키값 추가했습니다다)
def clova_ai_glee(prompt):
    url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_glee")  

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    system_msg = "사용자가 선택하거나 입력한 내용을 보고 글을 제안해줘. 이때 출력은 오로지 너가 제안하는 문장만 출력해줘"
    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 256,
        "temperature": 0.5,
        "repeatPenalty": 5.0,
        "stopBefore": [],
        "includeAiFilters": True,
        "seed": 0
    }
    response = requests.post(url, headers=headers, json=payload, stream=True)
    if response.status_code == 200:
        result_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                try:
                    data_json = json.loads(data_str)
                    token = data_json.get("message", {}).get("content", "")
                    result_text += token
                except Exception:
                    continue
        result_text = deduplicate_sentences(result_text)
        return result_text
    else:
        return f"Error: {response.status_code} - {response.text}"

# 제목 지어주는 AI
def clova_ai_title_suggestions(input_text):
    # .env에서 불러오기
    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_TITLE")  

    suggestions = []
    system_msg = ("사용자가 입력한 내용에 맞는 제목을 작성해줘. 출력은 문장만 출력해줘")

    for _ in range(3):
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": input_text}
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 72,
            "temperature": 0.5,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": 0
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            title_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
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


# 잘 작동하는 지 간단히 테스트용..
####################################################################################
#####################################################################################
def update_custom_entry(combo, custom_entry):
    if combo.get() in ["직접 입력(사용자가 입력)", "직접 입력"]:
        custom_entry.grid()
    else:
        custom_entry.grid_remove()

def generate_suggestions():
    situation = situation_var.get()
    if situation == "직접 입력(사용자가 입력)":
        situation = situation_custom_entry.get()
    
    tone = tone_var.get()
    if tone == "직접 입력(사용자가 입력)":
        tone = tone_custom_entry.get()
    
    platform = platform_var.get()
    details = details_entry.get()
    
    prompt = (
        f"상황: {situation}\n"
        f"말투: {tone}\n"
        f"사용처: {platform}\n"
        f"추가 디테일: {details}"
    )
    
    for title_box, content_box in [(title_textbox1, suggestion_textbox1), 
                                   (title_textbox2, suggestion_textbox2), 
                                   (title_textbox3, suggestion_textbox3)]:
        title_box.config(state="normal")
        content_box.config(state="normal")
        title_box.delete(1.0, tk.END)
        content_box.delete(1.0, tk.END)
        title_box.insert(tk.END, "제목 생성 중입니다...")
        content_box.insert(tk.END, "내용 생성 중입니다...")
        title_box.config(state="disabled")
        content_box.config(state="disabled")
    
    # 제안 1
    suggestion1 = clova_ai_glee(prompt)
    title_list1 = clova_ai_title_suggestions(suggestion1)
    title1 = title_list1[0] if title_list1 else "제목 없음"
    
    # 제안 2
    suggestion2 = clova_ai_glee(prompt)
    title_list2 = clova_ai_title_suggestions(suggestion2)
    title2 = title_list2[0] if title_list2 else "제목 없음"
    
    # 제안 3
    suggestion3 = clova_ai_glee(prompt)
    title_list3 = clova_ai_title_suggestions(suggestion3)
    title3 = title_list3[0] if title_list3 else "제목 없음"
    
    title_textbox1.config(state="normal")
    suggestion_textbox1.config(state="normal")
    title_textbox2.config(state="normal")
    suggestion_textbox2.config(state="normal")
    title_textbox3.config(state="normal")
    suggestion_textbox3.config(state="normal")
    
    title_textbox1.delete(1.0, tk.END)
    suggestion_textbox1.delete(1.0, tk.END)
    title_textbox2.delete(1.0, tk.END)
    suggestion_textbox2.delete(1.0, tk.END)
    title_textbox3.delete(1.0, tk.END)
    suggestion_textbox3.delete(1.0, tk.END)
    
    title_textbox1.insert(tk.END, title1)
    suggestion_textbox1.insert(tk.END, suggestion1)
    
    title_textbox2.insert(tk.END, title2)
    suggestion_textbox2.insert(tk.END, suggestion2)
    
    title_textbox3.insert(tk.END, title3)
    suggestion_textbox3.insert(tk.END, suggestion3)
    
    title_textbox1.config(state="disabled")
    suggestion_textbox1.config(state="disabled")
    title_textbox2.config(state="disabled")
    suggestion_textbox2.config(state="disabled")
    title_textbox3.config(state="disabled")
    suggestion_textbox3.config(state="disabled")

# 메인 창 
root = tk.Tk()
root.title("글 제안 GUI")
root.geometry("550x800")
root.resizable(False, False)

# Depth 1: 상황 선택
situation_label = ttk.Label(root, text="상황을 선택해주세요")
situation_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

situation_var = tk.StringVar()
situation_options = [
    "업무를 보고할게요",
    "안부를 묻고 싶어요",
    "부탁을 거절하고 싶어요",
    "감사 인사를 전할게요",
    "진심이 담긴 사과를 하고 싶어요",
    "직접 입력(사용자가 입력)"
]
situation_combo = ttk.Combobox(root, textvariable=situation_var, values=situation_options, state="readonly")
situation_combo.current(0)
situation_combo.grid(row=0, column=1, padx=10, pady=10)

situation_custom_entry = ttk.Entry(root)
situation_custom_entry.grid(row=1, column=1, padx=10, pady=5)
situation_custom_entry.grid_remove()
situation_combo.bind("<<ComboboxSelected>>", lambda event: update_custom_entry(situation_combo, situation_custom_entry))

# Depth 2: 말투 선택
tone_label = ttk.Label(root, text="말투를 선택해주세요")
tone_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

tone_var = tk.StringVar()
tone_options = [
    "친구에게 말하듯 친근하게",
    "예의바르고 정중하게",
    "공적인 사이, 프로페셔널하게",
    "애교있고 센스있게",
    "직접 입력(사용자가 입력)"
]
tone_combo = ttk.Combobox(root, textvariable=tone_var, values=tone_options, state="readonly")
tone_combo.current(0)
tone_combo.grid(row=2, column=1, padx=10, pady=10)

tone_custom_entry = ttk.Entry(root)
tone_custom_entry.grid(row=3, column=1, padx=10, pady=5)
tone_custom_entry.grid_remove()
tone_combo.bind("<<ComboboxSelected>>", lambda event: update_custom_entry(tone_combo, tone_custom_entry))

# Depth 3: 글 사용처 선택
platform_label = ttk.Label(root, text="어디에 쓰이는 글인가요?")
platform_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")

platform_var = tk.StringVar()
platform_options = ["카카오톡", "회사 메신저", "메일", "인스타그램", "블로그"]
platform_combo = ttk.Combobox(root, textvariable=platform_var, values=platform_options, state="readonly")
platform_combo.current(0)
platform_combo.grid(row=4, column=1, padx=10, pady=10)

# Depth 4: 추가 디테일
details_label = ttk.Label(root, text="추가로 필요한 디테일")
details_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")

details_entry = ttk.Entry(root)
details_entry.grid(row=5, column=1, padx=10, pady=10)

# Depth 5: 글 제안 생성 및 결과 출력
generate_button = ttk.Button(root, text="제안받기(다시가능)", command=generate_suggestions)
generate_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

# 결과
# 제안 1 
sug1_label = ttk.Label(root, text="글 제안 1")
sug1_label.grid(row=7, column=0, padx=10, pady=(5,0), sticky="w")
title_textbox1 = tk.Text(root, height=2, width=60, state="disabled", bg="#f0f0f0")
title_textbox1.grid(row=8, column=0, columnspan=2, padx=10, pady=(0,5))
suggestion_textbox1 = tk.Text(root, height=6, width=60, state="disabled")
suggestion_textbox1.grid(row=9, column=0, columnspan=2, padx=10, pady=(0,10))

# 제안 2 
sug2_label = ttk.Label(root, text="글 제안 2")
sug2_label.grid(row=10, column=0, padx=10, pady=(5,0), sticky="w")
title_textbox2 = tk.Text(root, height=2, width=60, state="disabled", bg="#f0f0f0")
title_textbox2.grid(row=11, column=0, columnspan=2, padx=10, pady=(0,5))
suggestion_textbox2 = tk.Text(root, height=6, width=60, state="disabled")
suggestion_textbox2.grid(row=12, column=0, columnspan=2, padx=10, pady=(0,10))

# 제안 3 
sug3_label = ttk.Label(root, text="글 제안 3")
sug3_label.grid(row=13, column=0, padx=10, pady=(5,0), sticky="w")
title_textbox3 = tk.Text(root, height=2, width=60, state="disabled", bg="#f0f0f0")
title_textbox3.grid(row=14, column=0, columnspan=2, padx=10, pady=(0,5))
suggestion_textbox3 = tk.Text(root, height=6, width=60, state="disabled")
suggestion_textbox3.grid(row=15, column=0, columnspan=2, padx=10, pady=(0,10))

root.mainloop()