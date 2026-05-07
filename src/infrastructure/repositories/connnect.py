"""Motor SQLAlchemy y sesiones; admite URL_CONEXION/URL_CONNECTION desde entorno o config."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cargar .env desde la raiz del proyecto (no depende del directorio de trabajo actual).
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

from src.core.config import config

_raw_url = (
    config.url_conexion
    or config.url_connection
    or os.getenv("URL_CONEXION")
    or os.getenv("URL_CONNECTION")
    or ""
).strip()
if not _raw_url:
    msg = (
        "Falta URL_CONEXION/URL_CONNECTION: agrega en tu `.env` una linea como "
        "URL_CONEXION=mysql+pymysql://usuario:clave@host:3306/nombre_bd "
        "(o sqlite+pysqlite:///./local.db para pruebas locales)."
    )
    raise RuntimeError(msg)

DATABASE_URL = _raw_url

db = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=db)
Base = declarative_base()
