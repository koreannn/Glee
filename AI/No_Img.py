import json

from loguru import logger
import requests
import yaml


def load_config(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config


class CompletionExecutor:
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val
        self._request_id = request_id

    def execute(self, completion_request):
        headers = {
            "X-NCP-CLOVASTUDIO-API-KEY": self._api_key,
            "X-NCP-APIGW-API-KEY": self._api_key_primary_val,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self._request_id,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        }

        with requests.post(
            self._host + "/testapp/v1/chat-completions/HCX-003", headers=headers, json=completion_request, stream=True
        ) as r:

            if r.status_code != 200:
                logger.warning(f"API 요청 실패: 상태 코드 {r.status_code}")
                return None, r.status_code

            lines = [line.decode("utf-8") for line in r.iter_lines() if line]
            for line in lines[-4:]:
                try:
                    if line.startswith("data:"):
                        line = line[len("data:") :]
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", None)

                    if content:
                        return content

                except json.JSONDecodeError:
                    continue
        return None


def run_no_img():
    config = load_config("./config/config_No_Img.yaml")

    HOST = config["API"]["HOST"]
    API_KEY = config["API"]["API_KEY"]
    API_KEY_PRIMARY_VAL = config["API"]["API_KEY_PRIMARY_VAL"]
    REQUEST_ID = config["API"]["REQUEST_ID"]

    completion_executor = CompletionExecutor(
        host=f"{HOST}", api_key=f"{API_KEY}", api_key_primary_val=f"{API_KEY_PRIMARY_VAL}", request_id=f"{REQUEST_ID}"
    )

    step_1 = [
        "업무를 보고할게요",
        "안부를 묻고 싶어요",
        "부탁을 거절하고 싶어요",
        "감사 인사를 전할게요",
        "진심이 담긴 사과를 하고싶어요",
        "직접입력",
    ]
    step_2 = [
        "친구에게 말하듯 친근하게",
        "예의바르고 정중하게",
        "공적인 사이. 프로페셔널하게",
        "애교있고 센스있게",
        "직접입력",
    ]
    step_3 = ["카카오톡", "회사 메신저", "메일", "인스타그램 DM", "블로그"]
    step_4_ex = [
        "중학교 동창에게 10년만에 보내는연락",
        "이사님께 보고드려야하는 업무 현황. 이사님 심기에 불편할만한 워딩이나 표현은 사용하지 않을 것.",
        "교수님께 보내는 메일. 수강신청을 놓쳐서 추가 신쳥을 교수님께 요구드려야하는 상황",
    ]

    preset_text = [
        {
            "role": config["PROMPT"]["preset_text"]["system"]["role"],
            "content": config["PROMPT"]["preset_text"]["system"]["content"],
        },
        {
            "role": config["PROMPT"]["preset_text"]["user"]["role"],
            "content": f"상황: {step_1[0]}\n말투: {step_2[1]}\n사용되는곳: {step_3[2]}\n사용자가 추가적으로 원하는 요구사항:{step_4_ex[1]}",  # 사용자 입력
        },
    ]

    request_data = {
        "messages": preset_text,
        "topP": config["PARAMS"]["request_params"]["topP"],
        "topK": config["PARAMS"]["request_params"]["topK"],
        "maxTokens": config["PARAMS"]["request_params"]["maxTokens"],
        "temperature": config["PARAMS"]["request_params"]["temperature"],
        "repeatPenalty": config["PARAMS"]["request_params"]["repeatPenalty"],
        "stopBefore": config["PARAMS"]["request_params"]["stopBefore"],
        "includeAiFilters": config["PARAMS"]["request_params"]["includeAiFilters"],
        "seed": config["PARAMS"]["request_params"]["seed"],
    }
    executor = CompletionExecutor(
        host=HOST, api_key=API_KEY, api_key_primary_val=API_KEY_PRIMARY_VAL, request_id=REQUEST_ID
    )
    result = executor.execute(request_data)

    logger.info(f"생성된 답변:\n{result}")
    return result
