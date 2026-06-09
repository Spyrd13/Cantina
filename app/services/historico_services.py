import json
from datetime import datetime
from typing import Optional
from sqlmodel import Session

from app.models.historico import Historico
from app.repository.historico_repository import HistoricoRepository


class HistoricoService:
    def __init__(self, session: Session):
        self.repo = HistoricoRepository(session)

    # ------------------------------------------------------------------
    # Método central — chamado pelos outros services
    # ------------------------------------------------------------------

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
            valor_antes=json.dumps(valor_antes) if valor_antes else None,
            valor_depois=json.dumps(valor_depois) if valor_depois else None,
        )
        return self.repo.registrar(historico)

    # ------------------------------------------------------------------
    # Consultas — usadas pela view
    # ------------------------------------------------------------------

    def listar_tudo(self, limite: int = 100) -> list[Historico]:
        return self.repo.get_all(limite=limite)

    def listar_por_entidade(
        self,
        entidade: str,
        limite: int = 100,
    ) -> list[Historico]:
        return self.repo.get_por_entidade(entidade=entidade, limite=limite)

    def listar_por_periodo(
        self,
        inicio: datetime,
        fim: datetime,
        entidade: Optional[str] = None,
        limite: int = 100,
    ) -> list[Historico]:
        return self.repo.get_por_periodo(
            inicio=inicio,
            fim=fim,
            entidade=entidade,
            limite=limite,
        )

    def listar_por_entidade_id(
        self,
        entidade: str,
        entidade_id: int,
    ) -> list[Historico]:
        return self.repo.get_por_entidade_id(
            entidade=entidade,
            entidade_id=entidade_id,
        )