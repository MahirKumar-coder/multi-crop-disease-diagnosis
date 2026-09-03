import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logger import logger
from app.api.routes.health import router as health_router
from app.api.routes import predict, diseases
from app.core.security import limiter, rate_limit_exceeded_handler
from app.api.routes import history

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Request Logging & Timing Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Inference-Time-ms"] = f"{process_time:.2f}"
    logger.info(f"{request.method} {request.url.path} - Completed in {process_time:.2f}ms (Status: {response.status_code})")
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occured. Please check server logs."}
    )

# Include API route modules directly so route registration remains compatible
# with FastAPI's lazy nested-router representation.
app.include_router(health_router, prefix=f"{settings.API_V1_STR}/health")
app.include_router(predict.router, prefix=settings.API_V1_STR)
app.include_router(diseases.router, prefix=f"{settings.API_V1_STR}/diseases", tags=["Disease Knowledge Base"])
app.include_router(history.router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "online", "version": settings.VERSION}