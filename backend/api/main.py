from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.core.config import settings
from api.core.logging import get_logger, setup_logging
from api.core.middleware import LoggingMiddleware
from api.core.exception import validation_exception_handler
from api.utils.migrations import run_migrations
from api.src.train.routes import router as train_router
from api.src.auth import auth_router
from api.src.user import user_router

setup_logging()

run_migrations()

# Set up logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

# Add custom exception handler for validation errors
app.add_exception_handler(RequestValidationError, validation_exception_handler)

if settings.DEBUG:
    app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(train_router, prefix="/api/v1/train", tags=["train"])
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user_router.router, prefix="/api/v1/user", tags=["user"])

@app.get("/")
async def health_check():
    return {"status": "ok"}

