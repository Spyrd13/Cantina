import flet as ft
from sqlmodel import Session

from app.services.movimentacao_services import MovimentacaoService
from app.services.item_services import ItemService
from app.services.cliente_services import ClienteService
from app.services.financeiro_services import FinanceiroService

from app.schemas.movimentacao_base import MovimentacaoBaseCreate
from app.schemas.financeiro_base import financeiroCreate

from app.utils.enums import (
    TipoMovimentacao,
    TipoFinanceiro,
    TipoPagamento,
)


class VendasView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):

        super().__init__(
            expand=True,
            spacing=0,
        )

        self.session = session
        self._page = page

        self.service = MovimentacaoService(session)
        self.item_service = ItemService(session)
        self.cliente_service = ClienteService(session)
        self.financeiro_service = FinanceiroService(session)

        self.itens_pedido = []

        self._build()

    # ============================================================
    # BUILD
    # ============================================================

    def _build(self):

        # ========================================================
        # CAMPOS
        # ========================================================

        self.dd_item_venda = ft.Dropdown(
            label="Item",
            expand=True,
            options=self._opcoes_itens(),
        )

        self.field_qtd_venda = ft.TextField(
            label="Quantidade",
            width=120,
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.dd_pagamento = ft.Dropdown(
            visible=True,
            label="Pagamento",
            width=180,
            value=TipoPagamento.pix.value,
            options=[
                ft.dropdown.Option(
                    key=TipoPagamento.dinheiro.value,
                    text="Dinheiro",
                ),
                ft.dropdown.Option(
                    key=TipoPagamento.debito.value,
                    text="Débito",
                ),
                ft.dropdown.Option(
                    key=TipoPagamento.credito.value,
                    text="Crédito",
                ),
                ft.dropdown.Option(
                    key=TipoPagamento.pix.value,
                    text="Pix",
                ),
            ],
        )

        self.cb_pendurado = ft.Checkbox(
            label="Pendurado",
            value=False,
            on_change=self._toggle_pendurado
        )

        self.dd_cliente_venda = ft.Dropdown(
            label="Cliente",
            expand=True,
            visible=False,
            options=self._opcoes_clientes(),
        )

        self.cb_pendurado.on_change = self._on_pendurado_change

        self.msg_erro = ft.Text(
            "",
            color=ft.Colors.RED_400,
        )

        self.msg_ok = ft.Text(
            "",
            color=ft.Colors.GREEN_600,
        )

        # ========================================================
        # BOTÕES
        # ========================================================

        btn_add_item = ft.ElevatedButton(
            "Adicionar Item",
            icon=ft.Icons.ADD,
            on_click=self._adicionar_item,
        )

        btn_finalizar = ft.ElevatedButton(
            "Finalizar Venda",
            icon=ft.Icons.SHOPPING_CART_CHECKOUT,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=self._finalizar_venda,
        )

        # ========================================================
        # TABELA PEDIDO
        # ========================================================

        self.tabela_pedido = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Item")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("")),
            ],
            rows=[],
        )

        self.txt_total = ft.Text(
            "Total: R$ 0.00",
            size=18,
            weight=ft.FontWeight.BOLD,
        )

        # ========================================================
        # HISTÓRICO
        # ========================================================

        self.tabela_vendas = ft.DataTable(
            expand=True,
            border=ft.BorderSide(1, ft.Colors.GREY_300),

            columns=[
                ft.DataColumn(ft.Text("Item")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Pagamento")),
                ft.DataColumn(ft.Text("Cliente")),
                ft.DataColumn(ft.Text("Data")),
            ],

            rows=[],
        )

        self._carregar_tabela_vendas()


        

        # ========================================================
        # LAYOUT
        # ========================================================

        self.controls = [

            ft.Container(

                expand=True,
                padding=20,

                content=ft.Column([

                    ft.Text(
                        "Vendas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.Divider(),

                    ft.Row([
                        self.dd_item_venda,
                        self.field_qtd_venda,
                        btn_add_item,
                    ]),

                    ft.Row([
                        self.dd_pagamento,
                        self.cb_pendurado,
                    ]),

                    self.dd_cliente_venda,

                    ft.Container(height=10),

                    ft.Text(
                        "Pedido",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),

                    self.tabela_pedido,

                    self.txt_total,

                    self.msg_erro,
                    self.msg_ok,

                    ft.Row([
                        btn_finalizar,
                    ]),

                    ft.Divider(),

                    ft.Text(
                        "Histórico",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.Row(
                        [self.tabela_vendas],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ])
            )
        ]

    def _toggle_pendurado(self, e):

            self.dd_pagamento.visible = not self.cb_pendurado.value

            self.page.update()
            
    # ============================================================
    # EVENTOS
    # ============================================================

    def _on_pendurado_change(self, e):

        self.dd_cliente_venda.visible = (
            self.cb_pendurado.value
        )

        self._page.update()

    # ============================================================
    # PEDIDO
    # ============================================================

    def _adicionar_item(self, e):
        try:
            if not self.dd_item.value:
                return

            item_id = int(self.dd_item.value)
            quantidade = int(self.tf_quantidade.value or 1)

            item = self.item_service.buscar_por_id(item_id)

            if not item:
                return

            # VERIFICA SE ITEM JÁ EXISTE NO PEDIDO
            item_existente = next(
                (
                    i for i in self.itens_pedido
                    if i["item"].id == item.id
                ),
                None
            )

            if item_existente:
                item_existente["quantidade"] += quantidade
                item_existente["total"] = (
                    item_existente["quantidade"] *
                    item_existente["valor_unitario"]
                )

            else:
                self.itens_pedido.append({
                    "item": item,
                    "quantidade": quantidade,
                    "valor_unitario": float(item.valor),
                    "total": float(item.valor) * quantidade
                })

            self._atualizar_tabela()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao adicionar item: {str(ex)}")
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _renderizar_pedido(self):

        self.tabela_pedido.rows = []

        total = 0

        for idx, pedido in enumerate(self.itens_pedido):

            item = pedido["item"]
            qtd = pedido["quantidade"]

            subtotal = (
                qtd * item.valor
            )

            total += subtotal

            self.tabela_pedido.rows.append(

                ft.DataRow(
                    cells=[

                        ft.DataCell(
                            ft.Text(item.nome)
                        ),

                        ft.DataCell(
                            ft.Text(str(qtd))
                        ),

                        ft.DataCell(
                            ft.Text(
                                f"R$ {item.valor:.2f}"
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                f"R$ {subtotal:.2f}"
                            )
                        ),

                        ft.DataCell(

                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.RED,
                                data=idx,
                                on_click=self._remover_item,
                            )
                        ),
                    ]
                )
            )

        self.txt_total.value = (
            f"Total: R$ {total:.2f}"
        )

        self._page.update()

    def _remover_item(self, e):

        idx = e.control.data

        self.itens_pedido.pop(idx)

        self._renderizar_pedido()

    # ============================================================
    # FINALIZAR
    # ============================================================

    def _finalizar_venda(self, e):

        self.msg_erro.value = ""
        self.msg_ok.value = ""

        if not self.itens_pedido:

            self.msg_erro.value = (
                "Adicione itens ao pedido."
            )

            self._page.update()
            return

        cliente_id = None

        if self.cb_pendurado.value:

            if not self.dd_cliente_venda.value:

                self.msg_erro.value = (
                    "Selecione um cliente."
                )

                self._page.update()
                return

            cliente_id = int(
                self.dd_cliente_venda.value
            )

        total_geral = 0

        try:

            for pedido in self.itens_pedido:

                item = pedido["item"]
                qtd = pedido["quantidade"]

                total = qtd * item.valor

                total_geral += total

                self.service.registrar(

                    MovimentacaoBaseCreate(
                        item_id=item.id,
                        quantidade=qtd,
                        tipo=TipoMovimentacao.saida,
                        cliente_id=cliente_id,
                    )
                )

            self.financeiro_service.registrar(

                financeiroCreate(
                    tipo=TipoFinanceiro.receita,
                    tipo_pagamento=TipoPagamento(
                        self.dd_pagamento.value
                    ),
                    valor=total_geral,
                    descricao="Venda",
                    movimentacao_id=None,
                )
            )

            self.itens_pedido = []

            self._renderizar_pedido()

            self.dd_cliente_venda.value = None

            self.msg_ok.value = (
                "Venda finalizada com sucesso!"
            )

            self._carregar_tabela_vendas()

        except Exception as ex:

            self.msg_erro.value = str(ex)

        self._page.update()

    # ============================================================
    # HISTÓRICO
    # ============================================================

    def _carregar_tabela_vendas(self):

        movs = self.service.listar_por_tipo(
            TipoMovimentacao.saida
        )

        itens = {
            i.id: i.nome
            for i in self.item_service.listar_todos()
        }

        clientes = {
            c.id: c.nome
            for c in self.cliente_service.listar_todos()
        }

        self.tabela_vendas.rows = [

            ft.DataRow(
                cells=[

                    ft.DataCell(
                        ft.Text(
                            itens.get(
                                m.item_id,
                                "-"
                            )
                        )
                    ),

                    ft.DataCell(
                        ft.Text(
                            str(m.quantidade)
                        )
                    ),

                    ft.DataCell(
                        ft.Text(
                            f"R$ {m.valor_unitario:.2f}"
                        )
                    ),

                    ft.DataCell(
                        ft.Text(
                            "Pendurado"
                            if m.cliente_id
                            else "Pago"
                        )
                    ),

                    ft.DataCell(
                        ft.Text(
                            clientes.get(
                                m.cliente_id,
                                "-"
                            )
                        )
                    ),

                    ft.DataCell(
                        ft.Text(
                            m.data.strftime(
                                "%d/%m/%Y %H:%M"
                            )
                        )
                    ),
                ]
            )

            for m in movs
        ]

        self._page.update()

    # ============================================================
    # HELPERS
    # ============================================================

    def _opcoes_itens(self):

        itens = self.item_service.listar_todos()

        return [

            ft.dropdown.Option(
                key=str(i.id),
                text=(
                    f"{i.nome} "
                    f"(R$ {i.valor:.2f})"
                )
            )

            for i in itens
        ]

    def _opcoes_clientes(self):

        clientes = (
            self.cliente_service.listar_todos()
        )

        return [

            ft.dropdown.Option(
                key=str(c.id),
                text=c.nome,
            )

            for c in clientes
        ]