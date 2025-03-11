# 아나콘다 환경 설정 방법

## 방법 1: environment.yml 파일 사용

```bash
# 환경 생성 및 패키지 설치 (기본 위치에 설치)
conda env create -f environment.yml

# 또는 특정 경로에 설치 (권장)
conda env create -f environment.yml --prefix $HOME/.conda/envs/dap-dap-back

# 환경 활성화 (기본 위치에 설치한 경우)
conda activate dap-dap-back

# 환경 활성화 (특정 경로에 설치한 경우)
conda activate $HOME/.conda/envs/dap-dap-back
```

## 방법 2: 스크립트 실행

```bash
# 스크립트 실행 권한 부여
chmod +x conda_setup.sh

# 스크립트 실행
./conda_setup.sh

# 환경 활성화
conda activate $HOME/.conda/envs/dap-dap-back
```

## 방법 3: 수동 설치

```bash
# 환경 경로 설정
ENV_PATH="$HOME/.conda/envs/dap-dap-back"

# 환경 생성 (특정 경로에 설치)
conda create --prefix $ENV_PATH python=3.11 -y

# 환경 활성화
conda activate $ENV_PATH

# conda 패키지 설치
conda install --prefix $ENV_PATH -c conda-forge fastapi=0.115 uvicorn=0.34 black=25.1 mypy=1.15 pytest=8.3 httpx=0.28 itsdangerous=2.2 requests=2.32 pillow=11.1 -y

# pip 패키지 설치
pip install "ruff>=0.9.7,<0.10.0" "pytest-asyncio>=0.25.3,<0.26.0" "pydantic-settings>=2.8.0,<3.0.0" "python-multipart>=0.0.20,<0.0.21" "motor>=3.7.0,<4.0.0" "pyjwt[crypto]>=2.10.1,<3.0.0" "loguru>=0.7.3,<0.8.0" "langchain-community>=0.3.19,<0.4.0" "youtube-transcript-api>=0.6.3,<0.7.0" "google-api-python-client>=2.162.0,<3.0.0" "pre-commit>=4.1.0"
```

## 권한 오류 해결 방법

아나콘다 환경 생성 시 다음과 같은 권한 오류가 발생할 수 있습니다:

```
NotWritableError: The current user does not have write permissions to a required path.
  path: /Users/[사용자명]/anaconda3/bin/conda/.conda_envs_dir_test
```

### 해결 방법 1: 권한 수정

아나콘다 디렉토리의 소유권을 현재 사용자로 변경합니다:

```bash
# 아나콘다 디렉토리 권한 수정 (macOS/Linux)
sudo chown -R $(whoami) ~/anaconda3

# 또는 오류 메시지에 나온 특정 경로만 수정
sudo chown $(whoami):$(id -g) /Users/[사용자명]/anaconda3/bin/conda/.conda_envs_dir_test
```

### 해결 방법 2: 사용자 환경에 설치

`--user` 옵션을 사용하여 사용자 환경에 설치합니다:

```bash
# 환경 생성 시 사용자 환경에 설치
conda env create -f environment.yml --user
```

### 해결 방법 3: 환경 위치 지정 (권장)

환경을 생성할 때 사용자가 쓰기 권한을 가진 디렉토리를 지정합니다:

```bash
# 환경 위치를 지정하여 생성 (--prefix 옵션 사용)
ENV_PATH="$HOME/.conda/envs/dap-dap-back"
conda env create -f environment.yml --prefix $ENV_PATH

# 또는 다른 경로 지정
conda env create -f environment.yml --prefix ~/my_conda_envs/dap-dap-back
```

이 경우 환경 활성화는 다음과 같이 합니다:
```bash
# 환경 활성화 (전체 경로 지정)
conda activate $HOME/.conda/envs/dap-dap-back

# 또는 다른 경로를 지정한 경우
conda activate ~/my_conda_envs/dap-dap-back
``` 