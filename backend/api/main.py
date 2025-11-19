from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.core.logging import get_logger, setup_logging
from api.core.middleware import LoggingMiddleware
from api.core.exception import validation_exception_handler
from api.shared.utils.migrations import run_migrations
from api.modules.training.routes import router as train_router
from api.modules.auth import router as auth_router
from api.modules.user import router as user_router

setup_logging()

run_migrations()

# Set up logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom exception handler for validation errors
app.add_exception_handler(RequestValidationError, validation_exception_handler)

if settings.DEBUG:
    app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(train_router, prefix="/api/v1/train", tags=["train"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

