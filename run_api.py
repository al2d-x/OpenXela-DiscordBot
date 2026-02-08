from app.api.api import app
from app.core.logging import setup_logging


if __name__ == "__main__":
    import uvicorn

    setup_logging()
    uvicorn.run("app.api.api:app", host="127.0.0.1", port=8000, reload=True)
