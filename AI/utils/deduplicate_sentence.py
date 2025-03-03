# 중복되는 문장 제거
def deduplicate_sentences(text: str) -> str:
    """
    문자열에서 중복되는 문장을 제거합니다.
    1. 문자열 전체가 두 번 반복되는 경우
    2. 개별 문장이 반복되는 경우
    """
    if not text:
        return text

    text = text.strip()

    # 1. 전체 문자열이 두 번 반복되는 경우 처리
    half_len = len(text) // 2
    if len(text) % 2 == 0 and text[:half_len] == text[half_len:]:
        return text[:half_len].strip()

    # 2. 개별 문장이 반복되는 경우 처리
    # 마침표, 물음표, 느낌표로 문장 구분
    sentences = []
    current_sentence = ""

    for char in text:
        current_sentence += char
        if char in [".", "?", "!"]:
            current_sentence = current_sentence.strip()
            if current_sentence and (not sentences or current_sentence != sentences[-1]):
                sentences.append(current_sentence)
            current_sentence = ""

    # 마지막 문장 처리
    if current_sentence.strip() and (not sentences or current_sentence.strip() != sentences[-1]):
        sentences.append(current_sentence.strip())

    return " ".join(sentences)
