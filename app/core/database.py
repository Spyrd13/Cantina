from sqlmodel import SQLModel, create_engine

DATABASE_URL = "sqlite:///database/cantina.db"

engine = create_engine(DATABASE_URL, echo=True)
