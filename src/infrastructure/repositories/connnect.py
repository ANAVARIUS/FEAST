from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (os.getenv("URL_CONEXION") or "").strip() or None
if not DATABASE_URL:
    raise RuntimeError(
        "URL_CONNECTION no esta definida o esta vacia. "
        "En Docker, deja URL_CONNECTION sin definir en .env para usar MariaDB del servicio db, "
        "o define una URL mysql+pymysql://..."
    )

db = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=db)
Base = declarative_base()
