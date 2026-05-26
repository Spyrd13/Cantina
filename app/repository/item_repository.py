from typing import Optional
from sqlmodel import Session, select
from app.models.item import Item
from app.schemas.item_base import ItemBaseCreate, ItemBaseUpdate


class ItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, item_id: int) -> Optional[Item]:
        return self.session.get(Item, item_id)

    def get_all(self) -> list[Item]:
        statement = select(Item).order_by(Item.nome)
        return self.session.exec(statement).all()

    def get_by_nome(self, nome: str) -> list[Item]:
        statement = select(Item).where(Item.nome.ilike(f"%{nome}%")).order_by(Item.nome)
        return self.session.exec(statement).all()
    
    def get_by_nome_exato(self, nome: str) -> Optional[Item]:

        statement = (
            select(Item)
            .where(Item.nome.ilike(nome.strip()))
        )

        return self.session.exec(statement).first()

    def get_sem_estoque(self) -> list[Item]:
        """Retorna itens com quantidade igual a zero."""
        statement = select(Item).where(Item.quantidade <= 0).order_by(Item.nome)
        return self.session.exec(statement).all()

    def create(self, item_data: ItemBaseCreate) -> Item:
        item = Item(**item_data.model_dump())
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(self, item: Item, item_data: ItemBaseUpdate) -> Item:
        dados = item_data.model_dump(exclude_unset=True)
        for campo, valor in dados.items():
            setattr(item, campo, valor)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, item: Item) -> None:
        self.session.delete(item)
        self.session.commit()

    def update_quantidade(self, item: Item, quantidade: int) -> Item:
        """Incrementa (ou decrementa se negativo) a quantidade em estoque."""
        item.quantidade = (item.quantidade or 0) + quantidade
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item