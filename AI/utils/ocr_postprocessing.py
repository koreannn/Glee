# 헬퍼 함수: OCR 결과 JSON에서 텍스트 추출
def extract_text_from_ocr_result(ocr_result):
    text_list = []
    if isinstance(ocr_result, dict) and "images" in ocr_result:
        for image in ocr_result["images"]:
            if "fields" in image:
                for field in image["fields"]:
                    text_list.append(field.get("inferText", ""))
    return " ".join(text_list)

# ----------------------------
# 이미지 전처리를 위한 클래스 
class ImagePreprocessor:
    def preprocess(self, image_bytes: bytes) -> bytes:
        try:
            with BytesIO(image_bytes) as stream:
                image = Image.open(stream)
                # 그레이스케일 변환 및 대비 보정
                image = ImageOps.grayscale(image)
                image = ImageOps.autocontrast(image)
                output_stream = BytesIO()
                image.save(output_stream, format="JPEG")
                return output_stream.getvalue()
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_bytes

# ----------------------------
# OCR 결과 캐싱 (같은 이미지에 대해 중복 호출 방지)
class OcrCache:
    def __init__(self):
        self.cache = {}

    def get_hash(self, filedata: bytes) -> str:
        return hashlib.md5(filedata).hexdigest()

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value: str):
        self.cache[key] = value

ocr_cache = OcrCache()

# ----------------------------
# OcrPostProcessingAgent (후처리 및 Clova AI 교정)
class OcrPostProcessingAgent:
    def __init__(self):
        self.clova_ai_url = os.getenv("https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003")
        self.bearer_token = os.getenv("CLOVA_AI_BEARER_TOKEN")
        self.request_id = os.getenv("CLOVA_REQ_ID_glee_agent")

    def run(self, ocr_text: str) -> str:
        # 기본 필터링: 중복 문장, 특수문자, 공백 정리
        cleaned_text = deduplicate_sentences(ocr_text)
        cleaned_text = re.sub(r'[^가-힣a-zA-Z0-9\s.,?!]', '', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        # Clova AI(문맥 수정) 호출
        corrected_text = self.correct_text(cleaned_text)
        return corrected_text

    def correct_text(self, text: str) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": "다음 텍스트에서 문맥에 맞게 자연스럽게 수정해줘. 불필요한 오류와 부자연스러운 부분을 고쳐줘."},
                {"role": "user", "content": text}
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 500,
            "temperature": 0.3,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": 0
        }
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        response = requests.post(self.clova_ai_url, headers=headers, json=payload, stream=True)
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
            return result_text.strip()
        else:
            logger.error(f"Clova AI 교정 에러: {response.status_code} - {response.text}")
            return text

# OcrAgent 
class OcrAgent:
    def __init__(self, max_retries=2):
        self.max_retries = max_retries
        self.post_processor = OcrPostProcessingAgent()
        self.preprocessor = ImagePreprocessor()

    def run(self, image_files: list[tuple[str, bytes]]) -> str:
        aggregated_text = []
        for (filename, filedata) in image_files:
            # 이미지 전처리 적용
            processed_bytes = self.preprocessor.preprocess(filedata)
            # 캐시 확인: 동일 이미지에 대한 OCR 결과 재사용
            file_hash = ocr_cache.get_hash(processed_bytes)
            cached_result = ocr_cache.get(file_hash)
            if cached_result:
                logger.info(f"Using cached OCR result for {filename}")
                aggregated_text.append(cached_result)
                continue

            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(processed_bytes)
                temp_file_path = temp_file.name
            try:
                retry = 0
                while retry <= self.max_retries:
                    ocr_result = CLOVA_OCR([(filename, processed_bytes)])
                    if isinstance(ocr_result, str) and ocr_result.startswith("Error"):
                        logger.error(ocr_result)
                        aggregated_text.append("")
                        break
                    extracted_text = extract_text_from_ocr_result(ocr_result)
                    if len(extracted_text.strip()) < 5 and retry < self.max_retries:
                        retry += 1
                        continue
                    else:
                        aggregated_text.append(extracted_text)
                        ocr_cache.set(file_hash, extracted_text)
                        break
            finally:
                os.remove(temp_file_path)
        raw_text = "\n".join(aggregated_text)
        processed_text = self.post_processor.run(raw_text)
        return processed_text
