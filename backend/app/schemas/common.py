import re
from typing import Annotated, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

T = TypeVar("T")


def _check_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
    if len(value.encode()) > 72:  # bcrypt hard limit
        raise ValueError("Mật khẩu quá dài (tối đa 72 byte)")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("Mật khẩu phải có cả chữ và số")
    return value


Password = Annotated[str, AfterValidator(_check_password)]
Phone = Annotated[str, Field(pattern=r"^\+?\d{9,15}$")]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
