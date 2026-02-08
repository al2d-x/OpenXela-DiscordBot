from fastapi import FastAPI

from app.core.config import get_settings


settings = get_settings()
app = FastAPI()


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "token_loaded": bool(settings.discord_token),
        "sqlite_path": settings.sqlite_path,
    }
