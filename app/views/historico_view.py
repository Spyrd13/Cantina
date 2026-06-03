import flet as ft
from sqlmodel import Session
from datetime import datetime, timedelta

from app.services.movimentacao_services import MovimentacaoService
from app.services.financeiro_services import FinanceiroService
from app.services.item_services import ItemService
from app.services.cliente_services import ClienteService

from app.utils.enums import (
    TipoMovimentacao,
    TipoFinanceiro,
    TipoPagamento,
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

        self.dp_inicio_vendas = ft.DatePicker(
            field_label_text="Data início",
        )

        self.dp_fim_vendas = ft.DatePicker(
            field_label_text="Data fim",
        )

        self.dd_mes_vendas = ft.Dropdown(
            label="Mês",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option("01", "Janeiro"),
                ft.dropdown.Option("02", "Fevereiro"),
                ft.dropdown.Option("03", "Março"),
                ft.dropdown.Option("04", "Abril"),
                ft.dropdown.Option("05", "Maio"),
                ft.dropdown.Option("06", "Junho"),
                ft.dropdown.Option("07", "Julho"),
                ft.dropdown.Option("08", "Agosto"),
                ft.dropdown.Option("09", "Setembro"),
                ft.dropdown.Option("10", "Outubro"),
                ft.dropdown.Option("11", "Novembro"),
                ft.dropdown.Option("12", "Dezembro"),
            ],
        )

        ano_atual = datetime.now().year
        self.dd_ano_vendas = ft.Dropdown(
            label="Ano",
            width=120,
            value=str(ano_atual),
            options=[
                ft.dropdown.Option(str(ano), str(ano))
                for ano in range(ano_atual - 2, ano_atual + 2)
            ],
        )

        self.field_busca_vendas.on_change = (
            self._carregar_historico_vendas
        )
        self.dp_inicio_vendas.on_change = self._carregar_historico_vendas
        self.dp_fim_vendas.on_change = self._carregar_historico_vendas
        self.dd_mes_vendas.on_change = self._carregar_historico_vendas
        self.dd_ano_vendas.on_change = self._carregar_historico_vendas

        self.btn_filtrar_vendas = ft.FilledButton(
            "Filtrar",
            icon=ft.Icons.FILTER_ALT,
            on_click=self._carregar_historico_vendas,
        )

        # ======================================================
        # FILTROS ESTOQUE
        # ======================================================

        self.field_busca_estoque = ft.TextField(
            label="Buscar estoque por item",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
        )

        self.dp_inicio_estoque = ft.DatePicker(
            field_label_text="Data início",
        )

        self.dp_fim_estoque = ft.DatePicker(
            field_label_text="Data fim",
        )

        self.dd_mes_estoque = ft.Dropdown(
            label="Mês",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option("01", "Janeiro"),
                ft.dropdown.Option("02", "Fevereiro"),
                ft.dropdown.Option("03", "Março"),
                ft.dropdown.Option("04", "Abril"),
                ft.dropdown.Option("05", "Maio"),
                ft.dropdown.Option("06", "Junho"),
                ft.dropdown.Option("07", "Julho"),
                ft.dropdown.Option("08", "Agosto"),
                ft.dropdown.Option("09", "Setembro"),
                ft.dropdown.Option("10", "Outubro"),
                ft.dropdown.Option("11", "Novembro"),
                ft.dropdown.Option("12", "Dezembro"),
            ],
        )

        self.dd_ano_estoque = ft.Dropdown(
            label="Ano",
            width=120,
            value=str(ano_atual),
            options=[
                ft.dropdown.Option(str(ano), str(ano))
                for ano in range(ano_atual - 2, ano_atual + 2)
            ],
        )

        self.field_busca_estoque.on_change = (
            self._carregar_historico_estoque
        )
        self.dp_inicio_estoque.on_change = self._carregar_historico_estoque
        self.dp_fim_estoque.on_change = self._carregar_historico_estoque
        self.dd_mes_estoque.on_change = self._carregar_historico_estoque
        self.dd_ano_estoque.on_change = self._carregar_historico_estoque

        self.btn_filtrar_estoque = ft.FilledButton(
            "Filtrar",
            icon=ft.Icons.FILTER_ALT,
            on_click=self._carregar_historico_estoque,
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

        self.dp_inicio_financeiro = ft.DatePicker(
            field_label_text="Data início",
        )

        self.dp_fim_financeiro = ft.DatePicker(
            field_label_text="Data fim",
        )

        self.dd_mes_financeiro = ft.Dropdown(
            label="Mês",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option("01", "Janeiro"),
                ft.dropdown.Option("02", "Fevereiro"),
                ft.dropdown.Option("03", "Março"),
                ft.dropdown.Option("04", "Abril"),
                ft.dropdown.Option("05", "Maio"),
                ft.dropdown.Option("06", "Junho"),
                ft.dropdown.Option("07", "Julho"),
                ft.dropdown.Option("08", "Agosto"),
                ft.dropdown.Option("09", "Setembro"),
                ft.dropdown.Option("10", "Outubro"),
                ft.dropdown.Option("11", "Novembro"),
                ft.dropdown.Option("12", "Dezembro"),
            ],
        )

        self.dd_ano_financeiro = ft.Dropdown(
            label="Ano",
            width=120,
            value=str(ano_atual),
            options=[
                ft.dropdown.Option(str(ano), str(ano))
                for ano in range(ano_atual - 2, ano_atual + 2)
            ],
        )

        self.field_busca_financeiro.on_change = (
            self._carregar_historico_financeiro
        )
        self.dp_inicio_financeiro.on_change = self._carregar_historico_financeiro
        self.dp_fim_financeiro.on_change = self._carregar_historico_financeiro
        self.dd_mes_financeiro.on_change = self._carregar_historico_financeiro
        self.dd_ano_financeiro.on_change = self._carregar_historico_financeiro

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

        self.btn_filtrar_financeiro = ft.FilledButton(
            "Filtrar",
            icon=ft.Icons.FILTER_ALT,
            on_click=self._carregar_historico_financeiro,
        )

        self.dd_pagamento_financeiro = ft.Dropdown(
            label="Pagamento",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option(TipoPagamento.pix.value, "Pix"),
                ft.dropdown.Option(TipoPagamento.dinheiro.value, "Dinheiro"),
                ft.dropdown.Option(TipoPagamento.debito.value, "Débito"),
                ft.dropdown.Option(TipoPagamento.credito.value, "Crédito"),
            ],
        )

        self.dd_pagamento_financeiro.on_change = (
            self._carregar_historico_financeiro
        )

        # ======================================================
        # FILTROS PENDURADOS
        # ======================================================

        self.dd_cliente_pendurados = ft.Dropdown(
            label="Cliente",
            expand=True,
            value="todos",
            options=[ft.dropdown.Option("todos", "Todos os clientes")] + [
                ft.dropdown.Option(str(c.id), c.nome)
                for c in self.cliente_service.listar_todos()
            ],
        )

        self.dp_inicio_pendurados = ft.DatePicker(
            field_label_text="Data início",
        )

        self.dp_fim_pendurados = ft.DatePicker(
            field_label_text="Data fim",
        )

        self.btn_filtrar_pendurados = ft.FilledButton(
            "Filtrar",
            icon=ft.Icons.FILTER_ALT,
            on_click=self._carregar_historico_pendurados,
        )

        self.dd_cliente_pendurados.on_change = (
            self._carregar_historico_pendurados
        )
        self.dp_inicio_pendurados.on_change = self._carregar_historico_pendurados
        self.dp_fim_pendurados.on_change = self._carregar_historico_pendurados

        # ======================================================
        # TABELAS
        # ======================================================

        self.tabela_vendas = ft.Column()
        self.tabela_pendurados = ft.Column()
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
                            self.btn_filtrar_vendas,
                        ]),
                        ft.Row([
                            self.dp_inicio_vendas,
                            self.dp_fim_vendas,
                            self.dd_mes_vendas,
                            self.dd_ano_vendas,
                        ]),

                        self.tabela_vendas,

                        ft.Container(height=30),

                        # ======================================
                        # PENDURADOS
                        # ======================================

                        ft.Text(
                            "Histórico de Pendurados",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Row([
                            self.dd_cliente_pendurados,
                            self.btn_filtrar_pendurados,
                        ]),
                        ft.Row([
                            self.dp_inicio_pendurados,
                            self.dp_fim_pendurados,
                        ]),

                        self.tabela_pendurados,

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
                            self.btn_filtrar_estoque,
                        ]),
                        ft.Row([
                            self.dp_inicio_estoque,
                            self.dp_fim_estoque,
                            self.dd_mes_estoque,
                            self.dd_ano_estoque,
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
                            self.dd_pagamento_financeiro,
                            self.btn_filtrar_financeiro,
                        ]),
                        ft.Row([
                            self.dp_inicio_financeiro,
                            self.dp_fim_financeiro,
                            self.dd_mes_financeiro,
                            self.dd_ano_financeiro,
                        ]),

                        self.tabela_financeiro,
                    ],
                ),
            )
        ]

        self._carregar_historico_vendas()
        self._carregar_historico_pendurados()
        self._carregar_historico_estoque()
        self._carregar_historico_financeiro()

    def _get_periodo(self, data_inicio, data_fim, mes, ano):
        if data_inicio.value or data_fim.value:
            inicio = datetime.combine(
                data_inicio.value,
                datetime.min.time(),
            ) if data_inicio.value else datetime.min
            fim = datetime.combine(
                data_fim.value,
                datetime.max.time(),
            ) if data_fim.value else datetime.max
            return inicio, fim

        if mes.value != "todos":
            mes_num = int(mes.value)
            ano_num = int(ano.value)
            inicio = datetime(ano_num, mes_num, 1)
            if mes_num == 12:
                fim = datetime(ano_num + 1, 1, 1)
            else:
                fim = datetime(ano_num, mes_num + 1, 1)
            return inicio, fim

        return None, None

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

        inicio, fim = self._get_periodo(
            self.dp_inicio_vendas,
            self.dp_fim_vendas,
            self.dd_mes_vendas,
            self.dd_ano_vendas,
        )

        rows = []

        for mov in movs:

            if inicio and fim:
                if mov.data < inicio or mov.data >= fim:
                    continue

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
    # PENDURADOS
    # ==========================================================

    def _carregar_historico_pendurados(self, e=None):
        
        cliente_id = None
        if self.dd_cliente_pendurados.value != "todos":
            cliente_id = int(self.dd_cliente_pendurados.value)
        
        inicio = None
        fim = None
        
        if self.dp_inicio_pendurados.value and self.dp_fim_pendurados.value:
            inicio = datetime.combine(
                self.dp_inicio_pendurados.value,
                datetime.min.time(),
            )
            fim = datetime.combine(
                self.dp_fim_pendurados.value,
                datetime.max.time(),
            )
        elif self.dp_inicio_pendurados.value:
            inicio = datetime.combine(
                self.dp_inicio_pendurados.value,
                datetime.min.time(),
            )
        elif self.dp_fim_pendurados.value:
            fim = datetime.combine(
                self.dp_fim_pendurados.value,
                datetime.max.time(),
            )
        
        movs = self.mov_service.listar_pendurados(
            inicio=inicio,
            fim=fim,
            cliente_id=cliente_id,
        )
        
        rows = []
        total_geral = 0.0
        
        for mov in movs:
            item_nome = self._itens_map.get(mov.item_id, "-")
            cliente_nome = self._clientes_map.get(mov.cliente_id, "-")
            
            total = mov.valor_unitario * mov.quantidade
            total_geral += total
            
            rows.append(
                self._criar_row(
                    [
                        (item_nome, True),
                        (mov.quantidade, False),
                        (f"R$ {mov.valor_unitario:.2f}", False),
                        (f"R$ {total:.2f}", False),
                        (cliente_nome, False),
                        (mov.data.strftime("%d/%m/%Y %H:%M"), False),
                    ]
                )
            )
        
        if rows:
            total_row = ft.Container(
                bgcolor=ft.Colors.BLUE_50,
                content=ft.Row(
                    spacing=0,
                    controls=[
                        ft.Container(
                            expand=True,
                            width=None,
                            padding=10,
                            content=ft.Text(
                                "TOTAL",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),
                        ft.Container(width=140, padding=10, content=ft.Text("")),
                        ft.Container(width=140, padding=10, content=ft.Text("")),
                        ft.Container(width=140, padding=10, content=ft.Text("")),
                        ft.Container(
                            width=140,
                            padding=10,
                            content=ft.Text(
                                f"R$ {total_geral:.2f}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_700,
                            ),
                        ),
                        ft.Container(width=140, padding=10, content=ft.Text("")),
                    ],
                ),
            )
            rows.append(total_row)
        
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
            self.tabela_pendurados,
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

        inicio, fim = self._get_periodo(
            self.dp_inicio_estoque,
            self.dp_fim_estoque,
            self.dd_mes_estoque,
            self.dd_ano_estoque,
        )

        rows = []

        for mov in movs:

            if mov.tipo == TipoMovimentacao.saida:
                continue

            if inicio and fim:
                if mov.data < inicio or mov.data >= fim:
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

        inicio, fim = self._get_periodo(
            self.dp_inicio_financeiro,
            self.dp_fim_financeiro,
            self.dd_mes_financeiro,
            self.dd_ano_financeiro,
        )

        rows = []

        for reg in registros:

            if inicio and fim:
                if reg.data < inicio or reg.data >= fim:
                    continue

            if tipo != "todos":
                if reg.tipo.value != tipo:
                    continue

            pagamento = self.dd_pagamento_financeiro.value
            if pagamento != "todos":
                if reg.pagamento.value != pagamento:
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