from sqlmodel import Session
from app.repository.cliente_repository import ClienteRepository
from app.schemas.cliente_base import ClienteCreate, ClienteUpdate, ClienteResponse
from app.models.cliente import Cliente


class ClienteService:
    def __init__(self, session: Session):
        self.repo = ClienteRepository(session)

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    def listar_todos(self) -> list[ClienteResponse]:
        clientes = self.repo.get_all()
        return [ClienteResponse.model_validate(c) for c in clientes]

    def buscar_por_id(self, cliente_id: int) -> ClienteResponse:
        cliente = self._get_or_raise(cliente_id)
        return ClienteResponse.model_validate(cliente)

    def buscar_por_nome(self, nome: str) -> list[ClienteResponse]:
        clientes = self.repo.get_by_nome(nome)
        return [ClienteResponse.model_validate(c) for c in clientes]

    def listar_devedores(self) -> list[ClienteResponse]:
        clientes = self.repo.get_devedores()
        return [ClienteResponse.model_validate(c) for c in clientes]

    # ------------------------------------------------------------------ #
    #  Mutações                                                            #
    # ------------------------------------------------------------------ #

    def cadastrar(self, dados: ClienteCreate) -> ClienteResponse:
        self._validar_nome(dados.nome)
        cliente = self.repo.create(dados)
        return ClienteResponse.model_validate(cliente)

    def atualizar(self, cliente_id: int, dados: ClienteUpdate) -> ClienteResponse:
        cliente = self._get_or_raise(cliente_id)
        if dados.nome is not None:
            self._validar_nome(dados.nome)
        cliente = self.repo.update(cliente, dados)
        return ClienteResponse.model_validate(cliente)

    def remover(self, cliente_id: int) -> None:
        cliente = self._get_or_raise(cliente_id)
        if (cliente.saldo_devedor or 0.0) > 0:
            raise ValueError(
                f"O cliente '{cliente.nome}' possui saldo devedor de "
                f"R$ {cliente.saldo_devedor:.2f} e não pode ser removido."
            )
        self.repo.delete(cliente)

    def registrar_debito(self, cliente_id: int, valor: float) -> ClienteResponse:
        """Adiciona um valor ao saldo devedor do cliente (compra fiado)."""
        if valor <= 0:
            raise ValueError("O valor do débito deve ser positivo.")
        cliente = self._get_or_raise(cliente_id)
        cliente = self.repo.update_saldo(cliente, valor)
        return ClienteResponse.model_validate(cliente)

    def registrar_pagamento(self, cliente_id: int, valor: float) -> ClienteResponse:
        """Abate um valor do saldo devedor do cliente."""
        if valor <= 0:
            raise ValueError("O valor do pagamento deve ser positivo.")
        cliente = self._get_or_raise(cliente_id)
        novo_saldo = (cliente.saldo_devedor or 0.0) - valor
        if novo_saldo < 0:
            raise ValueError(
                f"Pagamento de R$ {valor:.2f} excede o saldo devedor de "
                f"R$ {cliente.saldo_devedor:.2f}."
            )
        cliente = self.repo.update_saldo(cliente, -valor)
        return ClienteResponse.model_validate(cliente)

    # ------------------------------------------------------------------ #
    #  Helpers privados                                                    #
    # ------------------------------------------------------------------ #

    def _get_or_raise(self, cliente_id: int) -> Cliente:
        cliente = self.repo.get_by_id(cliente_id)
        if not cliente:
            raise ValueError(f"Cliente com id {cliente_id} não encontrado.")
        return cliente

    @staticmethod
    def _validar_nome(nome: str) -> None:
        if not nome or not nome.strip():
            raise ValueError("O nome do cliente não pode ser vazio.")