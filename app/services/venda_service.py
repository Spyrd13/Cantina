from sqlmodel import Session

from app.repository.movimentacao_repository import MovimentacaoRepository
from app.repository.item_repository import ItemRepository
from app.repository.cliente_repository import ClienteRepository
from app.repository.financeiro_repository import FinanceiroRepository

from app.models.movimentacao import Movimentacao
from app.models.financeiro import Financeiro

from app.schemas.movimentacao_base import MovimentacaoBaseCreate
from app.schemas.financeiro_base import financeiroCreate

from app.utils.enums import (
    TipoMovimentacao,
    TipoFinanceiro,
    TipoPagamento,
)


class VendaService:
    """
    Finaliza uma venda inteira em um único commit:
      1. Valida todos os itens e estoque
      2. Desconta estoque de todos os itens
      3. Cria todas as movimentações (flush → gera IDs sem commit)
      4. Cria todos os lançamentos financeiros vinculados
      5. Commit único no final
    """

    def __init__(self, session: Session):
        self.session      = session
        self.item_repo    = ItemRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.mov_repo     = MovimentacaoRepository(session)
        self.fin_repo     = FinanceiroRepository(session)

    def finalizar_venda(
        self,
        itens_pedido: list[dict],
        pagamento: TipoPagamento,
        cliente_id: int | None = None,
    ) -> dict:
        """
        Parâmetros
        ----------
        itens_pedido : list[dict]
            Lista de dicts com ``item_id`` e ``quantidade``.
        pagamento : TipoPagamento
            Forma de pagamento (ignorado em venda pendurada).
        cliente_id : int | None
            Informado → venda pendurada (não paga imediatamente).
        """

        if not itens_pedido:
            raise ValueError("Nenhum item no pedido.")

        pendurado = cliente_id is not None
        pago      = not pendurado

        if pendurado:
            if not self.cliente_repo.get_by_id(cliente_id):
                raise ValueError("Cliente não encontrado.")
            pagamento = TipoPagamento.pix  # placeholder para pendurado

        # ------------------------------------------------------------------
        # 1. Valida tudo antes de alterar qualquer coisa
        # ------------------------------------------------------------------
        itens_resolvidos = []
        for pedido in itens_pedido:
            item = self.item_repo.get_by_id(pedido["item_id"])
            if not item:
                raise ValueError(f"Item {pedido['item_id']} não encontrado.")

            quantidade = pedido["quantidade"]
            if quantidade <= 0:
                raise ValueError(f"Quantidade inválida para o item {item.nome}.")

            if (item.quantidade or 0) < quantidade:
                raise ValueError(f"Estoque insuficiente para '{item.nome}'.")

            itens_resolvidos.append((item, quantidade))

        # ------------------------------------------------------------------
        # 2. Aplica todas as alterações (sem commit ainda)
        # ------------------------------------------------------------------
        total_geral   = 0.0
        movimentacoes = []

        for item, quantidade in itens_resolvidos:
            total_item   = float(item.valor) * quantidade
            total_geral += total_item

            # Desconta estoque
            item.quantidade -= quantidade
            self.session.add(item)

            # Atualiza saldo do cliente se pendurado
            if pendurado:
                cliente = self.cliente_repo.get_by_id(cliente_id)
                self.cliente_repo.update_saldo(cliente, total_item)

            # Cria movimentação
            mov = Movimentacao(
                item_id=item.id,
                quantidade=quantidade,
                tipo=TipoMovimentacao.saida,
                cliente_id=cliente_id,
                valor_unitario=item.valor,
                valor_pago=total_item if pago else None,
            )
            self.session.add(mov)
            movimentacoes.append((mov, item, total_item))

        # flush → banco gera os IDs das movimentações sem commitar
        self.session.flush()

        # Cria lançamentos financeiros com os IDs já disponíveis
        for mov, item, total_item in movimentacoes:
            fin = Financeiro(
                tipo=TipoFinanceiro.receita,
                pagamento=pagamento,
                valor=total_item,
                descricao=f"Venda - {item.nome}",
                movimentacao_id=mov.id,
                pago=pago,
            )
            self.session.add(fin)

        # ------------------------------------------------------------------
        # 3. Commit único
        # ------------------------------------------------------------------
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return {
            "total":         total_geral,
            "movimentacoes": [m for m, _, _ in movimentacoes],
        }