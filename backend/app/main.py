"""FastAPI-приложение: единый backend для мини-аппки и админ-дашборда."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import (
    admin,
    internal,
    meta,
    mock,
    orders,
    products,
    robokassa,
    ton,
)


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
    app.include_router(meta.router)
    app.include_router(admin.router)
    app.include_router(internal.router)
    app.include_router(mock.router)
    app.include_router(robokassa.router)
    app.include_router(ton.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # single-origin: бэкенд отдаёт собранную мини-аппку (miniapp/dist), если она есть
    from pathlib import Path

    from fastapi.responses import FileResponse, PlainTextResponse
    from fastapi.staticfiles import StaticFiles
    from starlette.exceptions import HTTPException as StarletteHTTPException

    dist_dir = Path(__file__).resolve().parents[2] / "miniapp" / "dist"
    if dist_dir.is_dir():
        assets_dir = dist_dir / "assets"
        if assets_dir.is_dir():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="assets",
            )

        # Админка (admin/dist, base=/admin/) отдаётся динамически по префиксу
        # /admin — проверяем наличие на каждый запрос, чтобы работало сразу
        # после сборки, без перезапуска бэкенда.
        admin_dist = Path(__file__).resolve().parents[2] / "admin" / "dist"

        @app.get("/", include_in_schema=False)
        def _spa_index():
            return FileResponse(str(dist_dir / "index.html"))

        @app.get("/{full_path:path}", include_in_schema=False)
        def _spa_fallback(full_path: str):
            # API-маршруты обрабатываются выше; сюда попадают только неизвестные GET.
            if full_path.startswith("api/"):
                raise StarletteHTTPException(status_code=404, detail="Not Found")

            # /admin[/*] -> админ-дашборд из admin/dist
            if full_path == "admin" or full_path.startswith("admin/"):
                if not admin_dist.is_dir():
                    return PlainTextResponse(
                        "Админка ещё не собрана. Запусти ./tgshop.sh build — "
                        "появится admin/dist, и /admin заработает без перезапуска.",
                        status_code=503,
                    )
                rel = full_path[len("admin"):].lstrip("/")
                candidate = admin_dist / rel
                if rel and candidate.is_file():
                    return FileResponse(str(candidate))
                return FileResponse(str(admin_dist / "index.html"))

            candidate = dist_dir / full_path
            if candidate.is_file():
                return FileResponse(str(candidate))
            # SPA-fallback: любой другой путь — это маршрут внутри мини-аппки
            return FileResponse(str(dist_dir / "index.html"))

    return app


app = create_app()
