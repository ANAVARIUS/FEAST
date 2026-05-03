import logging
import time
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI

from src.core.config import config
from src.core.llm.gemini import GeminiLLM
from src.core.logging_setup import configure_logging
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.api.endpoints.pay_pages import pay_router
from src.orchestrator.graph import create_graph

configure_logging()

logger = logging.getLogger(__name__)

Telegram_key = config.telegram_token

llm = None
checkpointer = None
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    logger.info("Lifespan: inicializando LLM, checkpointer y grafo…")
    llm = GeminiLLM()
    logger.info("Lifespan: LLM listo (%s)", llm.get_capabilities())
    checkpointer = await create_async_redis_checkpointer()
    logger.info("Lifespan: AsyncRedisSaver configurado")
    graph = create_graph(llm, checkpointer)
    logger.info("Lifespan: grafo compilado; aplicación lista para tráfico")
    yield
    logger.info("Lifespan: apagado de la aplicación")


app = FastAPI(lifespan=lifespan)
app.include_router(pay_router)


def get_docker_ngrok_url(retries=5):
    time.sleep(1)
    try:
        response = requests.get("http://ngrok:4040/api/tunnels")
        data = response.json()
        url = data["tunnels"][0]["public_url"]
        logger.info("Ngrok URL obtenida: %s", url)
        return url
    except Exception as e:
        logger.warning("No se pudo obtener URL de ngrok: %s", e)
        return None
