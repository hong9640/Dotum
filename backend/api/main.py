from fastapi import FastAPI

from api.core.config import settings
from api.core.logging import get_logger, setup_logging
from api.utils.migrations import run_migrations

setup_logging()

run_migrations()

# Set up logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)
# Include routers

@app.get("/health")
async def health_check():
    return {"status": "ok"}

