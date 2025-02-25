import tkinter as tk
from tkinter import filedialog, messagebox
import os
import requests
import uuid
import time
import json
import random
from dotenv import load_dotenv
import re

load_dotenv()  # .env 파일 로드


# 중복되는 문장 제거..
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

# -------------------------------------------------------------------
# 1) CLOVA OCR 호출 함수
def clova_ocr(image_path):
    # (2) .env에서 불러오기
    url = os.getenv("CLOVA_OCR_URL")
    secret_key = os.getenv("CLOVA_OCR_SECRET_KEY")

    headers = {"X-OCR-SECRET": secret_key}
    request_json = {
        "images": [{"format": "jpg", "name": "demo"}],
        "requestId": str(uuid.uuid4()),
        "version": "V2",
        "timestamp": int(round(time.time() * 1000))
    }
    payload = {"message": json.dumps(request_json).encode("UTF-8")}
    files = [("file", open(image_path, "rb"))]
    response = requests.post(url, headers=headers, data=payload, files=files)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"


# -------------------------------------------------------------------
# 2) 답장 모드: 상황 요약
def clova_ai_reply_summary(prompt):
    # (2) .env에서 불러오기
    url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_REPLY_SUMMARY")  

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "사용자가 입력한 내용을 보고 상황을 요약해줘."},
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

# -------------------------------------------------------------------
# 3) 제목 지어주는 AI
def clova_ai_title_suggestions(input_text):
    # (2) .env에서 불러오기
    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_TITLE")  

    suggestions = []
    system_msg = ("사용자가 입력한 내용에 맞는 제목과 부연 설명을 작성해줘. "
                  "제목은 '제목:'으로, 내용은 '내용:'으로 시작하도록 해줘.")

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
            suggestions.append(title_text)
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
    return suggestions

# -------------------------------------------------------------------
# 4) 사진에 대한 답장 AI
def clova_ai_reply_suggestions(situation_text):
    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_OLD_REPLY")  

    suggestions = []
    system_msg = (
        "사용자가 입력한 내용은 지금 사용자가 처한 상황이야.\n"
        "해당 상황에서 사용자가 상대방에게 어떻게 답장하면 좋을지 작성해줘.\n"
        "이때 답장 부분만 출력해줘."
    )
    for _ in range(3):
        seed = random.randint(0, 10000)
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": situation_text}
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 256,
            "temperature": 0.5,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": seed
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            reply_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        reply_text += token
                    except Exception:
                        continue
            
            reply_text = deduplicate_sentences(reply_text)
            suggestions.append(reply_text)
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
    return suggestions

