from typing import Optional
from datetime import datetime
from sqlmodel import Session, select
from app.models.movimentacao import Movimentacao
from app.schemas.movimentacao_base import MovimentacaoBaseCreate, MovimentacaoBaseUpdate
from app.utils.enums import TipoMovimentacao


class MovimentacaoRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, movimentacao_id: int) -> Optional[Movimentacao]:
        return self.session.get(Movimentacao, movimentacao_id)

    def get_all(self) -> list[Movimentacao]:
        statement = select(Movimentacao).order_by(Movimentacao.data.desc())
        return self.session.exec(statement).all()

    def get_by_cliente(self, cliente_id: int) -> list[Movimentacao]:
        statement = (
            select(Movimentacao)
            .where(Movimentacao.cliente_id == cliente_id)
            .order_by(Movimentacao.data.desc())
        )
        return self.session.exec(statement).all()

    def get_by_item(self, item_id: int) -> list[Movimentacao]:
        statement = (
            select(Movimentacao)
            .where(Movimentacao.item_id == item_id)
            .order_by(Movimentacao.data.desc())
        )
        return self.session.exec(statement).all()

    def get_by_tipo(self, tipo: TipoMovimentacao) -> list[Movimentacao]:
        statement = (
            select(Movimentacao)
            .where(Movimentacao.tipo == tipo)
            .order_by(Movimentacao.data.desc())
        )
        return self.session.exec(statement).all()

    def get_by_periodo(
        self,
        inicio: datetime,
        fim: datetime,
        tipo: TipoMovimentacao | None = None,
    ) -> list[Movimentacao]:

        statement = (
            select(Movimentacao)
            .where(Movimentacao.data >= inicio)
            .where(Movimentacao.data < fim)
        )

        if tipo:
            statement = statement.where(
                Movimentacao.tipo == tipo
            )

        statement = statement.order_by(
            Movimentacao.data.desc()
        )

        return self.session.exec(statement).all()

    def create(self, dados: MovimentacaoBaseCreate, valor_unitario: float) -> Movimentacao:
        movimentacao = Movimentacao(
            item_id=dados.item_id,
            cliente_id=dados.cliente_id,
            tipo=dados.tipo,
            quantidade=dados.quantidade,
            valor_unitario=valor_unitario,
            valor_pago=dados.valor_pago,
        )
        self.session.add(movimentacao)
        self.session.commit()
        self.session.refresh(movimentacao)
        return movimentacao
    
    

    def update(self, movimentacao: Movimentacao, dados: MovimentacaoBaseUpdate) -> Movimentacao:
        campos = dados.model_dump(exclude_unset=True)
        for campo, valor in campos.items():
            setattr(movimentacao, campo, valor)
        self.session.add(movimentacao)
        self.session.commit()
        self.session.refresh(movimentacao)
        return movimentacao

    def delete(self, movimentacao: Movimentacao) -> None:
        self.session.delete(movimentacao)
        self.session.commit()