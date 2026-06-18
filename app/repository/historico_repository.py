from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.historico import Historico


class HistoricoRepository:
    def __init__(self, session: Session):
        self.session = session

    def buscar(
        self,
        limite: int = 100,
        entidade: Optional[str] = None,
        operacao: Optional[str] = None,
        descricao: Optional[str] = None,
        inicio: Optional[datetime] = None,
        fim: Optional[datetime] = None,
    ) -> list[Historico]:

        stmt = select(Historico)

        if entidade:
            stmt = stmt.where(Historico.entidade == entidade)

        if operacao:
            stmt = stmt.where(Historico.operacao == operacao)

        if descricao:
            stmt = stmt.where(
                Historico.descricao.ilike(f"%{descricao}%")
            )

        if inicio:
            stmt = stmt.where(Historico.data >= inicio)

        if fim:
            stmt = stmt.where(Historico.data < fim)

        stmt = (
            stmt
            .order_by(Historico.data.desc())
            .limit(limite)
        )

        return self.session.exec(stmt).all()

    def get_por_id(self, historico_id: int) -> Optional[Historico]:
        return self.session.get(Historico, historico_id)