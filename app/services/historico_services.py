import json
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.models.historico import Historico
from app.repository.historico_repository import HistoricoRepository


class HistoricoService:
    def __init__(self, session: Session):
        self.repo = HistoricoRepository(session)

    # =====================================
    # Registro manual (casos específicos)
    # =====================================

    def registrar(
        self,
        entidade: str,
        operacao: str,
        entidade_id: int,
        descricao: str,
        valor_antes: Optional[dict] = None,
        valor_depois: Optional[dict] = None,
    ) -> Historico:

        historico = Historico(
            entidade=entidade,
            operacao=operacao,
            entidade_id=entidade_id,
            descricao=descricao,
            valor_antes=json.dumps(
                valor_antes,
                ensure_ascii=False,
            ) if valor_antes else None,
            valor_depois=json.dumps(
                valor_depois,
                ensure_ascii=False,
            ) if valor_depois else None,
        )

        self.repo.session.add(historico)
        self.repo.session.commit()
        self.repo.session.refresh(historico)

        return historico

    # =====================================
    # Consultas
    # =====================================

    def buscar(
        self,
        limite: int = 100,
        entidade: Optional[str] = None,
        operacao: Optional[str] = None,
        descricao: Optional[str] = None,
        inicio: Optional[datetime] = None,
        fim: Optional[datetime] = None,
    ) -> list[Historico]:

        return self.repo.buscar(
            limite=limite,
            entidade=entidade,
            operacao=operacao,
            descricao=descricao,
            inicio=inicio,
            fim=fim,
        )