import flet as ft
from sqlmodel import Session
from app.services.movimentacao_services import MovimentacaoService
from app.services.item_services import ItemService
from app.services.cliente_services import ClienteService
from app.schemas.movimentacao_base import MovimentacaoBaseCreate
from app.utils.enums import TipoMovimentacao


class MovimentacoesView(ft.Column):
    def __init__(self, session: Session, page: ft.Page, aba_inicial: int = 0):
        super().__init__(expand=True, spacing=0)
        self.session = session
        self._page = page
        self._aba_inicial = aba_inicial  # ← adiciona essa linha
        self.service = MovimentacaoService(session)
        self.item_service = ItemService(session)
        self.cliente_service = ClienteService(session)
        self._build()

    def _build(self):
        aba_vendas = self._build_vendas()
        aba_estoque = self._build_estoque()

        tab_vendas = ft.Tab("Vendas")
        tab_vendas.content = aba_vendas

        tab_estoque = ft.Tab("Estoque")
        tab_estoque.content = aba_estoque

        tabs = ft.Tabs(
            selected_index=self._aba_inicial,
            expand=True,
            
        )
        tabs=[tab_vendas, tab_estoque]
        
        self.controls = [
            ft.Container(
                content=tabs,
                padding=24,
                expand=True,
            )
        ]
    # ================================================================ #
    #  ABA VENDAS                                                       #
    # ================================================================ #

    def _build_vendas(self) -> ft.Container:
        # Dropdowns
        self.dd_item_venda = ft.Dropdown(
            label="Item",
            expand=True,
            options=self._opcoes_itens(),
        )
        self.field_qtd_venda = ft.TextField(
            label="Quantidade",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="1",
        )

        # Checkboxes tipo venda
        self.cb_avulsa = ft.Checkbox(
            label="Venda avulsa",
            value=True,
            on_change=self._on_tipo_venda_change,
        )
        self.cb_pendurado = ft.Checkbox(
            label="Pendurado",
            value=False,
            on_change=self._on_tipo_venda_change,
        )

        # Dropdown cliente (visível só se pendurado)
        self.dd_cliente_venda = ft.Dropdown(
            label="Cliente",
            expand=True,
            options=self._opcoes_clientes(),
            visible=False,
        )

        self.msg_erro_venda = ft.Text("", color=ft.Colors.RED_400, size=13)
        self.msg_ok_venda = ft.Text("", color=ft.Colors.GREEN_600, size=13)

        btn_registrar = ft.ElevatedButton(
            "Registrar Venda",
            icon=ft.Icons.SHOPPING_CART,
            on_click=self._registrar_venda,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )

        # Tabela histórico vendas
        self.tabela_vendas = ft.DataTable(
            expand=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            column_spacing=20,
            columns=[
                ft.DataColumn(ft.Text("Item", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Qtd", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Valor Unit.", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        self._carregar_tabela_vendas()

        return ft.Container(
            content=ft.Column([
                ft.Text("Registrar Venda", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.cb_avulsa, self.cb_pendurado]),
                ft.Row([self.dd_item_venda, self.field_qtd_venda]),
                self.dd_cliente_venda,
                self.msg_erro_venda,
                self.msg_ok_venda,
                ft.Row([btn_registrar]),
                ft.Container(height=16),
                ft.Text("Histórico de Vendas", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.tabela_vendas], scroll=ft.ScrollMode.AUTO),
            ]),
            padding=16,
        )

    def _on_tipo_venda_change(self, e):
        # Garante que só um checkbox fica marcado por vez
        if e.control == self.cb_avulsa and e.control.value:
            self.cb_pendurado.value = False
            self.dd_cliente_venda.visible = False
        elif e.control == self.cb_pendurado and e.control.value:
            self.cb_avulsa.value = False
            self.dd_cliente_venda.visible = True
        else:
            # Não deixa desmarcar os dois
            e.control.value = True
        self._page.update()

    def _registrar_venda(self, e):
        self.msg_erro_venda.value = ""
        self.msg_ok_venda.value = ""

        if not self.dd_item_venda.value:
            self.msg_erro_venda.value = "Selecione um item."
            self._page.update()
            return

        try:
            quantidade = int(self.field_qtd_venda.value or 0)
            if quantidade <= 0:
                raise ValueError()
        except ValueError:
            self.msg_erro_venda.value = "Quantidade inválida."
            self._page.update()
            return

        cliente_id = None
        if self.cb_pendurado.value:
            if not self.dd_cliente_venda.value:
                self.msg_erro_venda.value = "Selecione um cliente para venda pendurada."
                self._page.update()
                return
            cliente_id = int(self.dd_cliente_venda.value)

        try:
            self.service.registrar(MovimentacaoBaseCreate(
                item_id=int(self.dd_item_venda.value),
                quantidade=quantidade,
                tipo=TipoMovimentacao.saida,
                cliente_id=cliente_id,
            ))
            self.msg_ok_venda.value = "Venda registrada com sucesso!"
            self.dd_item_venda.value = None
            self.field_qtd_venda.value = "1"
            self.dd_cliente_venda.value = None
            self._carregar_tabela_vendas()
        except ValueError as ex:
            self.msg_erro_venda.value = str(ex)
            self._page.update()

    def _carregar_tabela_vendas(self, movs=None):
        if movs is None:
            movs = self.service.listar_por_tipo(TipoMovimentacao.saida)

        # Mapeia item_id para nome
        itens = {i.id: i.nome for i in self.item_service.listar_todos()}

        self.tabela_vendas.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(itens.get(m.item_id, str(m.item_id)))),
                ft.DataCell(ft.Text(str(m.quantidade))),
                ft.DataCell(ft.Text(f"R$ {m.valor_unitario:.2f}")),
                ft.DataCell(ft.Text(f"R$ {m.quantidade * m.valor_unitario:.2f}")),
                ft.DataCell(ft.Text("Pendurado" if m.cliente_id else "Avulsa")),
                ft.DataCell(ft.Text(m.data.strftime("%d/%m/%Y %H:%M"))),
            ])
            for m in movs
        ]
        self._page.update()

    # ================================================================ #
    #  ABA ESTOQUE                                                      #
    # ================================================================ #

    def _build_estoque(self) -> ft.Container:
        self.dd_item_estoque = ft.Dropdown(
            label="Item",
            expand=True,
            options=self._opcoes_itens(),
        )
        self.dd_tipo_estoque = ft.Dropdown(
            label="Tipo",
            width=200,
            options=[
                ft.dropdown.Option(key=TipoMovimentacao.entrada, text="Entrada"),
                ft.dropdown.Option(key=TipoMovimentacao.ajuste, text="Ajuste"),
                ft.dropdown.Option(key=TipoMovimentacao.perda, text="Perda"),
            ],
        )
        self.field_qtd_estoque = ft.TextField(
            label="Quantidade",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="1",
        )
        self.field_desc_estoque = ft.TextField(
            label="Descrição (opcional)",
            expand=True,
        )

        self.msg_erro_estoque = ft.Text("", color=ft.Colors.RED_400, size=13)
        self.msg_ok_estoque = ft.Text("", color=ft.Colors.GREEN_600, size=13)

        btn_registrar = ft.ElevatedButton(
            "Registrar",
            icon=ft.Icons.SAVE,
            on_click=self._registrar_estoque,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )

        # Tabela histórico estoque
        self.tabela_estoque = ft.DataTable(
            expand=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            column_spacing=20,
            columns=[
                ft.DataColumn(ft.Text("Item", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Qtd", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        self._carregar_tabela_estoque()

        return ft.Container(
            content=ft.Column([
                ft.Text("Movimentação de Estoque", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.dd_item_estoque, self.dd_tipo_estoque, self.field_qtd_estoque]),
                ft.Row([self.field_desc_estoque]),
                self.msg_erro_estoque,
                self.msg_ok_estoque,
                ft.Row([btn_registrar]),
                ft.Container(height=16),
                ft.Text("Histórico de Estoque", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.tabela_estoque], scroll=ft.ScrollMode.AUTO),
            ]),
            padding=16,
        )

    def _registrar_estoque(self, e):
        self.msg_erro_estoque.value = ""
        self.msg_ok_estoque.value = ""

        if not self.dd_item_estoque.value:
            self.msg_erro_estoque.value = "Selecione um item."
            self._page.update()
            return

        if not self.dd_tipo_estoque.value:
            self.msg_erro_estoque.value = "Selecione o tipo de movimentação."
            self._page.update()
            return

        try:
            quantidade = int(self.field_qtd_estoque.value or 0)
            if quantidade <= 0:
                raise ValueError()
        except ValueError:
            self.msg_erro_estoque.value = "Quantidade inválida."
            self._page.update()
            return

        try:
            self.service.registrar(MovimentacaoBaseCreate(
                item_id=int(self.dd_item_estoque.value),
                quantidade=quantidade,
                tipo=TipoMovimentacao(self.dd_tipo_estoque.value),
                descricao=self.field_desc_estoque.value.strip() or None,
            ))
            self.msg_ok_estoque.value = "Movimentação registrada com sucesso!"
            self.dd_item_estoque.value = None
            self.dd_tipo_estoque.value = None
            self.field_qtd_estoque.value = "1"
            self.field_desc_estoque.value = ""
            self._carregar_tabela_estoque()
        except ValueError as ex:
            self.msg_erro_estoque.value = str(ex)
            self._page.update()

    def _carregar_tabela_estoque(self, movs=None):
        if movs is None:
            tipos = [TipoMovimentacao.entrada, TipoMovimentacao.ajuste, TipoMovimentacao.perda]
            movs = []
            for tipo in tipos:
                movs += self.service.listar_por_tipo(tipo)
            movs.sort(key=lambda m: m.data, reverse=True)

        itens = {i.id: i.nome for i in self.item_service.listar_todos()}

        labels = {
            TipoMovimentacao.entrada: "Entrada",
            TipoMovimentacao.ajuste: "Ajuste",
            TipoMovimentacao.perda: "Perda",
        }

        self.tabela_estoque.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(itens.get(m.item_id, str(m.item_id)))),
                ft.DataCell(ft.Text(labels.get(m.tipo, m.tipo))),
                ft.DataCell(ft.Text(str(m.quantidade))),
                ft.DataCell(ft.Text(m.descricao or "")),
                ft.DataCell(ft.Text(m.data.strftime("%d/%m/%Y %H:%M"))),
            ])
            for m in movs
        ]
        self._page.update()

    # ================================================================ #
    #  Helpers                                                          #
    # ================================================================ #

    def _opcoes_itens(self) -> list:
        itens = self.item_service.listar_todos()
        return [
            ft.dropdown.Option(key=str(i.id), text=f"{i.nome} (R$ {i.valor:.2f})")
            for i in itens
        ]

    def _opcoes_clientes(self) -> list:
        clientes = self.cliente_service.listar_todos()
        return [
            ft.dropdown.Option(key=str(c.id), text=c.nome)
            for c in clientes
        ]