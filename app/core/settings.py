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


# 설정을 불러옵니다.
settings = Settings()
