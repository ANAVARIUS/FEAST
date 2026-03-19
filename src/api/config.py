import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pyngrok import ngrok
from fastapi import FastAPI

from src.core.llm.gemini import GeminiLLM
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.orchestrator.graph import create_graph

load_dotenv()

Telegram_key = os.getenv("PAPI_BOT_KEY")
Ngrok_token = os.getenv("NGROK_TOKEN")
Port = os.getenv("PORT")

llm = None
checkpointer = None
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    print("Inicializando recursos...")

    llm = GeminiLLM()

    print("LLM inicializado")

    # Crear checkpointer asíncrono con TTL de 8 horas
    checkpointer = await create_async_redis_checkpointer(expire_seconds=28800)
    print("Checkpointer de Redis (async) creado")

    graph = create_graph(llm, checkpointer)
    print("Grafo compilado")

    yield
    print("Cerrando recursos...")


app = FastAPI(lifespan=lifespan)


def get_ngrok_tunnel_url() -> str:
    ngrok.kill()
    ngrok.set_auth_token(Ngrok_token)
    http_tunel = ngrok.connect(Port)
    return http_tunel.public_url