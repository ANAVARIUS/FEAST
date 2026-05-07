import logging
from contextlib import asynccontextmanager
from typing import Optional

import requests
from fastapi import FastAPI

from src.core.config import config, setup_logging
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.infrastructure.llm.factory import get_llm
from src.api.endpoints.pay_pages import pay_router
from src.orchestrator.graph import create_graph

setup_logging()
logger = logging.getLogger(__name__)

llm = None
checkpointer = None
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    logger.info("[app] init llm_provider=%s", config.llm_provider)
    llm = get_llm()
    logger.info("[app] llm %s", llm.get_capabilities())
    checkpointer = await create_async_redis_checkpointer()
    graph = create_graph(llm, checkpointer)
    logger.info("[app] ready")
    yield
    logger.info("[app] shutdown")


app = FastAPI(lifespan=lifespan)
app.include_router(pay_router)


def get_docker_ngrok_url() -> Optional[str]:
    try:
        response = requests.get("http://ngrok:4040/api/tunnels", timeout=10)
        data = response.json()
        return data["tunnels"][0]["public_url"]
    except Exception:
        return None
