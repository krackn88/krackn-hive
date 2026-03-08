from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import router
from .db import engine
from .models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Krackn Hive", lifespan=lifespan)
    app.include_router(router, prefix="/api")
    return app


app = create_app()
