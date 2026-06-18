import json
from datetime import date, datetime
from enum import Enum

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.historico import Historico


# Tabelas que NÃO devem ser auditadas
IGNORAR = {
    "historicos",
    "movimentacoes",
    "financeiros",
}


# Nome amigável para exibir na tela
MAPA_ENTIDADES = {
    "clientes": "cliente",
    "items": "item",
    "financeiros": "financeiro",
    "movimentacoes": "movimentacao",
}


def converter(valor):
    """
    Converte tipos não serializáveis para JSON.
    """
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()

    if isinstance(valor, Enum):
        return valor.value

    return valor


def serialize_model(obj):
    """
    Serializa apenas as colunas simples do model.
    Ignora relacionamentos.
    """
    dados = {}

    for coluna in obj.__table__.columns:
        valor = getattr(obj, coluna.name)

        try:
            dados[coluna.name] = converter(valor)
        except Exception:
            dados[coluna.name] = str(valor)

    return dados


def deve_ignorar(obj) -> bool:
    """
    Verifica se a entidade deve ser ignorada pela auditoria.
    """
    tabela = getattr(obj, "__tablename__", None)

    return (
        tabela is None
        or tabela in IGNORAR
        or isinstance(obj, Historico)
    )


@event.listens_for(Session, "after_flush")
def registrar_historico(session, flush_context, instances):
    """
    Gera histórico automaticamente para CREATE, UPDATE e DELETE.
    """

    # ==========================
    # CREATE
    # ==========================
    for obj in session.new:

        if deve_ignorar(obj):
            continue

        entidade = MAPA_ENTIDADES.get(
            obj.__tablename__,
            obj.__tablename__,
        )

        historico = Historico(
            entidade=entidade,
            operacao="criacao",
            entidade_id=getattr(obj, "id", 0) or 0,
            descricao=f"Criação de {entidade}",
            valor_depois=json.dumps(
                serialize_model(obj),
                ensure_ascii=False,
            ),
        )

        session.add(historico)

    # ==========================
    # UPDATE
    # ==========================
    for obj in session.dirty:

        if deve_ignorar(obj):
            continue

        state = inspect(obj)

        valor_antes = {}
        valor_depois = {}

        for attr in state.attrs:

            if not attr.history.has_changes():
                continue

            valor_antes[attr.key] = (
                converter(attr.history.deleted[0])
                if attr.history.deleted
                else None
            )

            valor_depois[attr.key] = (
                converter(attr.history.added[0])
                if attr.history.added
                else None
            )

        if not valor_antes:
            continue

        entidade = MAPA_ENTIDADES.get(
            obj.__tablename__,
            obj.__tablename__,
        )

        historico = Historico(
            entidade=entidade,
            operacao="edicao",
            entidade_id=getattr(obj, "id", 0) or 0,
            descricao=f"Edição de {entidade}",
            valor_antes=json.dumps(
                valor_antes,
                ensure_ascii=False,
            ),
            valor_depois=json.dumps(
                valor_depois,
                ensure_ascii=False,
            ),
        )

        session.add(historico)

    # ==========================
    # DELETE
    # ==========================
    for obj in session.deleted:

        if deve_ignorar(obj):
            continue

        entidade = MAPA_ENTIDADES.get(
            obj.__tablename__,
            obj.__tablename__,
        )

        historico = Historico(
            entidade=entidade,
            operacao="exclusao",
            entidade_id=getattr(obj, "id", 0) or 0,
            descricao=f"Exclusão de {entidade}",
            valor_antes=json.dumps(
                serialize_model(obj),
                ensure_ascii=False,
            ),
        )

        session.add(historico)