from sqlmodel import Session

from app.repository.item_repository import ItemRepository
from app.schemas.item_base import ItemBaseCreate, ItemBaseUpdate, ItemBaseResponse
from app.models.item import Item
from app.repository.movimentacao_repository import MovimentacaoRepository


class ItemService:
    def __init__(self, session: Session):
        self.repo = ItemRepository(session)
        self.mov_repo = MovimentacaoRepository(session)

        from app.services.historico_services import HistoricoService
        self.historico_service = HistoricoService(session)

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

        dados.nome = " ".join(dados.nome.split()).title()

        self._validar_nome(dados.nome)
        self._validar_valor(dados.valor)

        item_existente = self.repo.get_by_nome_exato(dados.nome)

        if item_existente:
            if item_existente.valor == dados.valor:
                raise ValueError("Este item já existe.")
            raise ValueError(
                "Já existe um item com esse nome. "
                "Edite o item existente para alterar o valor."
            )

        item = self.repo.create(dados)

        self.historico_service.registrar(
            entidade="item",
            operacao="criacao",
            entidade_id=item.id,
            descricao=f"Item '{item.nome}' cadastrado — R$ {item.valor:.2f}, estoque inicial: {item.quantidade or 0}un",
            valor_depois={
                "nome": item.nome,
                "valor": item.valor,
                "quantidade": item.quantidade,
            },
        )

        return ItemBaseResponse.model_validate(item)

    def atualizar(self, item_id: int, dados: ItemBaseUpdate) -> ItemBaseResponse:

        item = self._get_or_raise(item_id)

        if dados.nome is not None:
            dados.nome = " ".join(dados.nome.split()).title()
            self._validar_nome(dados.nome)

            item_existente = self.repo.get_by_nome_exato(dados.nome)
            if item_existente and item_existente.id != item_id:
                if item_existente.valor == dados.valor:
                    raise ValueError("Este item já existe.")
                raise ValueError(
                    "Já existe um item com esse nome. "
                    "Edite o item existente para alterar o valor."
                )

        if dados.valor is not None:
            self._validar_valor(dados.valor)

        if dados.quantidade is not None:
            self._validar_quantidade(dados.quantidade)

        antes = {
            "nome": item.nome,
            "valor": item.valor,
            "quantidade": item.quantidade,
        }

        item = self.repo.update(item, dados)

        depois = {
            "nome": item.nome,
            "valor": item.valor,
            "quantidade": item.quantidade,
        }

        # Monta descrição legível com o que mudou
        mudancas = []
        if antes["nome"] != depois["nome"]:
            mudancas.append(f"nome: '{antes['nome']}' → '{depois['nome']}'")
        if antes["valor"] != depois["valor"]:
            mudancas.append(f"valor: R$ {antes['valor']:.2f} → R$ {depois['valor']:.2f}")
        if antes["quantidade"] != depois["quantidade"]:
            mudancas.append(f"estoque: {antes['quantidade']}un → {depois['quantidade']}un")

        descricao_hist = f"Edição de '{item.nome}'" + (f": {', '.join(mudancas)}" if mudancas else " (sem alterações)")

        self.historico_service.registrar(
            entidade="item",
            operacao="edicao",
            entidade_id=item.id,
            descricao=descricao_hist,
            valor_antes=antes,
            valor_depois=depois,
        )

        return ItemBaseResponse.model_validate(item)

    def remover(self, item_id: int) -> None:
        item = self._get_or_raise(item_id)
        if self.mov_repo.existe_movimentacao_do_item(item_id):
            raise ValueError("Não é possível remover um item que já foi movimentado.")

        self.historico_service.registrar(
            entidade="item",
            operacao="exclusao",
            entidade_id=item.id,
            descricao=f"Item '{item.nome}' removido — valor: R$ {item.valor:.2f}, estoque: {item.quantidade or 0}un",
            valor_antes={
                "nome": item.nome,
                "valor": item.valor,
                "quantidade": item.quantidade,
            },
        )

        self.repo.delete(item)

    def adicionar_estoque(self, item_id: int, quantidade: int) -> ItemBaseResponse:
        if quantidade <= 0:
            raise ValueError("A quantidade a adicionar deve ser positiva.")
        item = self._get_or_raise(item_id)
        estoque_antes = item.quantidade or 0
        item = self.repo.update_quantidade(item, quantidade)

        self.historico_service.registrar(
            entidade="item",
            operacao="entrada",
            entidade_id=item.id,
            descricao=f"Estoque de '{item.nome}' aumentado: {estoque_antes}un → {item.quantidade}un (+{quantidade})",
            valor_antes={"quantidade": estoque_antes},
            valor_depois={"quantidade": item.quantidade},
        )

        return ItemBaseResponse.model_validate(item)

    def retirar_estoque(self, item_id: int, quantidade: int) -> ItemBaseResponse:
        if quantidade <= 0:
            raise ValueError("A quantidade a retirar deve ser positiva.")
        item = self._get_or_raise(item_id)
        if (item.quantidade or 0) < quantidade:
            raise ValueError(
                f"Estoque insuficiente para '{item.nome}'. "
                f"Disponível: {item.quantidade}, solicitado: {quantidade}."
            )
        estoque_antes = item.quantidade or 0
        item = self.repo.update_quantidade(item, -quantidade)

        self.historico_service.registrar(
            entidade="item",
            operacao="ajuste",
            entidade_id=item.id,
            descricao=f"Estoque de '{item.nome}' reduzido: {estoque_antes}un → {item.quantidade}un (-{quantidade})",
            valor_antes={"quantidade": estoque_antes},
            valor_depois={"quantidade": item.quantidade},
        )

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