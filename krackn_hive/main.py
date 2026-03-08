from fastapi import FastAPI

from .api import router
from .db import engine
from .models import Base


def create_app() -> FastAPI:
    app = FastAPI(title="Krackn Hive")
    app.include_router(router, prefix="/api")

    @app.on_event("startup")
    async def startup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    return app


app = create_app()
