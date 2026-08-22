from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes import predict, diseases

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health")
api_router.include_router(predict.router, prefix="/predict", tags=["Disease Inference"])
api_router.include_router(diseases.router, prefix="/diseases", tags=["Disease Knowledge Base"])
