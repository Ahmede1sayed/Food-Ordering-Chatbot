import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import Depends

class Database:
    def __init__(self):
        load_dotenv()

        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT")
        self.DB_NAME = os.getenv("DB_NAME")

        self.DATABASE_URL = (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

        self.engine = create_engine(self.DATABASE_URL)

        # Use text() for raw SQL
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT @@hostname, @@port;"))
            print(res.fetchall())

        

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_engine(self):
        return self.engine

    def get_session(self):
        return self.SessionLocal()


db = Database()



def get_db() -> Session:
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()