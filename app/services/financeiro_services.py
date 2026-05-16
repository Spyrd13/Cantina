from datetime import datetime
from sqlmodel import Session

from app.repository.financeiro_repository import FinanceiroRepository
from app.repository.movimentacao_repository import MovimentacaoRepository
from app.schemas.financeiro_base import (
    financeiroCreate,
    financeiroUpdate,
    financeiroResponse,
)
from app.models.financeiro import Financeiro
from app.utils.enums import TipoFinanceiro, TipoPagamento


class FinanceiroService:
    def __init__(self, session: Session):
        self.repo = FinanceiroRepository(session)
        self.mov_repo = MovimentacaoRepository(session)

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def listar_todos(self) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_all()]

    def buscar_por_id(self, financeiro_id: int) -> financeiroResponse:
        fin = self._get_or_raise(financeiro_id)
        return financeiroResponse.model_validate(fin)

    def listar_por_tipo(self, tipo: TipoFinanceiro) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_tipo(tipo)]

    def listar_por_pagamento(self, tipo_pagamento: TipoPagamento) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_pagamento(tipo_pagamento)]

    def listar_por_movimentacao(self, movimentacao_id: int) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_movimentacao(movimentacao_id)]

    def listar_nao_pagos(self) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_nao_pagos()]

    def listar_por_periodo(self, inicio: datetime, fim: datetime) -> list[financeiroResponse]:
        if inicio > fim:
            raise ValueError("A data de início não pode ser maior que a data de fim.")
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_periodo(inicio, fim)]

    def resumo_por_periodo(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna total de receitas, despesas e saldo no período."""
        registros = self.repo.get_by_periodo(inicio, fim)
        receitas = sum(f.valor for f in registros if f.tipo == TipoFinanceiro.receita)
        despesas = sum(f.valor for f in registros if f.tipo == TipoFinanceiro.despesa)
        return {
            "receitas": receitas,
            "despesas": despesas,
            "saldo": receitas - despesas,
        }

    # ------------------------------------------------------------------ #
    #  Mutações                                                            #
    # ------------------------------------------------------------------ #

    def registrar(self, dados: financeiroCreate) -> financeiroResponse:
        self._validar_valor(dados.valor)

        if dados.movimentacao_id is not None:
            if not self.mov_repo.get_by_id(dados.movimentacao_id):
                raise ValueError(f"Movimentação com id {dados.movimentacao_id} não encontrada.")

        financeiro = self.repo.create(dados)
        return financeiroResponse.model_validate(financeiro)

    def atualizar(self, financeiro_id: int, dados: financeiroUpdate) -> financeiroResponse:
        fin = self._get_or_raise(financeiro_id)

        if dados.valor is not None:
            self._validar_valor(dados.valor)

        if dados.movimentacao_id is not None:
            if not self.mov_repo.get_by_id(dados.movimentacao_id):
                raise ValueError(f"Movimentação com id {dados.movimentacao_id} não encontrada.")

        fin = self.repo.update(fin, dados)
        return financeiroResponse.model_validate(fin)

    def marcar_como_pago(self, financeiro_id: int) -> financeiroResponse:
        fin = self._get_or_raise(financeiro_id)
        if fin.pago:
            raise ValueError("Este registro já está marcado como pago.")
        fin = self.repo.marcar_pago(fin)
        return financeiroResponse.model_validate(fin)

    def remover(self, financeiro_id: int) -> None:
        fin = self._get_or_raise(financeiro_id)
        if fin.pago:
            raise ValueError("Não é possível remover um registro já pago.")
        self.repo.delete(fin)

    # ------------------------------------------------------------------ #
    #  Helpers privados                                                    #
    # ------------------------------------------------------------------ #

    def _get_or_raise(self, financeiro_id: int) -> Financeiro:
        fin = self.repo.get_by_id(financeiro_id)
        if not fin:
            raise ValueError(f"Registro financeiro com id {financeiro_id} não encontrado.")
        return fin

    @staticmethod
    def _validar_valor(valor: float) -> None:
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")