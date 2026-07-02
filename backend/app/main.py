"""FastAPI-приложение: единый backend для мини-аппки и админ-дашборда."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import admin, internal, mock, orders, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="TG Shop API", version="1.0.0", lifespan=lifespan)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(products.router)
    app.include_router(orders.router)
    app.include_router(admin.router)
    app.include_router(internal.router)
    app.include_router(mock.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
