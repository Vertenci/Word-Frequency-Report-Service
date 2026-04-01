import sys
from fastapi import FastAPI
import logging
from src.presentation.routers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Word frequency report service")

app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
