from fastapi import HTTPException


class NotFoundException(HTTPException):
    """리소스를 찾을 수 없을 때 발생하는 예외 (404)"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class UnauthorizedException(HTTPException):
    """인증 실패 시 발생하는 예외 (401)"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)


class BadRequestException(HTTPException):
    """잘못된 요청 시 발생하는 예외 (400)"""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class ForbiddenException(HTTPException):
    """권한이 없을 때 발생하는 예외 (403)"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)
