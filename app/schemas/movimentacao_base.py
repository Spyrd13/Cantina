from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.utils.enums import TipoMovimentacao


class MovimentacaoBaseCreate(BaseModel):
    item_id: int
    quantidade: int
    cliente_id: Optional[int] = None
    tipo: TipoMovimentacao
    descricao: Optional[str] = None


class MovimentacaoBaseUpdate(BaseModel):
    item_id: Optional[int] = None
    quantidade: Optional[int] = None
    cliente_id: Optional[int] = None
    tipo: Optional[TipoMovimentacao] = None
    descricao: Optional[str] = None


class MovimentacaoBaseResponse(BaseModel):
    id: int

    item_id: int
    cliente_id: Optional[int] = None

    quantidade: int

    tipo: TipoMovimentacao

    valor_unitario: float

    data: datetime

    descricao: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )