from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Multi-Tenant Org Manager", lifespan=lifespan)

app.include_router(auth.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
