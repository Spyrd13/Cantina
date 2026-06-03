from datetime import datetime, timedelta

import flet as ft
from sqlmodel import Session

from app.services.venda_service import VendaService
from app.services.item_services import ItemService
from app.services.cliente_services import ClienteService
from app.services.movimentacao_services import MovimentacaoService

from app.utils.enums import TipoMovimentacao, TipoPagamento


class VendasView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)

        self.session  = session
        self._page    = page

        self.venda_service    = VendaService(session)
        self.item_service     = ItemService(session)
        self.cliente_service  = ClienteService(session)
        self.mov_service      = MovimentacaoService(session)

        self.itens_pedido = []

        self._itens_cache = {}
        self._itens_map   = {}
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
        self.txt_total     = ft.Text("Total: R$ 0.00", size=18, weight=ft.FontWeight.BOLD)
        self.tabela_vendas = ft.Container(expand=True)

        self._carregar_tabela_vendas()

        self.controls = [
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
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
                    ],
                ),
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
        self.msg_erro.value = ""

        if not self.dd_item_venda.value:
            self.msg_erro.value = "Selecione um item."
            self._page.update()
            return

        try:
            item_id    = int(self.dd_item_venda.value)
            quantidade = int(self.field_qtd_venda.value or 1)
        except ValueError:
            self.msg_erro.value = "Quantidade inválida."
            self._page.update()
            return

        if quantidade <= 0:
            self.msg_erro.value = "Quantidade deve ser maior que zero."
            self._page.update()
            return

        item = self._itens_cache.get(item_id)
        if not item:
            self.msg_erro.value = "Item não encontrado."
            self._page.update()
            return

        existente = next((i for i in self.itens_pedido if i["item_id"] == item.id), None)

        if existente:
            existente["quantidade"] += quantidade
        else:
            self.itens_pedido.append({
                "item_id":        item.id,
                "nome":           item.nome,
                "valor_unitario": float(item.valor),
                "quantidade":     quantidade,
            })

        self._renderizar_pedido()

    def _renderizar_pedido(self):
        rows  = []
        total = 0.0

        for idx, pedido in enumerate(self.itens_pedido):
            qtd      = pedido["quantidade"]
            valor    = pedido["valor_unitario"]
            subtotal = qtd * valor
            total   += subtotal

            row = ft.Container(
                padding=10,
                on_hover=self._hover_row,
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Text(pedido["nome"], weight=ft.FontWeight.BOLD),
                        ),
                        ft.Container(width=70,  content=ft.Text(str(qtd))),
                        ft.Container(width=100, content=ft.Text(f"R$ {valor:.2f}")),
                        ft.Container(
                            width=100,
                            content=ft.Text(f"R$ {subtotal:.2f}", weight=ft.FontWeight.BOLD),
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
                rows.append(ft.Divider(height=1, thickness=0.5, color=ft.Colors.GREY_200))

        if not rows:
            rows = [ft.Container(
                padding=20,
                content=ft.Text("Nenhum item no pedido.", color=ft.Colors.GREY_500),
            )]

        def _header_col(text, width=None, expand=False):
            return ft.Container(
                expand=expand,
                width=width,
                content=ft.Text(text, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            )

        header = ft.Container(
            bgcolor=ft.Colors.GREY_100,
            padding=10,
            content=ft.Row(spacing=8, controls=[
                _header_col("Item",  expand=True),
                _header_col("Qtd",   width=70),
                _header_col("Valor", width=100),
                _header_col("Total", width=100),
                ft.Container(width=60, content=ft.Text("")),
            ]),
        )

        self.tabela_pedido.content = ft.Container(
            bgcolor=ft.Colors.WHITE,
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
            border_radius=10,
            content=ft.Column(spacing=0, controls=[
                header,
                ft.Container(content=ft.Column(spacing=0, controls=rows)),
            ]),
        )

        self.txt_total.value = f"Total: R$ {total:.2f}"
        self._page.update()

    def _remover_item(self, e):
        self.itens_pedido.pop(e.control.data)
        self._renderizar_pedido()

    # ============================================================
    # FINALIZAR — toda a lógica está no VendaService
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

        pagamento = (
            TipoPagamento.pix
            if self.cb_pendurado.value
            else TipoPagamento(self.dd_pagamento.value)
        )

        # Converte para o formato que o VendaService espera
        itens = [
            {"item_id": p["item_id"], "quantidade": p["quantidade"]}
            for p in self.itens_pedido
        ]

        try:
            self.venda_service.finalizar_venda(
                itens_pedido=itens,
                pagamento=pagamento,
                cliente_id=cliente_id,
            )
        except Exception as ex:
            self.msg_erro.value = str(ex)
            self._page.update()
            return

        # Limpa pedido e atualiza UI
        self.itens_pedido = []
        self._renderizar_pedido()
        self.dd_cliente_venda.value = None
        self.msg_ok.value = "Venda finalizada com sucesso!"
        self._carregar_tabela_vendas()

    # ============================================================
    # HISTÓRICO
    # ============================================================

    def _carregar_tabela_vendas(self):
        if not self._itens_map:
            self._itens_map = {i.id: i.nome for i in self.item_service.listar_todos()}

        if not self._clientes_map:
            self._clientes_map = {c.id: c.nome for c in self.cliente_service.listar_todos()}

        inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fim    = inicio + timedelta(days=1)

        movs = self.mov_service.listar_por_periodo(inicio, fim, TipoMovimentacao.saida)

        rows = []
        for idx, m in enumerate(movs):
            pendurado = m.cliente_id is not None

            badge = ft.Container(
                bgcolor=ft.Colors.ORANGE_50 if pendurado else ft.Colors.GREEN_50,
                border_radius=6,
                padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(
                            ft.Icons.WARNING_AMBER if pendurado else ft.Icons.CHECK_CIRCLE,
                            size=13,
                            color=ft.Colors.ORANGE_700 if pendurado else ft.Colors.GREEN_700,
                        ),
                        ft.Text(
                            "Pendurado" if pendurado else "Pago",
                            size=12,
                            color=ft.Colors.ORANGE_700 if pendurado else ft.Colors.GREEN_700,
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
                                self._itens_map.get(m.item_id, "-"),
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),
                        ft.Container(width=60,  content=ft.Text(str(m.quantidade))),
                        ft.Container(width=100, content=ft.Text(f"R$ {m.valor_unitario:.2f}")),
                        ft.Container(width=130, content=badge),
                        ft.Container(
                            width=180,
                            content=ft.Text(self._clientes_map.get(m.cliente_id, "-")),
                        ),
                        ft.Container(
                            width=140,
                            content=ft.Text(
                                m.data.strftime("%d/%m/%Y %H:%M"),
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                        ),
                    ],
                ),
            )

            rows.append(row)
            if idx < len(movs) - 1:
                rows.append(ft.Divider(height=1, thickness=0.5, color=ft.Colors.GREY_200))

        if not rows:
            rows = [ft.Container(
                padding=20,
                content=ft.Text("Nenhuma venda encontrada.", color=ft.Colors.GREY_500),
            )]

        def _header_col(text, width=None, expand=False):
            return ft.Container(
                expand=expand,
                width=width,
                content=ft.Text(text, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            )

        header = ft.Container(
            bgcolor=ft.Colors.GREY_100,
            padding=10,
            content=ft.Row(spacing=8, controls=[
                _header_col("Item",      expand=True),
                _header_col("Qtd",       width=60),
                _header_col("Valor",     width=100),
                _header_col("Pagamento", width=130),
                _header_col("Cliente",   width=180),
                _header_col("Data",      width=140),
            ]),
        )

        self.tabela_vendas.content = ft.Container(
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

        self._page.update()

    # ============================================================
    # HELPERS
    # ============================================================

    def _opcoes_itens(self):
        itens = self.item_service.listar_todos()
        self._itens_cache = {i.id: i for i in itens}
        self._itens_map = {i.id: i.nome for i in itens}
        return [
            ft.dropdown.Option(key=str(i.id), text=f"{i.nome} (R$ {i.valor:.2f})")
            for i in itens
        ]

    def _opcoes_clientes(self):
        clientes = self.cliente_service.listar_todos()
        self._clientes_map = {c.id: c.nome for c in clientes}
        return [
            ft.dropdown.Option(key=str(c.id), text=c.nome)
            for c in clientes
        ]

    def _hover_row(self, e):
        e.control.bgcolor = ft.Colors.GREY_50 if e.data == "true" else None
        e.control.update()