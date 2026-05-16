from sqlmodel import Session
from app.repository.item_repository import ItemRepository
from app.schemas.item_base import ItemBaseCreate, ItemBaseUpdate, ItemBaseResponse
from app.models.item import Item


class ItemService:
    def __init__(self, session: Session):
        self.repo = ItemRepository(session)

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def listar_todos(self) -> list[ItemBaseResponse]:
        itens = self.repo.get_all()
        return [ItemBaseResponse.model_validate(i) for i in itens]

    def buscar_por_id(self, item_id: int) -> ItemBaseResponse:
        item = self._get_or_raise(item_id)
        return ItemBaseResponse.model_validate(item)

    def buscar_por_nome(self, nome: str) -> list[ItemBaseResponse]:
        itens = self.repo.get_by_nome(nome)
        return [ItemBaseResponse.model_validate(i) for i in itens]

    def listar_sem_estoque(self) -> list[ItemBaseResponse]:
        itens = self.repo.get_sem_estoque()
        return [ItemBaseResponse.model_validate(i) for i in itens]

    # ------------------------------------------------------------------ #
    #  Mutações                                                            #
    # ------------------------------------------------------------------ #

    def cadastrar(self, dados: ItemBaseCreate) -> ItemBaseResponse:
        self._validar_nome(dados.nome)
        self._validar_valor(dados.valor)
        item = self.repo.create(dados)
        return ItemBaseResponse.model_validate(item)

    def atualizar(self, item_id: int, dados: ItemBaseUpdate) -> ItemBaseResponse:
        item = self._get_or_raise(item_id)
        if dados.nome is not None:
            self._validar_nome(dados.nome)
        if dados.valor is not None:
            self._validar_valor(dados.valor)
        if dados.quantidade is not None:
            self._validar_quantidade(dados.quantidade)
        item = self.repo.update(item, dados)
        return ItemBaseResponse.model_validate(item)

    def remover(self, item_id: int) -> None:
        item = self._get_or_raise(item_id)
        self.repo.delete(item)

    def adicionar_estoque(self, item_id: int, quantidade: int) -> ItemBaseResponse:
        """Adiciona unidades ao estoque do item."""
        if quantidade <= 0:
            raise ValueError("A quantidade a adicionar deve ser positiva.")
        item = self._get_or_raise(item_id)
        item = self.repo.update_quantidade(item, quantidade)
        return ItemBaseResponse.model_validate(item)

    def retirar_estoque(self, item_id: int, quantidade: int) -> ItemBaseResponse:
        """Remove unidades do estoque (usado nas vendas/movimentações)."""
        if quantidade <= 0:
            raise ValueError("A quantidade a retirar deve ser positiva.")
        item = self._get_or_raise(item_id)
        if (item.quantidade or 0) < quantidade:
            raise ValueError(
                f"Estoque insuficiente para '{item.nome}'. "
                f"Disponível: {item.quantidade}, solicitado: {quantidade}."
            )
        item = self.repo.update_quantidade(item, -quantidade)
        return ItemBaseResponse.model_validate(item)

    # ------------------------------------------------------------------ #
    #  Helpers privados                                                    #
    # ------------------------------------------------------------------ #

    def _get_or_raise(self, item_id: int) -> Item:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item com id {item_id} não encontrado.")
        return item

    @staticmethod
    def _validar_nome(nome: str) -> None:
        if not nome or not nome.strip():
            raise ValueError("O nome do item não pode ser vazio.")

    @staticmethod
    def _validar_valor(valor: float) -> None:
        if valor < 0:
            raise ValueError("O valor do item não pode ser negativo.")

    @staticmethod
    def _validar_quantidade(quantidade: int) -> None:
        if quantidade < 0:
            raise ValueError("A quantidade do item não pode ser negativa.")