from fastapi import HTTPException


class ApiError(HTTPException):
    """Error body is always {"detail": {"code": ..., "message": ...}}: `code` for the UI to branch on,
    `message` (Vietnamese) to show to the user."""

    def __init__(self, status_code: int, code: str, message: str, headers: dict | None = None):
        super().__init__(status_code, detail={"code": code, "message": message}, headers=headers)


def unauthorized(message: str = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn") -> ApiError:
    return ApiError(401, "UNAUTHORIZED", message, headers={"WWW-Authenticate": "Bearer"})


def forbidden(message: str = "Bạn không có quyền thực hiện thao tác này") -> ApiError:
    return ApiError(403, "FORBIDDEN", message)


def not_found(entity: str = "Dữ liệu") -> ApiError:
    return ApiError(404, "NOT_FOUND", f"{entity} không tồn tại")


def version_conflict() -> ApiError:
    return ApiError(409, "VERSION_CONFLICT", "Dữ liệu đã bị người khác thay đổi, vui lòng tải lại")
