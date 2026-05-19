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
        self._build()

    def _build(self):
        self.field_nome = ft.TextField(label="Nome", expand=True)
        self.field_telefone = ft.TextField(label="Telefone", width=200)
        self.field_busca = ft.TextField(
            label="Buscar cliente...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._on_busca,
        )

        self.btn_salvar = ft.ElevatedButton(
            "Salvar",
            icon=ft.Icons.SAVE,
            on_click=self._salvar,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )
        self.btn_cancelar = ft.TextButton(
            "Cancelar",
            on_click=self._cancelar,
            visible=False,
        )
        self.btn_ver_devedores = ft.TextButton(
            "Ver devedores",
            icon=ft.Icons.WARNING_AMBER,
            on_click=self._filtrar_devedores,
        )

        self._cliente_editando_id = None
        self._mostrando_devedores = False

        self.tabela = ft.DataTable(
            expand=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            column_spacing=20,
            columns=[
                ft.DataColumn(ft.Text("Nome",          weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Telefone",      weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Saldo Devedor", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Ações",         weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        self.msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13)

        formulario = ft.Container(
            content=ft.Column([
                ft.Text("Clientes", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.field_nome, self.field_telefone]),
                self.msg_erro,
                ft.Row([self.btn_salvar, self.btn_cancelar]),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_200),
        )

        self.controls = [
            ft.Container(
                expand=True,
                padding=24,
                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,   # ← scroll no Column, não no Row
                    controls=[
                        formulario,
                        ft.Container(height=16),
                        ft.Row([self.field_busca, self.btn_ver_devedores]),
                        ft.Container(height=8),
                        self.tabela,
                    ],
                ),
            )
        ]

        self._carregar_tabela()

    # ── Tabela ───────────────────────────────────────────────────────

    def _carregar_tabela(self, clientes=None):
        if clientes is None:
            clientes = self.service.listar_todos()

        self.tabela.rows = []
        for c in clientes:
            saldo = c.saldo_devedor or 0
            self.tabela.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(c.nome)),
                    ft.DataCell(ft.Text(c.telefone or "")),
                    ft.DataCell(
                        ft.Text(
                            f"R$ {saldo:.2f}",
                            color=ft.Colors.RED_600 if saldo > 0 else ft.Colors.GREEN_600,
                            weight=ft.FontWeight.BOLD if saldo > 0 else ft.FontWeight.NORMAL,
                        )
                    ),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                ft.Icons.EDIT,
                                tooltip="Editar",
                                icon_color=ft.Colors.BLUE_600,
                                data=c.id,
                                on_click=self._editar,
                            ),
                            # ← NOVO: botão de registrar pagamento (só aparece se tem saldo)
                            ft.IconButton(
                                ft.Icons.PAYMENTS,
                                tooltip="Registrar pagamento",
                                icon_color=ft.Colors.GREEN_700,
                                data=c,
                                on_click=self._abrir_pagamento,
                                visible=saldo > 0,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE,
                                tooltip="Remover",
                                icon_color=ft.Colors.RED_400,
                                data=c.id,
                                on_click=self._confirmar_remover,
                            ),
                        ])
                    ),
                ])
            )
        self._page.update()

    def _on_busca(self, e):
        termo = e.control.value.strip()
        self._mostrando_devedores = False
        self.btn_ver_devedores.text = "Ver devedores"
        clientes = self.service.buscar_por_nome(termo) if termo else self.service.listar_todos()
        self._carregar_tabela(clientes)

    def _filtrar_devedores(self, e):
        if self._mostrando_devedores:
            self._mostrando_devedores = False
            self.btn_ver_devedores.text = "Ver devedores"
            self.field_busca.value = ""
            self._carregar_tabela()
        else:
            self._mostrando_devedores = True
            self.btn_ver_devedores.text = "Ver todos"
            self.field_busca.value = ""
            self._carregar_tabela(self.service.listar_devedores())

    # ── Pagamento ────────────────────────────────────────────────────

    def _abrir_pagamento(self, e):
        cliente = e.control.data
        saldo = cliente.saldo_devedor or 0

        field_valor = ft.TextField(
            label=f"Valor pago (saldo: R$ {saldo:.2f})",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=260,
            autofocus=True,
        )
        msg = ft.Text("", color=ft.Colors.RED_400, size=12)

        def confirmar(ev):
            try:
                valor = float(field_valor.value.replace(",", "."))
                if valor <= 0:
                    raise ValueError("Valor deve ser maior que zero.")
                if valor > saldo:
                    raise ValueError(f"Valor maior que o saldo devedor (R$ {saldo:.2f}).")
            except ValueError as ex:
                msg.value = str(ex)
                self._page.update()
                return

            novo_saldo = round(saldo - valor, 2)
            self.service.atualizar(
                cliente.id,
                ClienteUpdate(saldo_devedor=novo_saldo),
            )
            dialog.open = False
            self._carregar_tabela()

        def fechar(ev):
            dialog.open = False
            self._page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Pagamento — {cliente.nome}"),
            content=ft.Column([
                ft.Text(f"Saldo atual: R$ {saldo:.2f}", weight=ft.FontWeight.BOLD),
                field_valor,
                msg,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton(
                    "Confirmar",
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE,
                    on_click=confirmar,
                ),
            ],
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    # ── Formulário ───────────────────────────────────────────────────

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
                self.service.cadastrar(ClienteCreate(nome=nome, telefone=telefone or None))
            else:
                self.service.atualizar(
                    self._cliente_editando_id,
                    ClienteUpdate(nome=nome, telefone=telefone or None),
                )
        except ValueError as ex:
            self.msg_erro.value = str(ex)
            self._page.update()
            return
        self._limpar_form()
        self._carregar_tabela()

    def _editar(self, e):
        cliente = self.service.buscar_por_id(e.control.data)
        self._cliente_editando_id = cliente.id
        self.field_nome.value = cliente.nome
        self.field_telefone.value = cliente.telefone or ""
        self.btn_salvar.text = "Atualizar"
        self.btn_cancelar.visible = True
        self.msg_erro.value = ""
        self._page.update()

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
            content=ft.Text("Tem certeza que deseja remover este cliente?"),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton(
                    "Remover",
                    on_click=confirmar,
                    bgcolor=ft.Colors.RED_400,
                    color=ft.Colors.WHITE,
                ),
            ],
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()