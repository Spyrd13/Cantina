from sqlmodel import Relationship, SQLModel, Field
from typing import TYPE_CHECKING, List, Optional


if TYPE_CHECKING:
   from app.models.movimentacao import Movimentacao






class Item(SQLModel, table=True):
   __tablename__ = "items"
   
   id: Optional[int] = Field(default=None, primary_key=True)
   nome: str
   quantidade: Optional[int] = Field(default=0)
   valor: float
   descricao: Optional[str] = Field(default="")


movimentacoes: List["Movimentacao"] = Relationship(back_populates="item")