from pydantic import BaseModel
from typing import Optional

from sqlalchemy import Enum

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
    quantidade: int
    tipo: TipoMovimentacao
    descricao: Optional[str] = None

    class Config:
        from_attributes = True