from sqlmodel import Field, SQLModel
from typing import Optional

from datetime import datetime

from app.utils.enums import TipoFinanceiro, TipoPagamento



class Financeiro(SQLModel, table=True):
    __tablename__ = "financeiros"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    movimentacao_id: Optional[int] = Field(default=None, foreign_key="movimentacoes.id")
    tipo: TipoFinanceiro
    pagamento: TipoPagamento
    valor: float
    pago: bool = Field(default=False)
    data: datetime = Field(default_factory=datetime.utcnow)
    descricao: Optional[str] = Field(default="")