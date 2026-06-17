from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.init_db import init_db
from app.core.exceptions import (
    PlayerNotFoundException,
    MatchNotFoundException,
    MatchAlreadyExistsException,
    PlayerAlreadyInQueueException,
    PlayerNotInQueueException
)
from app.routers.player_router import router as player_router
from app.routers.match_router import router as match_router
from app.routers.leaderboard_router import router as leaderboard_router
from app.routers.suspicious_player_router import router as suspicious_player_router
from app.routers.matchmaking_router import router as matchmaking_router


_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy"}



def _cors_response(request: Request, status_code: int, message: str) -> JSONResponse:
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in _ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=status_code,
        content={"message": message},
        headers=headers,
    )


@app.exception_handler(PlayerNotFoundException)
async def player_not_found(request: Request, exc: PlayerNotFoundException):
    return _cors_response(request, 404, str(exc))


@app.exception_handler(MatchNotFoundException)
async def match_not_found(request: Request, exc: MatchNotFoundException):
    return _cors_response(request, 404, str(exc))


@app.exception_handler(MatchAlreadyExistsException)
async def match_already_exists(request: Request, exc: MatchAlreadyExistsException):
    return _cors_response(request, 409, str(exc))


@app.exception_handler(PlayerAlreadyInQueueException)
async def player_already_in_queue(request: Request, exc: PlayerAlreadyInQueueException):
    return _cors_response(request, 409, str(exc))


@app.exception_handler(PlayerNotInQueueException)
async def player_not_in_queue(request: Request, exc: PlayerNotInQueueException):
    return _cors_response(request, 404, str(exc))


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return _cors_response(request, 500, "An internal server error occurred.")




app.include_router(player_router)
app.include_router(match_router)
app.include_router(leaderboard_router)
app.include_router(suspicious_player_router)
app.include_router(matchmaking_router)
