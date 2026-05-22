from datetime import datetime
from sqlmodel import Session, select

from app.models.movimentacao import Movimentacao
from app.models.financeiro import Financeiro
from app.utils.enums import TipoMovimentacao


class RelatorioRepository:

    def __init__(self, session: Session):
        self.session = session

    # ================================
    # MOVIMENTAÇÕES (VENDAS)
    # ================================
    def get_movimentacoes_periodo(self, inicio: datetime, fim: datetime):
        stmt = (
            select(Movimentacao)
            .where(Movimentacao.data >= inicio)
            .where(Movimentacao.data < fim)
            .where(Movimentacao.tipo == TipoMovimentacao.saida)
        )
        return self.session.exec(stmt).all()

    # ================================
    # FINANCEIRO
    # ================================
    def get_financeiro_periodo(self, inicio: datetime, fim: datetime):
        stmt = (
            select(Financeiro)
            .where(Financeiro.data >= inicio)
            .where(Financeiro.data < fim)
        )
        return self.session.exec(stmt).all()