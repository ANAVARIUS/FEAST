import os
from contextlib import asynccontextmanager
from pyngrok import ngrok
from fastapi import FastAPI

from src.core.llm.gemini import GeminiLLM
from src.core.redis_checkpointer import create_async_redis_checkpointer
from src.orchestrator.graph import create_graph
from src.core.config import config  

Telegram_key = config.telegram_token
Ngrok_token = config.ngrok_token
Port = config.port

llm = None
checkpointer = None
graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, checkpointer, graph
    print("Inicializando recursos...")
    llm = GeminiLLM()
    print("LLM inicializado")
    checkpointer = await create_async_redis_checkpointer()
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