from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mode: str = "dev"
    secret_key: str
    kakao_client_id: str
    kakao_client_secret: str
    kakao_redirect_uri: str
    kakao_rest_api_key: str
    kakao_logout_redirect_uri: str
    db_name: str
    mongo_uri: str

    CLOVA_OCR_URL: str
    CLOVA_OCR_SECRET_KEY: str
    CLOVA_AI_BEARER_TOKEN: str
    CLOVA_REQ_ID_REPLY_SUMMARY: str
    CLOVA_REQ_ID_TITLE: str
    CLOVA_REQ_ID_OLD_REPLY: str
    CLOVA_REQ_ID_NEW_REPLY: str
    CLOVA_REQ_ID_STYLE: str
    CLOVA_REQ_ID_glee: str

    test_jwt_token: str | None = None

    # 추가해야 할 필드들
    host: str
    api_key: str
    api_key_primary_val: str
    request_id: str
    youtube_api_key: str


# 설정을 불러옵니다.
settings = Settings()
