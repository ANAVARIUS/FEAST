from contextlib import asynccontextmanager
from fastapi import FastAPI
import time
import requests
import logging

from src.core.llm.base import BaseLLM
from src.infrastructure.clients.llama_llm_adapter import LlamaLLMAdapter
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.orchestrator.graph import create_graph
from src.core.config import config  

Telegram_key = config.telegram_token

llm = None
checkpointer = None
graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    print("Inicializando recursos...")
    llm = LlamaLLMAdapter()
    print("LLM inicializado")
    checkpointer = await create_async_redis_checkpointer()
    print("Checkpointer de Redis (async) creado")
    graph = create_graph(llm, checkpointer)
    print("Grafo compilado")
    yield
    print("Cerrando recursos...")

app = FastAPI(lifespan=lifespan)

def get_docker_ngrok_url(retries=5):
    time.sleep(1)
    try:
        response = requests.get("http://ngrok:4040/api/tunnels")
        data = response.json()
        return data['tunnels'][0]['public_url']
    except Exception as e:
        print(f"Could not connect to ngrok API: {e}")
        return None