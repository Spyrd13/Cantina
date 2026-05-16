import flet as ft
from sqlmodel import Session
from app.services.item_services import ItemService
from app.schemas.item_base import ItemBaseCreate, ItemBaseUpdate


class ItemsView(ft.Column):
    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)
        self.session = session
        self._page = page
        self.service = ItemService(session)
        self._build()

    def _build(self):
        self.field_nome = ft.TextField(label="Nome", expand=True)
        self.field_valor = ft.TextField(label="Valor (R$)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        self.field_quantidade = ft.TextField(label="Quantidade", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        self.field_descricao = ft.TextField(label="Descrição", expand=True)
        self.field_busca = ft.TextField(
            label="Buscar item...",
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

        self._item_editando_id = None

        self.tabela = ft.DataTable(
            expand=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            column_spacing=20,
            columns=[
                ft.DataColumn(ft.Text("Nome", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Qtd", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        self.msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13)

        formulario = ft.Container(
            content=ft.Column([
                ft.Text("Itens do Cardápio", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.field_nome, self.field_valor, self.field_quantidade]),
                ft.Row([self.field_descricao]),
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
                content=ft.Column([
                    formulario,
                    ft.Container(height=16),
                    ft.Row([self.field_busca]),
                    ft.Container(height=8),
                    ft.Row(
                        [self.tabela],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ]),
                padding=24,
                expand=True,
            )
        ]

        self._carregar_tabela()

    def _carregar_tabela(self, itens=None):
        if itens is None:
            itens = self.service.listar_todos()

        self.tabela.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(item.nome)),
                ft.DataCell(ft.Text(f"R$ {item.valor:.2f}")),
                ft.DataCell(ft.Text(str(item.quantidade or 0))),
                ft.DataCell(ft.Text(item.descricao or "")),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.EDIT,
                            tooltip="Editar",
                            icon_color=ft.Colors.BLUE_600,
                            data=item.id,
                            on_click=self._editar,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            tooltip="Remover",
                            icon_color=ft.Colors.RED_400,
                            data=item.id,
                            on_click=self._confirmar_remover,
                        ),
                    ])
                ),
            ])
            for item in itens
        ]
        self._page.update()

    def _on_busca(self, e):
        termo = e.control.value.strip()
        if termo:
            itens = self.service.buscar_por_nome(termo)
        else:
            itens = self.service.listar_todos()
        self._carregar_tabela(itens)

    def _limpar_form(self):
        self.field_nome.value = ""
        self.field_valor.value = ""
        self.field_quantidade.value = ""
        self.field_descricao.value = ""
        self.msg_erro.value = ""
        self._item_editando_id = None
        self.btn_cancelar.visible = False
        self.btn_salvar.text = "Salvar"
        self._page.update()

    def _cancelar(self, e):
        self._limpar_form()

    def _salvar(self, e):
        self.msg_erro.value = ""
        nome = self.field_nome.value.strip()
        descricao = self.field_descricao.value.strip()

        try:
            valor = float(self.field_valor.value.replace(",", "."))
            quantidade = int(self.field_quantidade.value or 0)
        except ValueError:
            self.msg_erro.value = "Valor ou quantidade inválidos."
            self._page.update()
            return

        try:
            if self._item_editando_id is None:
                self.service.cadastrar(ItemBaseCreate(
                    nome=nome,
                    valor=valor,
                    quantidade=quantidade,
                    descricao=descricao or None,
                ))
            else:
                self.service.atualizar(
                    self._item_editando_id,
                    ItemBaseUpdate(
                        nome=nome,
                        valor=valor,
                        quantidade=quantidade,
                        descricao=descricao or None,
                    ),
                )
        except ValueError as ex:
            self.msg_erro.value = str(ex)
            self._page.update()
            return

        self._limpar_form()
        self._carregar_tabela()

    def _editar(self, e):
        item = self.service.buscar_por_id(e.control.data)
        self._item_editando_id = item.id
        self.field_nome.value = item.nome
        self.field_valor.value = str(item.valor)
        self.field_quantidade.value = str(item.quantidade or 0)
        self.field_descricao.value = item.descricao or ""
        self.btn_salvar.text = "Atualizar"
        self.btn_cancelar.visible = True
        self.msg_erro.value = ""
        self._page.update()

    def _confirmar_remover(self, e):
        item_id = e.control.data

        def fechar(ev):
            dialog.open = False
            self._page.update()

        def confirmar(ev):
            try:
                self.service.remover(item_id)
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
            content=ft.Text("Tem certeza que deseja remover este item?"),
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