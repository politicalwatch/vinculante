from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from vinculante.infrastructure.cache.redis import init_cache
from vinculante.presentation.api.routers import health, matches, proposals, sections, targets


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_cache()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, title="Vinculante API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(health.router)
    app.include_router(proposals.router)
    app.include_router(sections.router)
    app.include_router(matches.router)
    app.include_router(targets.router)

    return app
