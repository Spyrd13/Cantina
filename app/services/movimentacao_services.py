from datetime import datetime
from sqlmodel import Session

from app.repository.movimentacao_repository import MovimentacaoRepository
from app.repository.item_repository import ItemRepository
from app.repository.cliente_repository import ClienteRepository
from app.schemas.movimentacao_base import (
    MovimentacaoBaseCreate,
    MovimentacaoBaseUpdate,
    MovimentacaoBaseResponse,
)
from app.models.movimentacao import Movimentacao
from app.utils.enums import TipoMovimentacao, TipoFinanceiro,  TipoPagamento
from app.services.financeiro_services import FinanceiroService
from app.schemas.financeiro_base import financeiroCreate


class MovimentacaoService:
    def __init__(self, session: Session):
        self.repo = MovimentacaoRepository(session)
        self.item_repo = ItemRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.financeiro_service = FinanceiroService(session)

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def listar_todas(self) -> list[MovimentacaoBaseResponse]:
        return [MovimentacaoBaseResponse.model_validate(m) for m in self.repo.get_all()]

    def buscar_por_id(self, movimentacao_id: int) -> MovimentacaoBaseResponse:
        mov = self._get_or_raise(movimentacao_id)
        return MovimentacaoBaseResponse.model_validate(mov)

    def listar_por_cliente(self, cliente_id: int) -> list[MovimentacaoBaseResponse]:
        return [MovimentacaoBaseResponse.model_validate(m) for m in self.repo.get_by_cliente(cliente_id)]

    def listar_por_item(self, item_id: int) -> list[MovimentacaoBaseResponse]:
        return [MovimentacaoBaseResponse.model_validate(m) for m in self.repo.get_by_item(item_id)]

    def listar_por_tipo(self, tipo: TipoMovimentacao) -> list[MovimentacaoBaseResponse]:
        return [MovimentacaoBaseResponse.model_validate(m) for m in self.repo.get_by_tipo(tipo)]

    def listar_por_periodo(
        self,
        inicio: datetime,
        fim: datetime,
        tipo: TipoMovimentacao | None = None,
    ) -> list[MovimentacaoBaseResponse]:
        if inicio > fim:
            raise ValueError("A data de início não pode ser maior que a data de fim.")
        return [MovimentacaoBaseResponse.model_validate(m) for m in self.repo.get_by_periodo(inicio, fim, tipo)]

    # ------------------------------------------------------------------ #
    #  Mutações                                                            #
    # ------------------------------------------------------------------ #

    def registrar(self, dados: MovimentacaoBaseCreate) -> MovimentacaoBaseResponse:

        item = self.item_repo.get_by_id(dados.item_id)

        if not item:
            raise ValueError(
                f"Item com id {dados.item_id} não encontrado."
            )

        if dados.quantidade <= 0:
            raise ValueError(
                "A quantidade deve ser positiva."
            )

        cliente = None

        if dados.cliente_id is not None:
            cliente = self.cliente_repo.get_by_id(
                dados.cliente_id
            )

            if not cliente:
                raise ValueError(
                    f"Cliente com id {dados.cliente_id} não encontrado."
                )

        # =========================================================
        # SAÍDA / PERDA
        # =========================================================

        if dados.tipo in (
            TipoMovimentacao.saida,
            TipoMovimentacao.perda,
        ):

            if (item.quantidade or 0) < dados.quantidade:
                raise ValueError(
                    f"Estoque insuficiente para '{item.nome}'. "
                    f"Disponível: {item.quantidade}, "
                    f"solicitado: {dados.quantidade}."
                )

            item.quantidade -= dados.quantidade

        # =========================================================
        # ENTRADA
        # =========================================================

        elif dados.tipo == TipoMovimentacao.entrada:

            item.quantidade = (
                item.quantidade or 0
            ) + dados.quantidade

            # Gera despesa automaticamente
            if dados.valor_pago is not None:

                self.financeiro_service.registrar(
                    financeiroCreate(
                        tipo=TipoFinanceiro.despesa,
                        pagamento=TipoPagamento.pix,
                        valor=dados.valor_pago,
                        descricao=f"Compra de estoque - {item.nome}",
                        movimentacao_id=None,
                    )
                )

        # =========================================================
        # AJUSTE
        # =========================================================

        elif dados.tipo == TipoMovimentacao.ajuste:

            item.quantidade = dados.quantidade

        # =========================================================
        # PERDA = prejuízo financeiro
        # =========================================================

        if dados.tipo == TipoMovimentacao.perda:

            valor_perda = float(item.valor) * dados.quantidade

            self.financeiro_service.registrar(
                financeiroCreate(
                    tipo=TipoFinanceiro.despesa,
                    pagamento=TipoPagamento.pix,
                    valor=valor_perda,
                    descricao=f"Perda de estoque - {item.nome}",
                    movimentacao_id=None,
                )
            )

        # =========================================================
        # Atualiza estoque
        # =========================================================

        self.item_repo.session.add(item)
        self.item_repo.session.commit()

        # =========================================================
        # Cliente pendurado
        # =========================================================

        if (
            dados.tipo == TipoMovimentacao.saida
            and cliente is not None
        ):

            valor_total = item.valor * dados.quantidade

            self.cliente_repo.update_saldo(
                cliente,
                valor_total,
            )

        # =========================================================
        # Cria movimentação
        # =========================================================

        movimentacao = self.repo.create(
            dados,
            valor_unitario=item.valor,
        )

        return MovimentacaoBaseResponse.model_validate(
            movimentacao
        )

    def atualizar(self, movimentacao_id: int, dados: MovimentacaoBaseUpdate) -> MovimentacaoBaseResponse:
        mov = self._get_or_raise(movimentacao_id)
        if dados.item_id is not None:
            if not self.item_repo.get_by_id(dados.item_id):
                raise ValueError(f"Item com id {dados.item_id} não encontrado.")
        if dados.cliente_id is not None:
            if not self.cliente_repo.get_by_id(dados.cliente_id):
                raise ValueError(f"Cliente com id {dados.cliente_id} não encontrado.")
        if dados.quantidade is not None and dados.quantidade <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        mov = self.repo.update(mov, dados)
        return MovimentacaoBaseResponse.model_validate(mov)

    def remover(self, movimentacao_id: int) -> None:
        mov = self._get_or_raise(movimentacao_id)
        self.repo.delete(mov)

    # ------------------------------------------------------------------ #
    #  Helpers privados                                                    #
    # ------------------------------------------------------------------ #

    def _get_or_raise(self, movimentacao_id: int) -> Movimentacao:
        mov = self.repo.get_by_id(movimentacao_id)
        if not mov:
            raise ValueError(f"Movimentação com id {movimentacao_id} não encontrada.")
        return mov