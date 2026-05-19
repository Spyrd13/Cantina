from pydantic import BaseModel
from typing import Optional

from app.utils.enums import TipoFinanceiro, TipoPagamento



from datetime import datetime



class financeiroBase(BaseModel):
    tipo: TipoFinanceiro
    valor: float
    descricao: Optional[str] = None
    pago: bool = False
    pagamento: TipoPagamento

class financeiroCreate(financeiroBase):
    movimentacao_id: Optional[int] = None

class financeiroUpdate(BaseModel):
    tipo: Optional[TipoFinanceiro] = None
    valor: Optional[float] = None
    descricao: Optional[str] = None
    pagamento: Optional[TipoPagamento] = None
    pago: Optional[bool] = None
    movimentacao_id: Optional[int] = None

class financeiroResponse(financeiroBase):
    id: int
    movimentacao_id: Optional[int] = None
    pago: bool
    data: datetime

    class Config:
        from_attributes = True