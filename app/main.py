from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.api.routers import admin, embed, libraries
from app.core import configure_logging
from app.core.auth import verify_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield
    from app.api.routers.embed import close_http_client

    await close_http_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vector DB",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.include_router(
        libraries.router,
        prefix="/libraries",
        tags=["libraries"],
        dependencies=[Depends(verify_token)],
    )
    app.include_router(
        admin.router,
        prefix="/admin",
        tags=["admin"],
        dependencies=[Depends(verify_token)],
    )
    app.include_router(
        embed.router,
        prefix="/embeddings",
        tags=["embeddings"],
        dependencies=[Depends(verify_token)],
    )

    return app


app = create_app()
