from datetime import datetime
from sqlmodel import Session, select

from app.repository.movimentacao_repository import MovimentacaoRepository
from app.repository.item_repository import ItemRepository
from app.repository.cliente_repository import ClienteRepository
from app.schemas.movimentacao_base import (
    MovimentacaoBaseCreate,
    MovimentacaoBaseUpdate,
    MovimentacaoBaseResponse,
)
from app.models.movimentacao import Movimentacao
from app.services.historico_services import HistoricoService
from app.utils.enums import TipoMovimentacao, TipoFinanceiro, TipoPagamento
from app.services.financeiro_services import FinanceiroService
from app.schemas.financeiro_base import financeiroCreate


class MovimentacaoService:
    def __init__(self, session: Session):
        self.repo = MovimentacaoRepository(session)
        self.item_repo = ItemRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.financeiro_service = FinanceiroService(session)
        self.historico_service = HistoricoService(session)

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

    def listar_pendurados(
        self,
        inicio: datetime | None = None,
        fim: datetime | None = None,
        cliente_id: int | None = None,
    ) -> list[MovimentacaoBaseResponse]:
        stmt = (
            select(Movimentacao)
            .where(Movimentacao.tipo == TipoMovimentacao.saida)
            .where(Movimentacao.cliente_id != None)
        )

        if cliente_id:
            stmt = stmt.where(Movimentacao.cliente_id == cliente_id)
        if inicio and fim:
            stmt = stmt.where(Movimentacao.data >= inicio).where(Movimentacao.data < fim)

        stmt = stmt.order_by(Movimentacao.data.desc()).limit(200)
        movs = self.repo.session.exec(stmt).all()

        return [MovimentacaoBaseResponse.model_validate(m) for m in movs]

    # ------------------------------------------------------------------ #
    #  Mutações                                                            #
    # ------------------------------------------------------------------ #

    def registrar(self, dados: MovimentacaoBaseCreate) -> MovimentacaoBaseResponse:

        item = self.item_repo.get_by_id(dados.item_id)
        if not item:
            raise ValueError("Item não encontrado")

        if dados.quantidade <= 0:
            raise ValueError("Quantidade inválida")

        cliente = None
        if dados.cliente_id:
            cliente = self.cliente_repo.get_by_id(dados.cliente_id)
            if not cliente:
                raise ValueError("Cliente não encontrado")

        # =========================
        # VALIDAR ESTOQUE PRIMEIRO
        # =========================
        estoque_antes = item.quantidade or 0

        if dados.tipo in (TipoMovimentacao.saida, TipoMovimentacao.perda):
            if estoque_antes < dados.quantidade:
                raise ValueError("Estoque insuficiente")
            item.quantidade -= dados.quantidade

        elif dados.tipo == TipoMovimentacao.entrada:
            item.quantidade += dados.quantidade

            self.financeiro_service.registrar(
                financeiroCreate(
                    tipo=TipoFinanceiro.despesa,
                    pagamento=TipoPagamento.pix,  # ou deixe o usuário informar
                    valor=float(item.valor) * dados.quantidade,
                    descricao=f"Entrada de estoque - {dados.quantidade}x {item.nome}",
                    movimentacao_id=None,
                )
            )
        elif dados.tipo == TipoMovimentacao.ajuste:
            item.quantidade = dados.quantidade

        estoque_depois = item.quantidade

        # =========================
        # FINANCEIRO
        # =========================
        if dados.tipo == TipoMovimentacao.perda:
            self.financeiro_service.registrar(
                financeiroCreate(
                    tipo=TipoFinanceiro.despesa,
                    pagamento=TipoPagamento.pix,
                    valor=float(item.valor) * dados.quantidade,
                    descricao=f"Perda de estoque - {item.nome}",
                    movimentacao_id=None,
                )
            )

        # =========================
        # SALVA ITEM
        # =========================
        self.item_repo.session.add(item)
        self.item_repo.session.commit()

        # =========================
        # CLIENTE
        # =========================
        if dados.tipo == TipoMovimentacao.saida and cliente:
            valor_total = item.valor * dados.quantidade
            self.cliente_repo.update_saldo(cliente, valor_total)

        # =========================
        # CRIA MOVIMENTAÇÃO
        # =========================
        movimentacao = self.repo.create(dados, valor_unitario=item.valor)

        # =========================
        # AUDITORIA
        # =========================
        if dados.tipo == TipoMovimentacao.saida:
            self.historico_service.registrar(
                entidade="venda",
                operacao="criacao",
                entidade_id=movimentacao.id,
                descricao=(
                    f"Venda de {dados.quantidade}x {item.nome}"
                    + (f" para {cliente.nome}" if cliente else " no balcão")
                ),
                valor_depois={
                    "quantidade": dados.quantidade,
                    "valor_unitario": item.valor,
                    "valor_total": item.valor * dados.quantidade,
                },
            )

        elif dados.tipo == TipoMovimentacao.entrada:
            self.historico_service.registrar(
                entidade="estoque",
                operacao="entrada",
                entidade_id=movimentacao.id,
                descricao=f"Entrada de {dados.quantidade}x {item.nome}",
                valor_antes={"estoque": estoque_antes},
                valor_depois={"estoque": estoque_depois},
            )

        elif dados.tipo == TipoMovimentacao.ajuste:
            self.historico_service.registrar(
                entidade="estoque",
                operacao="ajuste",
                entidade_id=movimentacao.id,
                descricao=f"Ajuste de estoque de {item.nome}: {estoque_antes} → {estoque_depois}un",
                valor_antes={"estoque": estoque_antes},
                valor_depois={"estoque": estoque_depois},
            )

        elif dados.tipo == TipoMovimentacao.perda:
            self.historico_service.registrar(
                entidade="estoque",
                operacao="perda",
                entidade_id=movimentacao.id,
                descricao=f"Perda de {dados.quantidade}x {item.nome}",
                valor_antes={"estoque": estoque_antes},
                valor_depois={"estoque": estoque_depois},
            )

        return MovimentacaoBaseResponse.model_validate(movimentacao)

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

        # Snapshot antes da edição
        antes = {
            "quantidade": mov.quantidade,
            "valor_unitario": mov.valor_unitario,
            "valor_pago": mov.valor_pago,
        }

        mov = self.repo.update(mov, dados)

        # Snapshot depois
        depois = {
            "quantidade": mov.quantidade,
            "valor_unitario": mov.valor_unitario,
            "valor_pago": mov.valor_pago,
        }

        self.historico_service.registrar(
            entidade="venda",
            operacao="edicao",
            entidade_id=mov.id,
            descricao=f"Edição de movimentação id={mov.id}",
            valor_antes=antes,
            valor_depois=depois,
        )

        return MovimentacaoBaseResponse.model_validate(mov)

    def atualizar_lote_valor_pago(self, updates: list[tuple[int, float]]):
        for mov_id, valor in updates:
            self.repo.session.query(Movimentacao).filter(
                Movimentacao.id == mov_id
            ).update({"valor_pago": valor})

            self.historico_service.registrar(
                entidade="venda",
                operacao="pagamento",
                entidade_id=mov_id,
                descricao=f"Pagamento registrado na movimentação id={mov_id}",
                valor_depois={"valor_pago": valor},
            )

        self.repo.session.commit()

    def remover(self, movimentacao_id: int) -> None:
        mov = self._get_or_raise(movimentacao_id)

        # Auditoria ANTES de deletar — depois o objeto some
        self.historico_service.registrar(
            entidade="venda",
            operacao="exclusao",
            entidade_id=mov.id,
            descricao=f"Exclusão de movimentação id={mov.id} ({mov.tipo})",
            valor_antes={
                "tipo": mov.tipo,
                "quantidade": mov.quantidade,
                "valor_unitario": mov.valor_unitario,
            },
        )

        self.repo.delete(mov)

    # ------------------------------------------------------------------ #
    #  Helpers privados                                                    #
    # ------------------------------------------------------------------ #

    def _get_or_raise(self, movimentacao_id: int) -> Movimentacao:
        mov = self.repo.get_by_id(movimentacao_id)
        if not mov:
            raise ValueError(f"Movimentação com id {movimentacao_id} não encontrada.")
        return mov