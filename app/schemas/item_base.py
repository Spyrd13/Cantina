from pydantic import BaseModel
from typing import Optional








class ItemBaseCreate(BaseModel):
    nome: str
    quantidade: Optional[int] = None
    valor: float
    descricao: Optional[str] = None

class ItemBaseUpdate(BaseModel):
    nome: Optional[str] = None
    quantidade: Optional[int] = None
    valor: Optional[float] = None
    descricao: Optional[str] = None

class ItemBaseResponse(BaseModel):
    id: int
    nome: str
    quantidade: Optional[int] = None
    valor: float
    descricao: Optional[str] = None

    class Config:
        from_attributes = True