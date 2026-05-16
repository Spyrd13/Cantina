from sqlmodel import SQLModel

from app.core.database import engine
import app.models

def create_db():
    SQLModel.metadata.create_all(engine)



if __name__ == "__main__":
    create_db()



print("Banco de dados criado com sucesso!")