import flet as ft
import logging
from datetime import datetime
from sqlmodel import Session

from app.services.historico_services import HistoricoService


class HistoricoView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)

        self.session = session
        self._page = page

        try:
            self.historico_service = HistoricoService(session)
            self._build()
        except Exception as ex:
            logging.getLogger(__name__).exception("Erro ao construir HistoricoView: %s", ex)
            self.controls = [
                ft.Container(
                    padding=24,
                    content=ft.Column(controls=[
                        ft.Text("Erro ao carregar o Histórico", color=ft.Colors.RED),
                        ft.Text(str(ex)),
                    ]),
                )
            ]

    # ==========================================================
    # BUILD
    # ==========================================================

    def _build(self):
        self._limite = 50
        ano_atual = datetime.now().year

        # ======================================================
        # FILTROS
        # ======================================================

        self.field_busca = ft.TextField(
            label="Buscar na descrição",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._carregar,
        )

        self.dd_entidade = ft.Dropdown(
            label="Categoria",
            width=200,
            value="todos",
            on_select=self._carregar,
            options=[
                ft.dropdown.Option("todos", "Todas"),
                ft.dropdown.Option("venda", "Vendas"),
                ft.dropdown.Option("estoque", "Estoque"),
                ft.dropdown.Option("financeiro", "Financeiro"),
                ft.dropdown.Option("cliente", "Clientes"),
                ft.dropdown.Option("item", "Itens"),
            ],
        )

        self.dd_operacao = ft.Dropdown(
            label="Operação",
            width=200,
            value="todos",
            on_select=self._carregar,
            options=[
                ft.dropdown.Option("todos", "Todas"),
                ft.dropdown.Option("criacao", "Criação"),
                ft.dropdown.Option("edicao", "Edição"),
                ft.dropdown.Option("exclusao", "Exclusão"),
                ft.dropdown.Option("pagamento", "Pagamento"),
                ft.dropdown.Option("entrada", "Entrada"),
                ft.dropdown.Option("ajuste", "Ajuste"),
                ft.dropdown.Option("perda", "Perda"),
            ],
        )

        self.dp_inicio = ft.DatePicker(
            field_label_text="Data início",
            on_change=self._carregar,
        )

        self.dp_fim = ft.DatePicker(
            field_label_text="Data fim",
            on_change=self._carregar,
        )

        self.dd_mes = ft.Dropdown(
            label="Mês",
            width=160,
            value="todos",
            on_select=self._carregar,
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

        self.dd_ano = ft.Dropdown(
            label="Ano",
            width=120,
            value=str(ano_atual),
            on_select=self._carregar,
            options=[
                ft.dropdown.Option(str(ano), str(ano))
                for ano in range(ano_atual - 2, ano_atual + 2)
            ],
        )

        self.btn_filtrar = ft.FilledButton(
            "Filtrar",
            icon=ft.Icons.FILTER_ALT,
            on_click=self._carregar,
        )

        # ======================================================
        # TABELA
        # ======================================================

        self.tabela = ft.Column()

        self.btn_carregar_mais = ft.TextButton(
            "Carregar mais",
            on_click=self._carregar_mais,
        )

        self.controls = [
            ft.Container(
                expand=True,
                padding=24,
                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text(
                            "Histórico / Auditoria",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Row([
                            self.field_busca,
                            self.dd_entidade,
                            self.dd_operacao,
                            self.btn_filtrar,
                        ]),
                        ft.Row([
                            self.dp_inicio,
                            self.dp_fim,
                            self.dd_mes,
                            self.dd_ano,
                        ]),
                        self.tabela,
                        self.btn_carregar_mais,
                    ],
                ),
            )
        ]

        self._carregar()

    # ==========================================================
    # CARREGAR
    # ==========================================================

    def _carregar(self, e=None):
        try:
            busca = self.field_busca.value.strip().lower() if self.field_busca.value else ""
            entidade = self.dd_entidade.value
            operacao = self.dd_operacao.value
            inicio, fim = self._get_periodo()

            registros = self.historico_service.listar_tudo(limite=self._limite)

            rows = []

            for reg in registros:

                if entidade != "todos" and reg.entidade != entidade:
                    continue

                if operacao != "todos" and reg.operacao != operacao:
                    continue

                if inicio and fim:
                    if reg.data < inicio or reg.data >= fim:
                        continue

                if busca and busca not in reg.descricao.lower():
                    continue

                rows.append(self._criar_row([
                    (reg.data.strftime("%d/%m/%Y %H:%M"), False),
                    (reg.entidade.capitalize(), False),
                    (reg.operacao.capitalize(), False),
                    (reg.descricao, True),
                    (str(reg.entidade_id), False),
                ]))

            header = self._criar_header([
                ("Data", False),
                ("Categoria", False),
                ("Operação", False),
                ("Descrição", True),
                ("ID Ref.", False),
            ])

            self._renderizar_tabela(header, rows)

        except Exception as ex:
            logging.getLogger(__name__).exception("Erro ao carregar histórico: %s", ex)
            self.tabela.controls = [
                ft.Container(padding=20, content=ft.Text("Erro ao carregar histórico."))
            ]
            self._page.update()

    # ==========================================================
    # PERÍODO
    # ==========================================================

    def _get_periodo(self):
        if self.dp_inicio.value or self.dp_fim.value:
            inicio = datetime.combine(self.dp_inicio.value, datetime.min.time()) if self.dp_inicio.value else datetime.min
            fim = datetime.combine(self.dp_fim.value, datetime.max.time()) if self.dp_fim.value else datetime.max
            return inicio, fim

        if self.dd_mes.value != "todos":
            mes_num = int(self.dd_mes.value)
            ano_num = int(self.dd_ano.value)
            inicio = datetime(ano_num, mes_num, 1)
            fim = datetime(ano_num + 1, 1, 1) if mes_num == 12 else datetime(ano_num, mes_num + 1, 1)
            return inicio, fim

        return None, None

    # ==========================================================
    # HELPERS DE UI
    # ==========================================================

    def _renderizar_tabela(self, header, rows):
        if not rows:
            rows = [
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum registro encontrado.", color=ft.Colors.GREY_500),
                )
            ]

        self.tabela.controls = [
            ft.Container(
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        header,
                        ft.Container(
                            height=500,
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                spacing=0,
                                controls=rows,
                            ),
                        ),
                    ],
                ),
            )
        ]

        self._page.update()

    def _criar_header(self, colunas):
        return ft.Container(
            bgcolor=ft.Colors.GREY_100,
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        expand=expand,
                        width=None if expand else 160,
                        padding=10,
                        content=ft.Text(
                            texto,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    )
                    for texto, expand in colunas
                ],
            ),
        )

    def _criar_row(self, colunas):
        return ft.Container(
            on_hover=self._hover_row,
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        expand=expand,
                        width=None if expand else 160,
                        padding=10,
                        content=ft.Text(
                            str(texto),
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    )
                    for texto, expand in colunas
                ],
            ),
        )

    def _hover_row(self, e):
        e.control.bgcolor = ft.Colors.GREY_50 if e.data == "true" else None
        e.control.update()

    def _carregar_mais(self, e=None):
        self._limite += 50
        self._carregar()