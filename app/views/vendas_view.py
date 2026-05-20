# vendas_view.py

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
        super().__init__(expand=True, spacing=0)

        self.session = session
        self._page   = page

        self.service             = MovimentacaoService(session)
        self.item_service        = ItemService(session)
        self.cliente_service     = ClienteService(session)
        self.financeiro_service  = FinanceiroService(session)

        self.itens_pedido = []

        # Cache para evitar queries repetidas ao renderizar o histórico
        self._itens_map    = {}
        self._clientes_map = {}

        self._build()

    # ============================================================
    # BUILD
    # ============================================================

    def _build(self):

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
            label="Pagamento",
            width=180,
            value=TipoPagamento.pix.value,
            options=[
                ft.dropdown.Option(key=TipoPagamento.dinheiro.value, text="Dinheiro"),
                ft.dropdown.Option(key=TipoPagamento.debito.value,   text="Débito"),
                ft.dropdown.Option(key=TipoPagamento.credito.value,  text="Crédito"),
                ft.dropdown.Option(key=TipoPagamento.pix.value,      text="Pix"),
            ],
        )

        self.cb_pendurado = ft.Checkbox(
            label="Pendurado",
            value=False,
            on_change=self._on_pendurado_change,
        )

        self.dd_cliente_venda = ft.Dropdown(
            label="Cliente",
            expand=True,
            visible=False,
            options=self._opcoes_clientes(),
        )

        self.msg_erro = ft.Text("", color=ft.Colors.RED_400)
        self.msg_ok   = ft.Text("", color=ft.Colors.GREEN_600)

        btn_add_item = ft.Button(
            "Adicionar Item",
            icon=ft.Icons.ADD,
            on_click=self._adicionar_item,
        )

        btn_finalizar = ft.Button(
            "Finalizar Venda",
            icon=ft.Icons.SHOPPING_CART_CHECKOUT,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=self._finalizar_venda,
        )

        self.tabela_pedido = ft.Container()

        self.txt_total = ft.Text("Total: R$ 0.00", size=18, weight=ft.FontWeight.BOLD)

        self.tabela_vendas = ft.Container(expand=True)

        self._carregar_tabela_vendas()

        self.controls = [
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    expand=True,
                    
                    controls=[
                        ft.Text("Vendas", size=24, weight=ft.FontWeight.BOLD),
                        ft.Divider(),

                        ft.Row([self.dd_item_venda, self.field_qtd_venda, btn_add_item]),
                        ft.Row([self.dd_pagamento, self.cb_pendurado]),
                        ft.Row([self.dd_cliente_venda]),

                        ft.Container(height=10),

                        ft.Text("Pedido", size=18, weight=ft.FontWeight.BOLD),
                        self.tabela_pedido,
                        self.txt_total,
                        self.msg_erro,
                        self.msg_ok,

                        ft.Row([btn_finalizar]),
                        ft.Divider(),

                        ft.Text("Histórico", size=18, weight=ft.FontWeight.BOLD),
                        self.tabela_vendas,
                    ]
                )
            )
        ]

    # ============================================================
    # EVENTOS
    # ============================================================

    def _on_pendurado_change(self, e):
        pendurado = self.cb_pendurado.value
        self.dd_pagamento.visible     = not pendurado
        self.dd_cliente_venda.visible = pendurado
        self._page.update()

    # ============================================================
    # PEDIDO
    # ============================================================

    def _adicionar_item(self, e):
        try:
            if not self.dd_item_venda.value:
                self.msg_erro.value = "Selecione um item."
                self._page.update()
                return

            item_id    = int(self.dd_item_venda.value)
            quantidade = int(self.field_qtd_venda.value or 1)

            if quantidade <= 0:
                self.msg_erro.value = "Quantidade deve ser maior que zero."
                self._page.update()
                return

            item = self.item_service.buscar_por_id(item_id)
            if not item:
                return

            item_existente = next(
                (i for i in self.itens_pedido if i["item"].id == item.id), None
            )

            if item_existente:
                item_existente["quantidade"] += quantidade
                item_existente["total"] = item_existente["quantidade"] * item_existente["valor_unitario"]
            else:
                self.itens_pedido.append({
                    "item": item,
                    "quantidade": quantidade,
                    "valor_unitario": float(item.valor),
                    "total": float(item.valor) * quantidade,
                })

            self.msg_erro.value = ""
            self._renderizar_pedido()

        except Exception as ex:
            self.msg_erro.value = f"Erro ao adicionar item: {str(ex)}"
            self._page.update()

    def _renderizar_pedido(self):

        rows = []
        total = 0

        for idx, pedido in enumerate(self.itens_pedido):

            item = pedido["item"]
            qtd = pedido["quantidade"]
            subtotal = qtd * item.valor

            total += subtotal

            row = ft.Container(
                padding=10,
                on_hover=self._hover_row,
                content=ft.Row(
                    spacing=8,
                    controls=[

                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                item.nome,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),

                        ft.Container(
                            width=70,
                            content=ft.Text(str(qtd)),
                        ),

                        ft.Container(
                            width=100,
                            content=ft.Text(
                                f"R$ {item.valor:.2f}",
                            ),
                        ),

                        ft.Container(
                            width=100,
                            content=ft.Text(
                                f"R$ {subtotal:.2f}",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),

                        ft.Container(
                            width=60,
                            content=ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.RED_400,
                                data=idx,
                                on_click=self._remover_item,
                            ),
                        ),
                    ],
                ),
            )

            rows.append(row)

            if idx < len(self.itens_pedido) - 1:
                rows.append(
                    ft.Divider(
                        height=1,
                        thickness=0.5,
                        color=ft.Colors.GREY_200,
                    )
                )

        if not rows:
            rows = [
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "Nenhum item no pedido.",
                        color=ft.Colors.GREY_500,
                    ),
                )
            ]

        header = ft.Container(
            bgcolor=ft.Colors.GREY_100,
            padding=10,
            content=ft.Row(
                spacing=8,
                controls=[

                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            "Item",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=70,
                        content=ft.Text(
                            "Qtd",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=100,
                        content=ft.Text(
                            "Valor",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=100,
                        content=ft.Text(
                            "Total",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=60,
                        content=ft.Text(""),
                    ),
                ],
            ),
        )

        tabela = ft.Container(
            bgcolor=ft.Colors.WHITE,
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
            border_radius=10,
            content=ft.Column(
                spacing=0,
                controls=[
                    header,

                    ft.Container(
                        content=ft.Column(
                            spacing=0,
                            controls=rows,
                        ),
                    ),
                ],
            ),
        )

        self.tabela_pedido.content = tabela

        self.txt_total.value = f"Total: R$ {total:.2f}"

        self._page.update()

    def _remover_item(self, e):
        self.itens_pedido.pop(e.control.data)
        self._renderizar_pedido()

    # ============================================================
    # FINALIZAR
    # ============================================================

    def _finalizar_venda(self, e):
        self.msg_erro.value = ""
        self.msg_ok.value   = ""

        if not self.itens_pedido:
            self.msg_erro.value = "Adicione itens ao pedido."
            self._page.update()
            return

        cliente_id = None
        if self.cb_pendurado.value:
            if not self.dd_cliente_venda.value:
                self.msg_erro.value = "Selecione um cliente."
                self._page.update()
                return
            cliente_id = int(self.dd_cliente_venda.value)

        try:
            total_geral = 0

            # Registra todos os itens de uma vez — o service faz 1 commit por chamada,
            # mas agrupamos o financeiro no final para minimizar round-trips.
            for pedido in self.itens_pedido:
                item = pedido["item"]
                qtd  = pedido["quantidade"]
                total_geral += qtd * item.valor

                self.service.registrar(
                    MovimentacaoBaseCreate(
                        item_id=item.id,
                        quantidade=qtd,
                        tipo=TipoMovimentacao.saida,
                        cliente_id=cliente_id,
                    )
                )

            # Um único lançamento financeiro para toda a venda
            self.financeiro_service.registrar(
                financeiroCreate(
                    tipo=TipoFinanceiro.receita,
                    pagamento=(
                        TipoPagamento.pix
                        if self.cb_pendurado.value
                        else TipoPagamento(self.dd_pagamento.value)
                    ),
                    valor=total_geral,
                    descricao="Venda",
                    movimentacao_id=None,
                )
            )

            self.itens_pedido = []
            self._renderizar_pedido()
            self.dd_cliente_venda.value = None
            self.msg_ok.value = "Venda finalizada com sucesso!"

            # Recarrega o histórico reaproveitando o cache de nomes já carregado
            self._carregar_tabela_vendas()

        except Exception as ex:
            self.msg_erro.value = str(ex)
            self._page.update()

    # ============================================================
    # HISTÓRICO
    # ============================================================

    def _carregar_tabela_vendas(self):

        if not self._itens_map:
            self._itens_map = {
                i.id: i.nome
                for i in self.item_service.listar_todos()
            }

        if not self._clientes_map:
            self._clientes_map = {
                c.id: c.nome
                for c in self.cliente_service.listar_todos()
            }

        movs = self.service.listar_por_tipo(
            TipoMovimentacao.saida
        )

        rows = []

        for idx, m in enumerate(movs):

            pendurado = m.cliente_id is not None

            badge = ft.Container(
                bgcolor=(
                    ft.Colors.ORANGE_50
                    if pendurado
                    else ft.Colors.GREEN_50
                ),
                border_radius=6,
                padding=ft.Padding(
                    left=8,
                    top=3,
                    right=8,
                    bottom=3,
                ),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(
                            (
                                ft.Icons.WARNING_AMBER
                                if pendurado
                                else ft.Icons.CHECK_CIRCLE
                            ),
                            size=13,
                            color=(
                                ft.Colors.ORANGE_700
                                if pendurado
                                else ft.Colors.GREEN_700
                            ),
                        ),

                        ft.Text(
                            (
                                "Pendurado"
                                if pendurado
                                else "Pago"
                            ),
                            size=12,
                            color=(
                                ft.Colors.ORANGE_700
                                if pendurado
                                else ft.Colors.GREEN_700
                            ),
                        ),
                    ],
                ),
            )

            row = ft.Container(
                padding=10,
                on_hover=self._hover_row,
                content=ft.Row(
                    spacing=8,
                    controls=[

                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                self._itens_map.get(
                                    m.item_id,
                                    "-"
                                ),
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),

                        ft.Container(
                            width=60,
                            content=ft.Text(
                                str(m.quantidade),
                            ),
                        ),

                        ft.Container(
                            width=100,
                            content=ft.Text(
                                f"R$ {m.valor_unitario:.2f}",
                            ),
                        ),

                        ft.Container(
                            width=130,
                            content=badge,
                        ),

                        ft.Container(
                            width=180,
                            content=ft.Text(
                                self._clientes_map.get(
                                    m.cliente_id,
                                    "-"
                                ),
                            ),
                        ),

                        ft.Container(
                            width=140,
                            content=ft.Text(
                                m.data.strftime(
                                    "%d/%m/%Y %H:%M"
                                ),
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                        ),
                    ],
                ),
            )

            rows.append(row)

            if idx < len(movs) - 1:
                rows.append(
                    ft.Divider(
                        height=1,
                        thickness=0.5,
                        color=ft.Colors.GREY_200,
                    )
                )

        if not rows:
            rows = [
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "Nenhuma venda encontrada.",
                        color=ft.Colors.GREY_500,
                    ),
                )
            ]

        header = ft.Container(
            bgcolor=ft.Colors.GREY_100,
            padding=10,
            content=ft.Row(
                spacing=8,
                controls=[

                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            "Item",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=60,
                        content=ft.Text(
                            "Qtd",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=100,
                        content=ft.Text(
                            "Valor",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=130,
                        content=ft.Text(
                            "Pagamento",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=180,
                        content=ft.Text(
                            "Cliente",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=140,
                        content=ft.Text(
                            "Data",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),
                ],
            ),
        )

        tabela = ft.Container(
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
            border_radius=10,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    header,

                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                            controls=rows,
                        ),
                    ),
                ],
            ),
        )

        self.tabela_vendas.content = tabela

        self._page.update()

    # ============================================================
    # HELPERS
    # ============================================================

    def _opcoes_itens(self):
        itens = self.item_service.listar_todos()
        self._itens_map = {i.id: i.nome for i in itens}   # aproveita pra popular o cache
        return [
            ft.dropdown.Option(key=str(i.id), text=f"{i.nome} (R$ {i.valor:.2f})")
            for i in itens
        ]

    def _opcoes_clientes(self):
        clientes = self.cliente_service.listar_todos()
        self._clientes_map = {c.id: c.nome for c in clientes}   # aproveita pra popular o cache
        return [
            ft.dropdown.Option(key=str(c.id), text=c.nome)
            for c in clientes
        ]
    
    def _hover_row(self, e):
        e.control.bgcolor = (
            ft.Colors.GREY_50
            if e.data == "true"
            else None
        )

        e.control.update()