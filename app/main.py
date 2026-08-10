from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, health
from app.core.config import get_settings
from app.db.init_db import init_db


def create_lifespan(init_database: bool) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        if init_database:
            init_db()
        yield

    return lifespan


def create_app(init_database: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=create_lifespan(init_database))
    app.include_router(auth.router)
    app.include_router(health.router)
    return app


app = create_app()

