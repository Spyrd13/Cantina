from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class HistoricoCreate(BaseModel):
    entidade: str
    operacao: str
    entidade_id: int
    descricao: str
    valor_antes: Optional[str] = None
    valor_depois: Optional[str] = None


class HistoricoResponse(BaseModel):
    id: int
    data: datetime
    entidade: str
    operacao: str
    entidade_id: int
    descricao: str
    valor_antes: Optional[str] = None
    valor_depois: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)