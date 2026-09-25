from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm.exc import StaleDataError

from app.api.v1 import auth, cinemas, users
from app.core.config import settings
from app.core.deps import DbSession
from app.core.errors import version_conflict

class UTF8JSONResponse(JSONResponse):
    # Explicit charset: some clients (e.g. Windows PowerShell 5.1) otherwise decode as Latin-1
    # and garble Vietnamese text.
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    default_response_class=UTF8JSONResponse,
    swagger_ui_parameters={"persistAuthorization": True},  # keep the token across page reloads
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StaleDataError)
def stale_data_handler(_: Request, __: StaleDataError) -> JSONResponse:
    # Raised by SQLAlchemy when row_version changed between our SELECT and UPDATE.
    err = version_conflict()
    return UTF8JSONResponse(status_code=err.status_code, content={"detail": err.detail})


API_V1 = "/api/v1"
app.include_router(auth.router, prefix=API_V1)
app.include_router(users.router, prefix=API_V1)
app.include_router(cinemas.router, prefix=API_V1)


@app.get("/health", tags=["system"])
def health(db: DbSession):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