# -------------------------------------------------------------------
# 5) 이런 느낌으로 써주는 답장 AI
def clova_ai_new_reply_suggestions(situation_text):
    base_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_NEW_REPLY") 

    suggestions = []
    system_msg = (
        "사용자가 입력한 내용을 바탕으로 어떤 답변을 하면 좋을지 작성해줘.\n"
        "이때 답변 부분만 출력해줘."
    )
    for _ in range(3):
        seed = random.randint(0, 10000)
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": situation_text}
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 256,
            "temperature": 0.5,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": seed
        }
        response = requests.post(base_url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            reply_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get("message", {}).get("content", "")
                        reply_text += token
                    except Exception:
                        continue
            
            reply_text = deduplicate_sentences(reply_text)
            suggestions.append(reply_text)
        else:
            suggestions.append(f"Error: {response.status_code} - {response.text}")
    return suggestions
# -------------------------------------------------------------------
# 6) 상황 말투 용도  AI
def clova_ai_style_analysis(prompt):
    url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
    request_id = os.getenv("CLOVA_REQ_ID_STYLE")  

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    system_msg = ("사용자가 입력한 내용을 보고 상황, 말투, 용도를 출력해줘. "
                  "출력 형식은 '상황: ...', '말투: ...', '용도: ...'로 해줘.")
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

# -------------------------------------------------------------------
# 7) 상황 말투 용도 분석 결과 파싱 함수
def parse_style_analysis(result):
    situation, tone, usage = "", "", ""
    lines = result.splitlines()
    for line in lines:
        if line.strip().startswith("상황"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                situation = parts[1].strip()
        elif line.strip().startswith("말투"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                tone = parts[1].strip()
        elif line.strip().startswith("용도"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                usage = parts[1].strip()
    return situation, tone, usage

# -------------------------------------------------------------------
# 8) 제목/내용 파싱 함수 
def parse_suggestion(suggestion):
    title = ""
    content = ""
    lines = suggestion.splitlines()
    for line in lines:
        if line.strip().startswith("제목"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                title = parts[1].strip()
        elif line.strip().startswith("내용"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                content = parts[1].strip()
    if not title:
        title = suggestion.strip()
    return title, content


# -------------------------------------------------------------------
# 9) GUI Application 클래스
MAX_IMAGES = 4
MAX_REGENERATE = 3

class ClovaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CLOVA OCR & AI GUI")
        self.geometry("900x700")
        
        # 데이터 저장
        self.mode = None
        self.selected_images = []
        self.ocr_texts = []
        self.ai_result = ""            # 상황말투용도/답장 등에서 받은 결과
        self.title_suggestions = []    # 제목 3개
        self.reply_suggestions = []    # 답장 3개
        self.regenerate_count = 0

        # 상황,말투,용도 에서 추출한 값
        self.situation_style = ""
        self.tone_style = ""
        self.usage_style = ""

        # Depth4에서 상황말투용도(스타일)도 결과 수정하는 Text
        self.text_style_edit = None

        self.create_frames()

    def create_frames(self):
        # Depth 1
        self.frame_depth1 = tk.LabelFrame(self, text="Depth 1: 선택", padx=10, pady=10)
        self.frame_depth1.pack(fill="x", padx=10, pady=5)
        btn_situation = tk.Button(self.frame_depth1, text="상황을 직접 선택할게요", command=self.choose_situation_mode)
        btn_situation.pack(side="left", padx=5, pady=5)
        btn_photo = tk.Button(self.frame_depth1, text="사진을 첨부할게요", command=self.choose_photo_mode)
        btn_photo.pack(side="left", padx=5, pady=5)
        
        # Depth 2
        self.frame_depth2 = tk.LabelFrame(self, text="Depth 2: 입력", padx=10, pady=10)
        # Photo mode
        self.frame_photo_input = tk.Frame(self.frame_depth2)
        btn_add = tk.Button(self.frame_photo_input, text="사진 추가하기", command=self.add_photos)
        btn_add.pack(side="left", padx=5, pady=5)
        self.listbox_photos = tk.Listbox(self.frame_photo_input, width=40)
        self.listbox_photos.pack(side="left", padx=5, pady=5)
        #btn_ocr = tk.Button(self.frame_photo_input, text="OCR 실행하기", command=self.run_ocr)
        #btn_ocr.pack(side="left", padx=5, pady=5)
        #self.text_ocr = tk.Text(self.frame_photo_input, height=8, width=40)
        #self.text_ocr.pack(side="left", padx=5, pady=5)
        self.frame_photo_input.pack_forget() 

        # Situation mode
        self.frame_situation_input = tk.Frame(self.frame_depth2)
        lbl_situation = tk.Label(self.frame_situation_input, text="상황을 입력하세요:")
        lbl_situation.pack(side="top", padx=5, pady=5)
        self.text_situation = tk.Text(self.frame_situation_input, height=8, width=60)
        self.text_situation.pack(side="top", padx=5, pady=5)
        #self.btn_next_depth2 = tk.Button(self.frame_depth2, text="다음", command=self.go_to_depth3)
        #self.btn_next_depth2.pack(side="bottom", padx=5, pady=5)
        self.frame_situation_input.pack_forget()
        self.btn_next_depth2 = tk.Button(self.frame_depth2, text="다음", command=self.go_to_depth3)
        self.btn_next_depth2.pack(side="bottom", padx=5, pady=5)

        # Depth 3
        self.frame_depth3 = tk.LabelFrame(self, text="Depth 3: 스타일 선택", padx=10, pady=10)
        btn_reply = tk.Button(self.frame_depth3, text="이 사진에 대한 답장이 필요해요", 
                              command=lambda: self.run_ai_analysis("reply"))
        btn_reply.pack(side="left", padx=5, pady=5)
        btn_style = tk.Button(self.frame_depth3, text="이런 느낌으로 써주세요", 
                              command=lambda: self.run_ai_analysis("style"))
        btn_style.pack(side="left", padx=5, pady=5)
        
        # Depth 4
        self.frame_depth4 = tk.LabelFrame(self, text="Depth 4: 결과", padx=10, pady=10)
        self.text_ai = tk.Text(self.frame_depth4, height=8, width=70)
        self.text_ai.pack(side="top", padx=5, pady=5)

        # [스타일 모드 전용] - 수정 Text + "글 제안받기" 버튼
        self.text_style_edit = tk.Text(self.frame_depth4, height=6, width=70)
        # (처음엔 숨긴 상태, 스타일 모드일 때만 보이도록)
        self.btn_get_text_suggestions = tk.Button(self.frame_depth4, text="글 제안받기", command=self.go_to_depth5)

        # [답장 모드 전용] - 제목/답장 표시 + 재생성 버튼
        self.frame_title_suggestions = tk.LabelFrame(self.frame_depth4, text="제목 제안", padx=5, pady=5)
        self.frame_reply_suggestions = tk.LabelFrame(self.frame_depth4, text="답장 제안", padx=5, pady=5)
        self.btn_regen = tk.Button(self.frame_depth4, text="다른 제안보기", command=self.regenerate_titles)

        # Depth 5 (스타일 모드 → 글 제안 결과)
        self.frame_depth5 = tk.LabelFrame(self, text="Depth 5: 글 제안 결과", padx=10, pady=10)
        self.frame_title_suggestions2 = tk.LabelFrame(self.frame_depth5, text="제목 제안 (3개)")
        self.frame_title_suggestions2.pack(side="top", fill="x", padx=5, pady=5)
        self.frame_reply_suggestions2 = tk.LabelFrame(self.frame_depth5, text="답변 제안 (3개)")
        self.frame_reply_suggestions2.pack(side="top", fill="x", padx=5, pady=5)
        self.btn_regen2 = tk.Button(self.frame_depth5, text="다른 제안보기", command=self.regenerate_titles_style_mode)
        self.btn_regen2.pack(side="top", padx=5, pady=5)

    # -------------------------------------------------------------
    # 모드 선택
    def choose_photo_mode(self):
        self.mode = "photo"
        self.frame_depth1.pack_forget()
        self.frame_depth2.pack(fill="x", padx=10, pady=5)
        self.frame_photo_input.pack(fill="x")
        self.frame_situation_input.pack_forget()
    
    def choose_situation_mode(self):
        self.mode = "situation"
        self.frame_depth1.pack_forget()
        self.frame_depth2.pack(fill="x", padx=10, pady=5)
        self.frame_situation_input.pack(fill="x")
        self.frame_photo_input.pack_forget()

    # -------------------------------------------------------------
    # 사진 추가 / OCR
    def add_photos(self):
        files = filedialog.askopenfilenames(title="사진 선택", 
                                            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if files:
            if len(self.selected_images) + len(files) > MAX_IMAGES:
                messagebox.showwarning("경고", f"최대 {MAX_IMAGES}장까지 첨부할 수 있습니다.")
                return
            for f in files:
                self.selected_images.append(f)
                self.listbox_photos.insert(tk.END, os.path.basename(f))

    def run_ocr(self):

        if not self.selected_images:
            messagebox.showwarning("경고", "먼저 사진을 첨부해주세요.")
            return

        self.ocr_texts = []
        for img_path in self.selected_images:
            result = clova_ocr(img_path)
            if isinstance(result, dict):
                texts = []
                try:
                    for field in result['images'][0]['fields']:
                        texts.append(field.get('inferText', ''))
                except (KeyError, IndexError):
                    texts.append("OCR 결과 오류")
                result_text = "\n".join(texts)
            else:
                result_text = str(result)

            self.ocr_texts.append(result_text)

    # -------------------------------------------------------------
    # Depth2 → Depth3
    def go_to_depth3(self):

        if self.mode == "photo":
            if not self.selected_images:
                messagebox.showwarning("경고", "사진을 첨부해주세요.")
                return
            # '다음' 버튼 누르면 자동으로 OCR 실행
            self.run_ocr()
        else:  # situation
            text = self.text_situation.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("경고", "상황을 입력해주세요.")
                return

        self.frame_depth2.pack_forget()
        self.frame_depth3.pack(fill="x", padx=10, pady=5)

    # -------------------------------------------------------------
    # Depth3
    def run_ai_analysis(self, style):
        # 입력 텍스트 준비
        if self.mode == "photo":
            prompt_text = "\n".join(self.ocr_texts)
        else:
            prompt_text = self.text_situation.get("1.0", tk.END).strip()
        
        # 모든 프레임 초기화
        self.frame_depth3.pack_forget()
        # Depth4 보여주기
        self.frame_depth4.pack(fill="x", padx=10, pady=5)
        self.text_ai.delete("1.0", tk.END)
        # 숨겨진 위젯 초기화
        self.text_style_edit.pack_forget()
        self.btn_get_text_suggestions.pack_forget()
        self.frame_title_suggestions.pack_forget()
        self.frame_reply_suggestions.pack_forget()
        self.btn_regen.pack_forget()

        if style == "reply":
            # 1) 상황 요약
            if self.mode == "photo":
                prompt = "이 사진에 대한 답장: " + prompt_text
            else:
                prompt = "이 상황에 대한 답장: " + prompt_text

            self.ai_result = clova_ai_reply_summary(prompt)

            # 2) 제목/답장 제안
            self.title_suggestions = clova_ai_title_suggestions(self.ai_result)
            self.reply_suggestions = clova_ai_reply_suggestions(self.ai_result)

            # 화면 표시
            self.text_ai.insert(tk.END, "[상황 요약]\n" + self.ai_result)
            # 제목/답장 영역 표시
            self.frame_title_suggestions.pack(side="top", fill="x", padx=5, pady=5)
            self.frame_reply_suggestions.pack(side="top", fill="x", padx=5, pady=5)
            self.btn_regen.pack(side="top", padx=5, pady=5)

            self.update_title_suggestions_display()
            self.update_reply_suggestions_display()

        elif style == "style":
            # 분석
            if self.mode == "photo":
                prompt = "이런 느낌: " + prompt_text
            else:
                prompt = "이런 느낌: " + prompt_text

            result = clova_ai_style_analysis(prompt)
            self.ai_result = result
            situation, tone, usage = parse_style_analysis(result)
            self.situation_style = situation
            self.tone_style = tone
            self.usage_style = usage

            # 결과 표시
            self.text_ai.insert(tk.END, f"상황: {situation}\n말투: {tone}\n용도: {usage}\n")
            # 수정창 표시
            self.text_style_edit.delete("1.0", tk.END)
            # 수정창에 기본값으로 AI가 준 결과를 넣어둠
            self.text_style_edit.insert(tk.END, result.strip())
            self.text_style_edit.pack(side="top", padx=5, pady=5)
            # "글 제안받기" 버튼
            self.btn_get_text_suggestions.pack(side="top", padx=5, pady=5)

    # -------------------------------------------------------------
    # Depth4 → Depth5(글 제안)
    def go_to_depth5(self):
        """
        사용자가 수정한 텍스트(스타일 분석 결과)를 기반으로
        
        3가지씩 호출
        """
        # 수정된 텍스트
        edited_text = self.text_style_edit.get("1.0", tk.END).strip()
        if not edited_text:
            messagebox.showwarning("경고", "스타일 내용을 수정/확인해주세요.")
            return

        # Depth4 숨기고 Depth5 표시
        self.frame_depth4.pack_forget()
        self.frame_depth5.pack(fill="x", padx=10, pady=5)

        # 제목 제안
        self.title_suggestions = clova_ai_title_suggestions(edited_text)
        # 새 답변 제안
        self.reply_suggestions = clova_ai_new_reply_suggestions(edited_text)

        self.update_title_suggestions_display2()
        self.update_reply_suggestions_display2()

    # -------------------------------------------------------------
    # Depth5(스타일 모드) 표시
    def update_title_suggestions_display2(self):
        for widget in self.frame_title_suggestions2.winfo_children():
            widget.destroy()
        for idx, suggestion in enumerate(self.title_suggestions):
            title, content = parse_suggestion(suggestion)
            subframe = tk.Frame(self.frame_title_suggestions2, borderwidth=1, relief="solid")
            subframe.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")
            label_title = tk.Label(subframe, text=title, font=("Arial", 12, "bold"), wraplength=200)
            label_title.pack(fill="x", padx=5, pady=5)
        for idx in range(3):
            self.frame_title_suggestions2.grid_columnconfigure(idx, weight=1)

    def update_reply_suggestions_display2(self):
        for widget in self.frame_reply_suggestions2.winfo_children():
            widget.destroy()
        for idx, suggestion in enumerate(self.reply_suggestions):
            title, content = parse_suggestion(suggestion)
            subframe = tk.Frame(self.frame_reply_suggestions2, borderwidth=1, relief="solid")
            subframe.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")
            
            reply_text = (title).strip()
            label_reply = tk.Label(subframe, text=reply_text, wraplength=200)
            label_reply.pack(fill="x", padx=5, pady=5)
        for idx in range(3):
            self.frame_reply_suggestions2.grid_columnconfigure(idx, weight=1)

    def regenerate_titles_style_mode(self):
        """
        Depth5에서 '다른 제안보기' (스타일 모드 전용)
        """
        if self.regenerate_count >= MAX_REGENERATE:
            messagebox.showinfo("정보", "더 이상 다른 제안을 생성할 수 없습니다.")
            return
        self.regenerate_count += 1

        # 현재 편집 텍스트로 다시 호출
        edited_text = self.text_style_edit.get("1.0", tk.END).strip()
        self.title_suggestions = clova_ai_title_suggestions(edited_text)
        self.reply_suggestions = clova_ai_new_reply_suggestions(edited_text)
        self.update_title_suggestions_display2()
        self.update_reply_suggestions_display2()

    # -------------------------------------------------------------
    # Depth4(답장 모드) 표시
    def update_title_suggestions_display(self):
        for widget in self.frame_title_suggestions.winfo_children():
            widget.destroy()
        for idx, suggestion in enumerate(self.title_suggestions):
            title, content = parse_suggestion(suggestion)
            subframe = tk.Frame(self.frame_title_suggestions, borderwidth=1, relief="solid")
            subframe.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")
            label_title = tk.Label(subframe, text=title, font=("Arial", 12, "bold"), wraplength=200)
            label_title.pack(fill="x", padx=5, pady=5)
        for idx in range(3):
            self.frame_title_suggestions.grid_columnconfigure(idx, weight=1)

    def update_reply_suggestions_display(self):
        for widget in self.frame_reply_suggestions.winfo_children():
            widget.destroy()
        for idx, suggestion in enumerate(self.reply_suggestions):
            title, content = parse_suggestion(suggestion)
            subframe = tk.Frame(self.frame_reply_suggestions, borderwidth=1, relief="solid")
            subframe.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")
            reply_text = (title).strip()
            label_reply = tk.Label(subframe, text=reply_text, wraplength=200)
            label_reply.pack(fill="x", padx=5, pady=5)
        for idx in range(3):
            self.frame_reply_suggestions.grid_columnconfigure(idx, weight=1)

    def regenerate_titles(self):
        """
        Depth4(답장 모드)에서 '다른 제안보기'
        """
        if self.regenerate_count >= MAX_REGENERATE:
            messagebox.showinfo("정보", "더 이상 다른 제안을 생성할 수 없습니다.")
            return
        self.regenerate_count += 1
        # 상황 요약 결과 self.ai_result를 바탕으로 다시 호출
        self.title_suggestions = clova_ai_title_suggestions(self.ai_result)
        self.reply_suggestions = clova_ai_reply_suggestions(self.ai_result)
        self.update_title_suggestions_display()
        self.update_reply_suggestions_display()

if __name__ == "__main__":
    app = ClovaApp()
    app.mainloop()
