from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlmodel import Field, SQLModel

BRASILIA = timezone(timedelta(hours=-3))

def agora_brasilia() -> datetime:
    return datetime.now(BRASILIA).replace(tzinfo=None)

class Historico(SQLModel, table=True):
    __tablename__ = "historicos"

    id: Optional[int] = Field(default=None, primary_key=True)
    data: datetime = Field(default_factory=agora_brasilia)

    # O que foi afetado
    entidade: str       # "venda" | "estoque" | "financeiro" | "cliente" | "item"
    operacao: str       # "criacao" | "edicao" | "exclusao" | "pagamento" | "ajuste" | "perda"
    entidade_id: int    # id do registro original

    # Texto legível para exibir na tela
    descricao: str

    # Snapshot opcional antes/depois em JSON
    valor_antes: Optional[str] = Field(default=None)  # ex: '{"quantidade": 10}'
    valor_depois: Optional[str] = Field(default=None)  # ex: '{"quantidade": 8}'