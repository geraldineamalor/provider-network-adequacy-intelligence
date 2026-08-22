from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.providers import router as providers_router
from app.api.routes.network_adequacy import (
    router as network_adequacy_router,
)


app = FastAPI(
    title="Provider Network Adequacy & Access Intelligence",
    version="1.0.0",
    description="Backend API for provider network adequacy analysis.",
)


# Frontend → Backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(
    providers_router,
    prefix="/api/v1",
)
app.include_router(
    network_adequacy_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "message": "Provider Network Adequacy API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }