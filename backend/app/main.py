from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.specialties import router as specialties_router


app = FastAPI(
    title="Provider Network Adequacy & Access Intelligence",
    version="1.0.0",
    description="Backend API for provider network adequacy analysis."
)


# Frontend → Backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routes
api_router.include_router(analysis_router)
api_router.include_router(specialties_router)
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Provider Network Adequacy backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "provider-network-adequacy-backend"
    }