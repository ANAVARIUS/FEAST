import logging
from contextlib import asynccontextmanager
from typing import Optional

import requests
from fastapi import FastAPI

from src.core.config import config
from src.core.logging_setup import configure_logging
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.infrastructure.llm.factory import get_llm
from src.orchestrator.graph import create_graph

configure_logging()
logger = logging.getLogger(__name__)

llm = None
checkpointer = None
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    logger.info("Runtime lifespan: creando LLM vía factory (LLM_PROVIDER=%s)", config.llm_provider)
    llm = get_llm()
    logger.info("Runtime lifespan: LLM=%s", llm.get_capabilities())
    checkpointer = await create_async_redis_checkpointer()
    graph = create_graph(llm, checkpointer)
    logger.info("Runtime lifespan: grafo listo")
    yield
    logger.info("Runtime lifespan: shutdown")


app = FastAPI(lifespan=lifespan)


def get_docker_ngrok_url() -> Optional[str]:
    try:
        response = requests.get("http://ngrok:4040/api/tunnels", timeout=10)
        data = response.json()
        return data["tunnels"][0]["public_url"]
    except Exception:
        return None
