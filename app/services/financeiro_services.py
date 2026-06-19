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

        # Import lazy para evitar circular
        from app.services.historico_services import HistoricoService
        self.historico_service = HistoricoService(session)

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

    def listar_por_pagamento(self, pagamento: TipoPagamento) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_pagamento(pagamento)]

    def listar_por_movimentacao(self, movimentacao_id: int) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_movimentacao(movimentacao_id)]

    def listar_nao_pagos(self) -> list[financeiroResponse]:
        return [financeiroResponse.model_validate(f) for f in self.repo.get_nao_pagos()]

    def listar_por_periodo(
        self,
        inicio: datetime | None,
        fim: datetime | None,
    ) -> list[financeiroResponse]:
        if inicio is not None and fim is not None and inicio > fim:
            raise ValueError("A data de início não pode ser maior que a data de fim.")
        return [financeiroResponse.model_validate(f) for f in self.repo.get_by_periodo(inicio, fim)]

    def resumo_por_periodo(
        self,
        inicio: datetime | None = None,
        fim: datetime | None = None,
    ):
        registros = self.repo.get_by_periodo(inicio, fim)
        receitas = sum(f.valor for f in registros if f.tipo == TipoFinanceiro.receita)
        despesas = sum(f.valor for f in registros if f.tipo == TipoFinanceiro.despesa)
        return {"receitas": receitas, "despesas": despesas, "saldo": receitas - despesas}

    # ------------------------------------------------------------------ #
    #  Mutações                                                            #
    # ------------------------------------------------------------------ #

    def registrar(self, dados: financeiroCreate) -> financeiroResponse:
        self._validar_valor(dados.valor)
        if dados.movimentacao_id is not None:
            if not self.mov_repo.get_by_id(dados.movimentacao_id):
                raise ValueError(f"Movimentação com id {dados.movimentacao_id} não encontrada.")

        financeiro = self.repo.create(dados)

        tipo_str = getattr(dados.tipo, "value", str(dados.tipo)).capitalize()
        pag_str = getattr(dados.pagamento, "value", str(dados.pagamento)).capitalize()
        descricao = dados.descricao or "-"

        self.historico_service.registrar(
            entidade="financeiro",
            operacao="criacao",
            entidade_id=financeiro.id,
            descricao=f"{tipo_str} de R$ {dados.valor:.2f} via {pag_str} — {descricao}",
            valor_depois={
                "tipo": tipo_str,
                "pagamento": pag_str,
                "valor": dados.valor,
                "descricao": descricao,
            },
        )

        return financeiroResponse.model_validate(financeiro)

    def atualizar(self, financeiro_id: int, dados: financeiroUpdate) -> financeiroResponse:
        fin = self._get_or_raise(financeiro_id)
        if dados.valor is not None:
            self._validar_valor(dados.valor)
        if dados.movimentacao_id is not None:
            if not self.mov_repo.get_by_id(dados.movimentacao_id):
                raise ValueError(f"Movimentação com id {dados.movimentacao_id} não encontrada.")

        antes = {
            "tipo": getattr(fin.tipo, "value", str(fin.tipo)),
            "pagamento": getattr(fin.pagamento, "value", str(fin.pagamento)),
            "valor": fin.valor,
            "descricao": fin.descricao,
            "pago": fin.pago,
        }

        fin = self.repo.update(fin, dados)

        depois = {
            "tipo": getattr(fin.tipo, "value", str(fin.tipo)),
            "pagamento": getattr(fin.pagamento, "value", str(fin.pagamento)),
            "valor": fin.valor,
            "descricao": fin.descricao,
            "pago": fin.pago,
        }

        # Monta descrição legível com o que mudou
        mudancas = []
        if antes["valor"] != depois["valor"]:
            mudancas.append(f"valor: R$ {antes['valor']:.2f} → R$ {depois['valor']:.2f}")
        if antes["tipo"] != depois["tipo"]:
            mudancas.append(f"tipo: {antes['tipo']} → {depois['tipo']}")
        if antes["pagamento"] != depois["pagamento"]:
            mudancas.append(f"pagamento: {antes['pagamento']} → {depois['pagamento']}")
        if antes["descricao"] != depois["descricao"]:
            mudancas.append(f"descrição: '{antes['descricao']}' → '{depois['descricao']}'")

        descricao_hist = f"Edição financeiro #{fin.id}" + (f": {', '.join(mudancas)}" if mudancas else " (sem alterações)")

        self.historico_service.registrar(
            entidade="financeiro",
            operacao="edicao",
            entidade_id=fin.id,
            descricao=descricao_hist,
            valor_antes=antes,
            valor_depois=depois,
        )

        return financeiroResponse.model_validate(fin)

    def marcar_como_pago(self, financeiro_id: int) -> financeiroResponse:
        fin = self._get_or_raise(financeiro_id)
        if fin.pago:
            raise ValueError("Este registro já está marcado como pago.")

        fin = self.repo.marcar_pago(fin)

        self.historico_service.registrar(
            entidade="financeiro",
            operacao="edicao",
            entidade_id=fin.id,
            descricao=f"Financeiro #{fin.id} marcado como pago — R$ {fin.valor:.2f}",
            valor_depois={"pago": True, "valor": fin.valor},
        )

        return financeiroResponse.model_validate(fin)

    def remover(self, financeiro_id: int) -> None:
        fin = self._get_or_raise(financeiro_id)
        if fin.pago:
            raise ValueError("Não é possível remover um registro já pago.")

        tipo_str = getattr(fin.tipo, "value", str(fin.tipo)).capitalize()
        pag_str = getattr(fin.pagamento, "value", str(fin.pagamento)).capitalize()

        self.historico_service.registrar(
            entidade="financeiro",
            operacao="exclusao",
            entidade_id=fin.id,
            descricao=f"Exclusão de {tipo_str} R$ {fin.valor:.2f} via {pag_str} — {fin.descricao or '-'}",
            valor_antes={
                "tipo": tipo_str,
                "pagamento": pag_str,
                "valor": fin.valor,
                "descricao": fin.descricao,
            },
        )

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