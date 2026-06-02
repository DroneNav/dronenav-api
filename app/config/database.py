import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = quote_plus(os.getenv("DATABASE_PASSWORD"))

DATABASE_URL = (
    f"postgresql+psycopg2://{DATABASE_USER}:"
    f"{DATABASE_PASSWORD}@{DATABASE_HOST}:"
    f"{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_engine(DATABASE_URL)

def check_database():
    with engine.connect() as connection:
        postgres_version = connection.execute(text("SELECT version();")).scalar()
        postgis_version = connection.execute(text("SELECT PostGIS_Version();")).scalar()

        return {
            "status": "connected",
            "postgres_version": postgres_version,
            "postgis_version": postgis_version
        }
