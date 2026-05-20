import flet as ft
from sqlmodel import Session

from app.services.movimentacao_services import MovimentacaoService
from app.services.financeiro_services import FinanceiroService
from app.services.item_services import ItemService
from app.services.cliente_services import ClienteService

from app.utils.enums import (
    TipoMovimentacao,
    TipoFinanceiro,
)


class HistoricoView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)

        self.session = session
        self._page = page

        self.mov_service = MovimentacaoService(session)
        self.fin_service = FinanceiroService(session)
        self.item_service = ItemService(session)
        self.cliente_service = ClienteService(session)

        self._itens_map = {}
        self._clientes_map = {}

        self._build()

    # ==========================================================
    # BUILD
    # ==========================================================

    def _build(self):

        self._carregar_maps()

        # ======================================================
        # FILTROS VENDAS
        # ======================================================

        self.field_busca_vendas = ft.TextField(
            label="Buscar venda por item",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
        )

        self.field_busca_vendas.on_change = (
            self._carregar_historico_vendas
        )

        # ======================================================
        # FILTROS ESTOQUE
        # ======================================================

        self.field_busca_estoque = ft.TextField(
            label="Buscar estoque por item",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
        )

        self.field_busca_estoque.on_change = (
            self._carregar_historico_estoque
        )

        self.dd_tipo_movimentacao = ft.Dropdown(
            label="Tipo movimentação",
            width=220,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option("entrada", "Entrada"),
                ft.dropdown.Option("ajuste", "Ajuste"),
                ft.dropdown.Option("perda", "Perda"),
            ],
        )

        self.dd_tipo_movimentacao.on_change = (
            self._carregar_historico_estoque
        )

        # ======================================================
        # FILTROS FINANCEIRO
        # ======================================================

        self.field_busca_financeiro = ft.TextField(
            label="Buscar financeiro",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
        )

        self.field_busca_financeiro.on_change = (
            self._carregar_historico_financeiro
        )

        self.dd_tipo_financeiro = ft.Dropdown(
            label="Tipo financeiro",
            width=220,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option(
                    TipoFinanceiro.receita.value,
                    "Receita",
                ),
                ft.dropdown.Option(
                    TipoFinanceiro.despesa.value,
                    "Despesa",
                ),
            ],
        )

        self.dd_tipo_financeiro.on_change = (
            self._carregar_historico_financeiro
        )

        # ======================================================
        # TABELAS
        # ======================================================

        self.tabela_vendas = ft.Column()
        self.tabela_estoque = ft.Column()
        self.tabela_financeiro = ft.Column()

        self.controls = [
            ft.Container(
                expand=True,
                padding=24,
                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[

                        ft.Text(
                            "Histórico Geral",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Divider(),

                        # ======================================
                        # VENDAS
                        # ======================================

                        ft.Text(
                            "Histórico de Vendas",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Row([
                            self.field_busca_vendas,
                        ]),

                        self.tabela_vendas,

                        ft.Container(height=30),

                        # ======================================
                        # ESTOQUE
                        # ======================================

                        ft.Text(
                            "Histórico de Estoque",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Row([
                            self.field_busca_estoque,
                            self.dd_tipo_movimentacao,
                        ]),

                        self.tabela_estoque,

                        ft.Container(height=30),

                        # ======================================
                        # FINANCEIRO
                        # ======================================

                        ft.Text(
                            "Histórico Financeiro",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Row([
                            self.field_busca_financeiro,
                            self.dd_tipo_financeiro,
                        ]),

                        self.tabela_financeiro,
                    ],
                ),
            )
        ]

        self._carregar_historico_vendas()
        self._carregar_historico_estoque()
        self._carregar_historico_financeiro()

    # ==========================================================
    # VENDAS
    # ==========================================================

    def _carregar_historico_vendas(self, e=None):

        busca = (
            self.field_busca_vendas.value.strip().lower()
            if self.field_busca_vendas.value
            else ""
        )

        movs = self.mov_service.listar_por_tipo(
            TipoMovimentacao.saida
        )

        rows = []

        for mov in movs:

            item_nome = self._itens_map.get(
                mov.item_id,
                "-"
            )

            cliente_nome = self._clientes_map.get(
                mov.cliente_id,
                "-"
            )

            if busca:
                if busca not in item_nome.lower():
                    continue

            total = mov.valor_unitario * mov.quantidade

            rows.append(
                self._criar_row(
                    [
                        (item_nome, True),
                        (mov.quantidade, False),
                        (f"R$ {mov.valor_unitario:.2f}", False),
                        (f"R$ {total:.2f}", False),
                        (
                            cliente_nome
                            if mov.cliente_id
                            else "Pago"
                        ,
                            False
                        ),
                        (
                            mov.data.strftime("%d/%m/%Y %H:%M"),
                            False,
                        ),
                    ]
                )
            )

        header = self._criar_header(
            [
                ("Item", True),
                ("Qtd", False),
                ("Valor", False),
                ("Total", False),
                ("Cliente", False),
                ("Data", False),
            ]
        )

        self._renderizar_tabela(
            self.tabela_vendas,
            header,
            rows,
        )

    # ==========================================================
    # ESTOQUE
    # ==========================================================

    def _carregar_historico_estoque(self, e=None):

        busca = (
            self.field_busca_estoque.value.strip().lower()
            if self.field_busca_estoque.value
            else ""
        )

        tipo = self.dd_tipo_movimentacao.value

        movs = self.mov_service.listar_todas()

        rows = []

        for mov in movs:

            if mov.tipo == TipoMovimentacao.saida:
                continue

            if tipo != "todos":
                if mov.tipo.value != tipo:
                    continue

            item_nome = self._itens_map.get(
                mov.item_id,
                "-"
            )

            if busca:
                if busca not in item_nome.lower():
                    continue

            rows.append(
                self._criar_row(
                    [
                        (item_nome, True),
                        (mov.tipo.value.capitalize(), False),
                        (mov.quantidade, False),
                        (
                            f"R$ {mov.valor_pago:.2f}"
                            if mov.valor_pago
                            else "-"
                        ,
                            False
                        ),
                        (
                            mov.descricao or "-",
                            True,
                        ),
                        (
                            mov.data.strftime("%d/%m/%Y %H:%M"),
                            False,
                        ),
                    ]
                )
            )

        header = self._criar_header(
            [
                ("Item", True),
                ("Tipo", False),
                ("Qtd", False),
                ("Valor Pago", False),
                ("Descrição", True),
                ("Data", False),
            ]
        )

        self._renderizar_tabela(
            self.tabela_estoque,
            header,
            rows,
        )

    # ==========================================================
    # FINANCEIRO
    # ==========================================================

    def _carregar_historico_financeiro(self, e=None):

        busca = (
            self.field_busca_financeiro.value.strip().lower()
            if self.field_busca_financeiro.value
            else ""
        )

        tipo = self.dd_tipo_financeiro.value

        registros = self.fin_service.listar_todos()

        rows = []

        for reg in registros:

            if tipo != "todos":
                if reg.tipo.value != tipo:
                    continue

            descricao = reg.descricao or "-"

            if busca:
                if busca not in descricao.lower():
                    continue

            rows.append(
                self._criar_row(
                    [
                        (
                            reg.tipo.value.capitalize(),
                            False,
                        ),
                        (
                            reg.pagamento.value.capitalize(),
                            False,
                        ),
                        (
                            f"R$ {reg.valor:.2f}",
                            False,
                        ),
                        (
                            descricao,
                            True,
                        ),
                        (
                            reg.data.strftime("%d/%m/%Y %H:%M"),
                            False,
                        ),
                    ]
                )
            )

        header = self._criar_header(
            [
                ("Tipo", False),
                ("Pagamento", False),
                ("Valor", False),
                ("Descrição", True),
                ("Data", False),
            ]
        )

        self._renderizar_tabela(
            self.tabela_financeiro,
            header,
            rows,
        )

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _renderizar_tabela(
        self,
        tabela_ref,
        header,
        rows,
    ):

        if not rows:
            rows = [
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "Nenhum registro encontrado.",
                        color=ft.Colors.GREY_500,
                    ),
                )
            ]

        tabela = ft.Container(
            border=ft.Border.all(
                1,
                ft.Colors.GREY_300,
            ),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column(
                spacing=0,
                controls=[
                    header,

                    ft.Container(
                        height=350,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                            controls=rows,
                        ),
                    ),
                ],
            ),
        )

        tabela_ref.controls = [tabela]

        self._page.update()

    def _criar_header(self, colunas):

        controls = []

        for texto, expand in colunas:

            controls.append(
                ft.Container(
                    expand=expand,
                    width=None if expand else 140,
                    padding=10,
                    content=ft.Text(
                        texto,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_700,
                    ),
                )
            )

        return ft.Container(
            bgcolor=ft.Colors.GREY_100,
            content=ft.Row(
                spacing=0,
                controls=controls,
            ),
        )

    def _criar_row(self, colunas):

        controls = []

        for texto, expand in colunas:

            controls.append(
                ft.Container(
                    expand=expand,
                    width=None if expand else 140,
                    padding=10,
                    content=ft.Text(
                        str(texto),
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                )
            )

        return ft.Container(
            on_hover=self._hover_row,
            content=ft.Row(
                spacing=0,
                controls=controls,
            ),
        )

    def _hover_row(self, e):

        e.control.bgcolor = (
            ft.Colors.GREY_50
            if e.data == "true"
            else None
        )

        e.control.update()

    def _carregar_maps(self):

        itens = self.item_service.listar_todos()
        clientes = self.cliente_service.listar_todos()

        self._itens_map = {
            i.id: i.nome
            for i in itens
        }

        self._clientes_map = {
            c.id: c.nome
            for c in clientes
        }