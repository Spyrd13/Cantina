from typing import Optional
from sqlmodel import Session, select
from app.models.cliente import Cliente
from app.schemas.cliente_base import ClienteCreate, ClienteUpdate
 
 
class ClienteRepository:
    def __init__(self, session: Session):
        self.session = session
 
    def get_by_id(self, cliente_id: int) -> Optional[Cliente]:
        return self.session.get(Cliente, cliente_id)
 
    def get_all(self) -> list[Cliente]:
        statement = select(Cliente).order_by(Cliente.nome)
        return self.session.exec(statement).all()
 
    def get_by_nome(self, nome: str) -> list[Cliente]:
        statement = select(Cliente).where(Cliente.nome.ilike(f"%{nome}%")).order_by(Cliente.nome)
        return self.session.exec(statement).all()
 
    def get_devedores(self) -> list[Cliente]:
        """Retorna clientes com saldo devedor maior que zero."""
        statement = select(Cliente).where(Cliente.saldo_devedor > 0).order_by(Cliente.nome)
        return self.session.exec(statement).all()
 
    def create(self, cliente_data: ClienteCreate) -> Cliente:
        cliente = Cliente(**cliente_data.model_dump())
        self.session.add(cliente)
        self.session.commit()
        self.session.refresh(cliente)
        return cliente
 
    def update(self, cliente: Cliente, cliente_data: ClienteUpdate) -> Cliente:
        dados = cliente_data.model_dump(exclude_unset=True)
        for campo, valor in dados.items():
            setattr(cliente, campo, valor)
        self.session.add(cliente)
        self.session.commit()
        self.session.refresh(cliente)
        return cliente
 
    def delete(self, cliente: Cliente) -> None:
        self.session.delete(cliente)
        self.session.commit()
 
    def update_saldo(self, cliente: Cliente, valor: float) -> Cliente:
        """Incrementa (ou decrementa se negativo) o saldo devedor do cliente."""
        cliente.saldo_devedor = (cliente.saldo_devedor or 0.0) + valor
        self.session.add(cliente)
        self.session.commit()
        self.session.refresh(cliente)
        return cliente