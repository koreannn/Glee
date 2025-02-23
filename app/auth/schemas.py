from pydantic import BaseModel, HttpUrl


class KakaoAuthUrl(BaseModel):
    url: HttpUrl  # URL은 Pydantic의 HttpUrl 타입으로 검증
