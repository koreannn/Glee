FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y build-essential curl

# Poetry 설치 (공식 설치 스크립트 사용)
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# 의존성 파일 복사 (poetry.lock 파일은 없을 경우에도 작동하도록 *)
COPY pyproject.toml poetry.lock* /app/

# Poetry 설정: 가상환경을 만들지 않고 전역에 설치
RUN poetry install --no-root

# 애플리케이션 코드 복사
COPY . /app

# 애플리케이션이 사용하는 포트 노출 (필요에 따라 수정)
EXPOSE 8000

# 컨테이너 시작 시 애플리케이션 실행 (app.py 예시)
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]