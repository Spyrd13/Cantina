from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.cliente import Cliente

BRASILIA = timezone(timedelta(hours=-3))


def agora_brasilia() -> datetime:
    return datetime.now(BRASILIA).replace(tzinfo=None)


class Movimentacao(SQLModel, table=True):
    __tablename__ = "movimentacoes"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.id")
    cliente_id: Optional[int] = Field(default=None, foreign_key="clientes.id")
    tipo: str
    quantidade: int
    valor_unitario: float
    valor_pago: Optional[float] = None
    data: datetime = Field(default_factory=agora_brasilia)

    item: Optional["Item"] = Relationship(back_populates="movimentacoes")
    cliente: Optional["Cliente"] = Relationship(back_populates="movimentacoes")