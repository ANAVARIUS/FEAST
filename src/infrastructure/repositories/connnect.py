"""Motor SQLAlchemy y sesiones; exige `URL_CONEXION` en el entorno o en `.env` en la raiz del repo."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cargar .env desde la raiz del proyecto (no depende del directorio de trabajo actual).
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

from src.core.config import config

_raw_url = (config.url_conexion or os.getenv("URL_CONEXION") or "").strip()
if not _raw_url:
    msg = (
        "Falta URL_CONEXION: agrega en tu `.env` en la raiz del proyecto una linea como "
        "URL_CONEXION=mysql+pymysql://usuario:clave@host:3306/nombre_bd "
        "(o sqlite+pysqlite:///./local.db para pruebas locales)."
    )
    raise RuntimeError(msg)

DATABASE_URL = _raw_url

db = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=db)
Base = declarative_base()
