from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, item, organization


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Multi-Tenant Org Manager",
    description="Use the **Authorize** button below to log in and get a JWT token.",
    lifespan=lifespan,
    swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": False},
)

app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(item.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
