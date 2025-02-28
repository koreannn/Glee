import json

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    return config

def get_headers_payloads(config_path: str):
    config = load_config(config_path)
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "messages": [{"role": "system", "content": config["SYSTEM_PROMPT"]}, {"role": "user", "content": conversation}],
        "topP": config["HYPER_PARAM"]["topP"],
        "topK": config["HYPER_PARAM"]["topK"],
        "maxTokens": config["HYPER_PARAM"]["maxTokens"],
        "temperature": config["HYPER_PARAM"]["temperature"],
        "repeatPenalty": config["HYPER_PARAM"]["repeatPenalty"],
        "stopBefore": config["HYPER_PARAM"]["stopBefore"],
        "includeAiFilters": config["HYPER_PARAM"]["includeAiFilters"],
        "seed": config["HYPER_PARAM"]["seed"],
    }