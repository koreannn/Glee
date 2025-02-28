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
        lines = new_text.splitlines()
        half = len(lines) // 2
        if len(lines) % 2 == 0 and lines[:half] == lines[half:]:
            return "\n".join(lines[:half]).strip()

    return new_text
