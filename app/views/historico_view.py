import json
import flet as ft
from sqlmodel import Session

from app.services.historico_services import HistoricoService


class HistoricoView(ft.Column):
    def __init__(
        self,
        session: Session,
        page: ft.Page,
    ):
        super().__init__(expand=True)

        self._page = page
        self.service = HistoricoService(session)
        self.limite = 100
        self._montado = False

        self._build()

    # ==================================================
    # LIFECYCLE
    # ==================================================

    def did_mount(self):
        self._montado = True
        self._carregar()

    # ==================================================
    # BUILD
    # ==================================================

    def _build(self):

        self.tf_busca = ft.TextField(
            label="Buscar descrição",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._carregar,
        )

        self.dd_entidade = ft.Dropdown(
            label="Categoria",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option("todos"),
                ft.dropdown.Option("cliente"),
                ft.dropdown.Option("item"),
                ft.dropdown.Option("financeiro"),
                ft.dropdown.Option("estoque"),
                ft.dropdown.Option("venda"),
            ],
        )
        self.dd_entidade.on_change = self._carregar

        self.dd_operacao = ft.Dropdown(
            label="Operação",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option("todos"),
                ft.dropdown.Option("criacao"),
                ft.dropdown.Option("edicao"),
                ft.dropdown.Option("exclusao"),
                ft.dropdown.Option("entrada"),
                ft.dropdown.Option("ajuste"),
                ft.dropdown.Option("pagamento"),
                ft.dropdown.Option("perda"),
            ],
        )
        self.dd_operacao.on_change = self._carregar

        self.tabela = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.controls = [
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.Text(
                            "Histórico / Auditoria",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                self.tf_busca,
                                self.dd_entidade,
                                self.dd_operacao,
                                ft.FilledButton(
                                    "Atualizar",
                                    icon=ft.Icons.REFRESH,
                                    on_click=self._carregar,
                                ),
                            ]
                        ),
                        ft.Container(
                            expand=True,
                            border=ft.Border(
                                left=ft.BorderSide(1, ft.Colors.GREY_300),
                                top=ft.BorderSide(1, ft.Colors.GREY_300),
                                right=ft.BorderSide(1, ft.Colors.GREY_300),
                                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
                            ),
                            border_radius=10,
                            content=self.tabela,
                        ),
                    ],
                ),
            )
        ]

    # ==================================================
    # CARREGAR
    # ==================================================

    def _carregar(self, e=None):

        entidade = None
        operacao = None
        descricao = None

        if self.dd_entidade.value and self.dd_entidade.value != "todos":
            entidade = self.dd_entidade.value

        if self.dd_operacao.value and self.dd_operacao.value != "todos":
            operacao = self.dd_operacao.value

        if self.tf_busca.value:
            descricao = self.tf_busca.value.strip()

        registros = self.service.buscar(
            limite=self.limite,
            entidade=entidade,
            operacao=operacao,
            descricao=descricao,
        )

        linhas = []

        linhas.append(
            ft.Container(
                bgcolor=ft.Colors.GREY_200,
                padding=10,
                content=ft.Row(
                    controls=[
                        ft.Text("Data", width=170, weight=ft.FontWeight.BOLD),
                        ft.Text("Categoria", width=120, weight=ft.FontWeight.BOLD),
                        ft.Text("Operação", width=120, weight=ft.FontWeight.BOLD),
                        ft.Text("Descrição", expand=True, weight=ft.FontWeight.BOLD),
                        ft.Text("ID", width=80, weight=ft.FontWeight.BOLD),
                        ft.Text("", width=50),
                    ]
                ),
            )
        )

        if not registros:
            linhas.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum registro encontrado."),
                )
            )

        for h in registros:
            linhas.append(
                ft.Container(
                    padding=10,
                    border=ft.Border(
                        bottom=ft.BorderSide(1, ft.Colors.GREY_300)
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                h.data.strftime("%d/%m/%Y %H:%M"),
                                width=170,
                            ),
                            ft.Text(h.entidade.capitalize(), width=120),
                            ft.Text(h.operacao.capitalize(), width=120),
                            ft.Text(
                                h.descricao,
                                expand=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(str(h.entidade_id), width=80),
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                tooltip="Detalhes",
                                data=h,
                                on_click=self._detalhes,
                            ),
                        ]
                    ),
                )
            )

        self.tabela.controls = linhas
        if self._montado:
            self.update()

    # ==================================================
    # DETALHES
    # ==================================================

    def _detalhes(self, e):

        h = e.control.data

        antes = "-"
        depois = "-"

        if h.valor_antes:
            try:
                antes = json.dumps(
                    json.loads(h.valor_antes),
                    indent=4,
                    ensure_ascii=False,
                )
            except Exception:
                antes = str(h.valor_antes)

        if h.valor_depois:
            try:
                depois = json.dumps(
                    json.loads(h.valor_depois),
                    indent=4,
                    ensure_ascii=False,
                )
            except Exception:
                depois = str(h.valor_depois)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalhes do Histórico"),
            content=ft.Container(
                width=700,
                height=500,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text(f"Data: {h.data.strftime('%d/%m/%Y %H:%M:%S')}"),
                        ft.Text(f"Categoria: {h.entidade}"),
                        ft.Text(f"Operação: {h.operacao}"),
                        ft.Text(f"Descrição: {h.descricao}"),
                        ft.Divider(),
                        ft.Text("ANTES", weight=ft.FontWeight.BOLD),
                        ft.Text(antes, selectable=True),
                        ft.Divider(),
                        ft.Text("DEPOIS", weight=ft.FontWeight.BOLD),
                        ft.Text(depois, selectable=True),
                    ],
                ),
            ),
            actions=[
                ft.TextButton(
                    "Fechar",
                    on_click=lambda _: self._page.pop_dialog(),
                )
            ],
        )

        self._page.show_dialog(dlg)