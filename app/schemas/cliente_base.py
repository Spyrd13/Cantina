from pydantic import BaseModel, Field
from typing import Optional






class ClienteBase(BaseModel):
    nome: str
    saldo_devedor: Optional[float] = Field(default=0.0)
    telefone: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    saldo_devedor: Optional[float] = None
    telefone: Optional[str] = None

class ClienteResponse(ClienteBase):
    id: int

    class Config:
        from_attributes = True