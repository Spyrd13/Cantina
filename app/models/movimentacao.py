from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime



if TYPE_CHECKING:
    from app.models.item import Item    
    from app.models.cliente import Cliente


class Movimentacao(SQLModel, table=True):
    __tablename__ = "movimentacoes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.id")
    cliente_id: Optional[int] = Field(default=None, foreign_key="clientes.id")
    tipo: str
    quantidade: int
    valor_unitario: float
    data: datetime = Field(default_factory=datetime.utcnow)




item: Optional["Item"] = Relationship(back_populates="movimentacoes")
cliente: Optional["Cliente"] = Relationship(back_populates="movimentacoes")
    