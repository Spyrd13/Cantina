from sqlmodel import Field, Relationship, SQLModel
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.movimentacao import Movimentacao





class Cliente(SQLModel, table=True):
    __tablename__ = "clientes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    saldo_devedor: Optional[float] = Field(default=0.0)
    telefone: Optional[str] = Field(default="")


    movimentacoes: list["Movimentacao"] = Relationship(back_populates="cliente")