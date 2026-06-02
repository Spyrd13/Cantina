from datetime import datetime
from collections import defaultdict

from app.repository.relatorio_repository import RelatorioRepository
from app.services.item_services import ItemService
from app.services.cliente_services import ClienteService
from app.utils.enums import TipoPagamento, TipoFinanceiro


class RelatorioService:

    def __init__(self, session):
        self.repo = RelatorioRepository(session)
        self.item_service = ItemService(session)
        self.cliente_service = ClienteService(session)

    def gerar(self, inicio: datetime, fim: datetime):

        movs = self.repo.get_movimentacoes_periodo(inicio, fim)

        itens = defaultdict(lambda: {"qtd": 0, "valor": 0})

        total_vendas = 0
        dinheiro = 0
        debito = 0
        credito = 0
        pix = 0

        clientes = defaultdict(lambda: {
            "total": 0,
            "pago": 0,
            "saldo": 0,
        })

        # Processar APENAS movimentações com seus financeiros vinculados
        for m in movs:
            item = self.item_service.buscar_por_id(m.item_id)
            nome_item = item.nome if item else f"Item {m.item_id}"

            valor = m.valor_unitario * m.quantidade

            print(
                f"MOV={m.id} | "
                f"CLIENTE={m.cliente_id} | "
                f"VALOR={valor:.2f} | "
                f"VALOR_PAGO={m.valor_pago} | "
                f"FINANCEIROS={len(getattr(m, 'financeiros', []) or [])}"
            )

            total_vendas += valor

            itens[nome_item]["qtd"] += m.quantidade
            itens[nome_item]["valor"] += valor

            saldo = valor - (m.valor_pago or 0)

            saldo = valor - (m.valor_pago or 0)

            if m.cliente_id is not None:

                clientes[m.cliente_id]["total"] += valor
                clientes[m.cliente_id]["pago"] += (m.valor_pago or 0)
                clientes[m.cliente_id]["saldo"] += saldo

            if (m.valor_pago or 0) > 0 and len(getattr(m, "financeiros", []) or []) == 0:
                print(
                    "⚠️ MOVIMENTAÇÃO PAGA SEM FINANCEIRO -> "
                    f"ID={m.id} | "
                    f"VALOR={valor:.2f} | "
                    f"PAGO={m.valor_pago}"
                )

                print("\n===== RESUMO =====")
                print("TOTAL_VENDAS =", total_vendas)
                print("DINHEIRO =", dinheiro)
                print("DEBITO =", debito)
                print("CREDITO =", credito)
                print("PIX =", pix)

                pendurado = sum(c["saldo"] for c in clientes.values())
                print("PENDURADO =", pendurado)

                print("CLIENTES:")
                for cid, d in clientes.items():
                    print(
                        cid,
                        "TOTAL=", d["total"],
                        "PAGO=", d["pago"],
                        "SALDO=", d["saldo"]
                    )

                print("==================\n")

            # Processa os financeiros independente de ter cliente
            for f in getattr(m, "financeiros", []) or []:
                if f.tipo == TipoFinanceiro.receita:
                    if f.pagamento == TipoPagamento.dinheiro:
                        dinheiro += f.valor
                    elif f.pagamento == TipoPagamento.debito:
                        debito += f.valor
                    elif f.pagamento == TipoPagamento.credito:
                        credito += f.valor
                    elif f.pagamento == TipoPagamento.pix:
                        pix += f.valor

        return {
            "itens": itens,
            "total_vendas": total_vendas,
            "dinheiro": dinheiro,
            "debito": debito,
            "credito": credito,
            "pix": pix,
            "pendurado_total": sum(
            c["saldo"] for c in clientes.values()
        ),
        "clientes": clientes,
        }