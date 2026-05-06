import logging
import time
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI

from src.api.endpoints.pay_pages import pay_router
from src.api.endpoints.stripe_webhook import router as stripe_webhook_router
from src.core.config import config, setup_logging
from src.core.llm.base import BaseLLM
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.infrastructure.clients.llm_factory import get_llm
from src.orchestrator.graph import create_graph

setup_logging()

logger = logging.getLogger(__name__)

Telegram_key = config.telegram_token

llm: BaseLLM | None = None
checkpointer = None
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    logger.info("[app] init llm+redis+graph")
    llm = get_llm()
    logger.info("[app] llm %s", llm.get_capabilities())
    checkpointer = await create_async_redis_checkpointer()
    graph = create_graph(llm, checkpointer)
    logger.info("[app] ready")
    yield
    logger.info("[app] shutdown")


app = FastAPI(lifespan=lifespan)
app.include_router(pay_router)
app.include_router(stripe_webhook_router)


def get_docker_ngrok_url(retries=5):
    time.sleep(1)
    try:
        response = requests.get("http://ngrok:4040/api/tunnels")
        data = response.json()
        url = data["tunnels"][0]["public_url"]
        logger.info("[app] ngrok %s", url)
        return url
    except Exception as e:
        logger.warning("[app] ngrok error: %s", e)
        return None
