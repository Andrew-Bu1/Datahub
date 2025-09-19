from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base

DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)