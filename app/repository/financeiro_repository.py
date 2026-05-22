from typing import Optional
from datetime import datetime
from sqlmodel import Session, select
from app.models.financeiro import Financeiro
from app.schemas.financeiro_base import financeiroCreate, financeiroUpdate
from app.utils.enums import TipoFinanceiro, TipoPagamento


class FinanceiroRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, financeiro_id: int) -> Optional[Financeiro]:
        return self.session.get(Financeiro, financeiro_id)

    def get_all(self) -> list[Financeiro]:
        statement = select(Financeiro).order_by(Financeiro.data.desc())
        return self.session.exec(statement).all()

    def get_by_tipo(self, tipo: TipoFinanceiro) -> list[Financeiro]:
        statement = (
            select(Financeiro)
            .where(Financeiro.tipo == tipo)
            .order_by(Financeiro.data.desc())
        )
        return self.session.exec(statement).all()

    def get_by_pagamento(self, pagamento: TipoPagamento) -> list[Financeiro]:
        statement = (
            select(Financeiro)
            .where(Financeiro.pagamento == pagamento)
            .order_by(Financeiro.data.desc())
        )
        return self.session.exec(statement).all()

    def get_by_movimentacao(self, movimentacao_id: int) -> list[Financeiro]:
        statement = (
            select(Financeiro)
            .where(Financeiro.movimentacao_id == movimentacao_id)
            .order_by(Financeiro.data.desc())
        )
        return self.session.exec(statement).all()

    def get_nao_pagos(self) -> list[Financeiro]:
        statement = (
            select(Financeiro)
            .where(Financeiro.pago == False)
            .order_by(Financeiro.data.desc())
        )
        return self.session.exec(statement).all()

    def get_by_periodo(
        self,
        inicio: datetime,
        fim: datetime,
    ) -> list[Financeiro]:

        statement = (
            select(Financeiro)
            .where(
                Financeiro.data >= inicio,
                Financeiro.data < fim,
            )
            .order_by(Financeiro.data.desc())
        )

        return self.session.exec(statement).all()

    def create(self, dados: financeiroCreate) -> Financeiro:
        financeiro = Financeiro(
            tipo=dados.tipo,
            pagamento=dados.pagamento,
            valor=dados.valor,
            descricao=dados.descricao or "",
            movimentacao_id=dados.movimentacao_id,
            pago=dados.pago,
        )
        self.session.add(financeiro)
        self.session.commit()
        self.session.refresh(financeiro)
        return financeiro
    
    

    def update(self, financeiro: Financeiro, dados: financeiroUpdate) -> Financeiro:
        campos = dados.model_dump(exclude_unset=True)
        # mapeia tipo_pagamento -> pagamento se vier no update
        if "pagamento" in campos:
            campos["pagamento"] = campos.pop("pagamento")
        for campo, valor in campos.items():
            setattr(financeiro, campo, valor)
        self.session.add(financeiro)
        self.session.commit()
        self.session.refresh(financeiro)
        return financeiro

    def marcar_pago(self, financeiro: Financeiro) -> Financeiro:
        financeiro.pago = True
        self.session.add(financeiro)
        self.session.commit()
        self.session.refresh(financeiro)
        return financeiro

    def delete(self, financeiro: Financeiro) -> None:
        self.session.delete(financeiro)
        self.session.commit()