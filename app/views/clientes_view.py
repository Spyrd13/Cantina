import flet as ft
from sqlmodel import Session

from app.services.cliente_services import ClienteService
from app.schemas.cliente_base import ClienteCreate, ClienteUpdate


class ClientesView(ft.Column):
    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)

        self.session = session
        self._page = page
        self.service = ClienteService(session)

        self._cliente_editando_id = None

        self._build()

    def _build(self):

        # ── Campos ─────────────────────────────────────────────

        self.field_nome = ft.TextField(
            label="Nome",
            expand=True,
        )

        self.field_telefone = ft.TextField(
            label="Telefone",
            width=200,
        )

        self.field_busca = ft.TextField(
            label="Buscar cliente...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._on_busca,
        )

        # ── Botões ────────────────────────────────────────────

        self.btn_salvar = ft.ElevatedButton(
            "Salvar",
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self._salvar,
        )

        self.btn_cancelar = ft.TextButton(
            "Cancelar",
            visible=False,
            on_click=self._cancelar,
        )

        # ── Mensagem erro ─────────────────────────────────────

        self.msg_erro = ft.Text(
            "",
            size=13,
            color=ft.Colors.RED_400,
        )

        # ── Tabela ────────────────────────────────────────────

        self.tabela = ft.Column()

        # ── Formulário ────────────────────────────────────────

        formulario = ft.Container(
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_200),

            content=ft.Column(
                controls=[
                    ft.Text(
                        "Clientes",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.Divider(),

                    ft.Row([
                        self.field_nome,
                        self.field_telefone,
                    ]),

                    self.msg_erro,

                    ft.Row([
                        self.btn_salvar,
                        self.btn_cancelar,
                    ]),
                ]
            ),
        )

        # ── Layout principal ─────────────────────────────────

        self.controls = [
            ft.Container(
                
                padding=10,

                content=ft.Column(
                    expand=True,

                    controls=[
                        formulario,

                        ft.Container(height=16),

                        self.field_busca,

                        ft.Container(height=8),

                        self.tabela,
                    ],
                ),
            )
        ]

        self._carregar_tabela()

    # ─────────────────────────────────────────────────────────
    # TABELA
    # ─────────────────────────────────────────────────────────

    def _carregar_tabela(self, clientes=None):

        if clientes is None:
            clientes = self.service.listar_todos()

        rows = []

        for c in clientes:

            row = ft.Container(
                padding=10,
                on_hover=self._hover_row,

                content=ft.Row(
                    spacing=8,

                    controls=[

                        # Nome
                        ft.Container(
                            expand=True,

                            content=ft.Text(
                                c.nome,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),

                        # Telefone
                        ft.Container(
                            width=220,

                            content=ft.Text(
                                c.telefone or "-",
                            ),
                        ),

                        # Ações
                        ft.Container(
                            width=120,

                            content=ft.Row(
                                spacing=0,

                                controls=[

                                    ft.IconButton(
                                        ft.Icons.EDIT,
                                        tooltip="Editar",
                                        icon_color=ft.Colors.BLUE_600,
                                        data=c.id,
                                        on_click=self._editar,
                                    ),

                                    ft.IconButton(
                                        ft.Icons.DELETE,
                                        tooltip="Remover",
                                        icon_color=ft.Colors.RED_400,
                                        data=c.id,
                                        on_click=self._confirmar_remover,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )

            rows.append(row)

            if c != clientes[-1]:
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
                        "Nenhum cliente encontrado.",
                        color=ft.Colors.GREY_500,
                    ),
                )
            ]

        # ── Header ───────────────────────────────────────────

        header = ft.Container(
            bgcolor=ft.Colors.GREY_100,
            padding=10,

            content=ft.Row(
                spacing=8,

                controls=[

                    ft.Container(
                        expand=True,

                        content=ft.Text(
                            "Nome",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=220,

                        content=ft.Text(
                            "Telefone",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=120,

                        content=ft.Text(
                            "Ações",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),
                ],
            ),
        )

        # ── Tabela final ─────────────────────────────────────

        tabela = ft.Container(
            
            bgcolor=ft.Colors.WHITE,
            border_radius=10,

            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
            ),

            content=ft.Column(
                spacing=0,

                controls=[

                    header,

                    ft.Container(
                        height=250,

                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                            controls=rows,
                        ),
                    ),
                ],
            ),
        )

        self.tabela.controls = [tabela]

        self._page.update()

    # ─────────────────────────────────────────────────────────
    # BUSCA
    # ─────────────────────────────────────────────────────────

    def _on_busca(self, e):

        termo = e.control.value.strip()

        clientes = (
            self.service.buscar_por_nome(termo)
            if termo
            else self.service.listar_todos()
        )

        self._carregar_tabela(clientes)

    # ─────────────────────────────────────────────────────────
    # FORMULÁRIO
    # ─────────────────────────────────────────────────────────

    def _limpar_form(self):

        self.field_nome.value = ""
        self.field_telefone.value = ""

        self.msg_erro.value = ""

        self._cliente_editando_id = None

        self.btn_cancelar.visible = False
        self.btn_salvar.text = "Salvar"

        self._page.update()

    def _cancelar(self, e):
        self._limpar_form()

    def _salvar(self, e):

        self.msg_erro.value = ""

        nome = self.field_nome.value.strip()
        telefone = self.field_telefone.value.strip()

        try:

            if self._cliente_editando_id is None:

                self.service.cadastrar(
                    ClienteCreate(
                        nome=nome,
                        telefone=telefone or None,
                    )
                )

            else:

                self.service.atualizar(
                    self._cliente_editando_id,

                    ClienteUpdate(
                        nome=nome,
                        telefone=telefone or None,
                    ),
                )

        except ValueError as ex:

            self.msg_erro.value = str(ex)

            self._page.update()

            return

        self._limpar_form()

        self._carregar_tabela()

    # ─────────────────────────────────────────────────────────
    # EDITAR
    # ─────────────────────────────────────────────────────────

    def _editar(self, e):

        cliente = self.service.buscar_por_id(e.control.data)

        self._cliente_editando_id = cliente.id

        self.field_nome.value = cliente.nome
        self.field_telefone.value = cliente.telefone or ""

        self.btn_salvar.text = "Atualizar"
        self.btn_cancelar.visible = True

        self.msg_erro.value = ""

        self._page.update()

    # ─────────────────────────────────────────────────────────
    # REMOVER
    # ─────────────────────────────────────────────────────────

    def _confirmar_remover(self, e):

        cliente_id = e.control.data

        def fechar(ev):

            dialog.open = False

            self._page.update()

        def confirmar(ev):

            try:

                self.service.remover(cliente_id)

                self._carregar_tabela()

            except ValueError as ex:

                self.msg_erro.value = str(ex)

                self._page.update()

            finally:

                dialog.open = False

                self._page.update()

        dialog = ft.AlertDialog(
            modal=True,

            title=ft.Text("Confirmar remoção"),

            content=ft.Text(
                "Tem certeza que deseja remover este cliente?"
            ),

            actions=[

                ft.TextButton(
                    "Cancelar",
                    on_click=fechar,
                ),

                ft.ElevatedButton(
                    "Remover",
                    bgcolor=ft.Colors.RED_400,
                    color=ft.Colors.WHITE,
                    on_click=confirmar,
                ),
            ],
        )

        self._page.overlay.append(dialog)

        dialog.open = True

        self._page.update()

    # ─────────────────────────────────────────────────────────
    # HOVER
    # ─────────────────────────────────────────────────────────

    def _hover_row(self, e):

        e.control.bgcolor = (
            ft.Colors.GREY_50
            if e.data == "true"
            else None
        )

        e.control.update()