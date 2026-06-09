from datetime import datetime
from typing import Optional
from sqlmodel import Session, select

from app.models.historico import Historico
from app.utils.enums import TipoFinanceiro


class HistoricoRepository:
    def __init__(self, session: Session):
        self.session = session

    def registrar(self, historico: Historico) -> Historico:
        self.session.add(historico)
        self.session.commit()
        self.session.refresh(historico)
        return historico

    def get_all(self, limite: int = 100) -> list[Historico]:
        stmt = (
            select(Historico)
            .order_by(Historico.data.desc())
            .limit(limite)
        )
        return self.session.exec(stmt).all()

    def get_por_entidade(
        self,
        entidade: str,
        limite: int = 100,
    ) -> list[Historico]:
        stmt = (
            select(Historico)
            .where(Historico.entidade == entidade)
            .order_by(Historico.data.desc())
            .limit(limite)
        )
        return self.session.exec(stmt).all()

    def get_por_periodo(
        self,
        inicio: datetime,
        fim: datetime,
        entidade: Optional[str] = None,
        limite: int = 100,
    ) -> list[Historico]:
        stmt = (
            select(Historico)
            .where(Historico.data >= inicio)
            .where(Historico.data < fim)
        )
        if entidade:
            stmt = stmt.where(Historico.entidade == entidade)

        stmt = stmt.order_by(Historico.data.desc()).limit(limite)
        return self.session.exec(stmt).all()

    def get_por_entidade_id(
        self,
        entidade: str,
        entidade_id: int,
    ) -> list[Historico]:
        stmt = (
            select(Historico)
            .where(Historico.entidade == entidade)
            .where(Historico.entidade_id == entidade_id)
            .order_by(Historico.data.desc())
        )
        return self.session.exec(stmt).all()