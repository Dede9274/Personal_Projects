from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database.connection import engine
from app.routers.monitors import router as monitors_router

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally: 
        await engine.dispose()

app =FastAPI(
    title="Uptime Monitor API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(monitors_router)