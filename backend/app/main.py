from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, analysis, auth, companies, news, reports, telemetry, users
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.services.bootstrap import ensure_default_access_control
from app.services.migrations import run_database_migrations


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_database_migrations()
    ensure_default_access_control()
    yield


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(companies.router, prefix=settings.api_prefix)
    app.include_router(news.router, prefix=settings.api_prefix)
    app.include_router(analysis.router, prefix=settings.api_prefix)
    app.include_router(reports.router, prefix=settings.api_prefix)
    app.include_router(admin.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(telemetry.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_application()
