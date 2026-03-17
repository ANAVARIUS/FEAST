from sqlalchemy import create_engine
import sys
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("URL_CONEXION")

db = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=db)
Base = declarative_base()