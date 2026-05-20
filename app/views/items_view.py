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

        self.tabela = ft.Container(expand=True)

        self.msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13)

        formulario = ft.Container(
            content=ft.Column([
                ft.Text("Itens do Cardápio", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.field_nome, self.field_valor]),
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
                expand=True,
                padding=24,
                content=ft.Column(
                    expand=True,
                    controls=[
                        formulario,
                        ft.Container(height=16),
                        ft.Row([self.field_busca]),
                        ft.Container(height=8),
                        self.tabela,
                    ],
                ),
            )
        ]

        self._carregar_tabela()

    def _carregar_tabela(self, itens=None):

        if itens is None:
            itens = self.service.listar_todos()

        rows = []

        for item in itens:

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
                            width=120,
                            content=ft.Text(
                                f"R$ {item.valor:.2f}",
                            ),
                        ),

                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                item.descricao or "-",
                                color=ft.Colors.GREY_700,
                            ),
                        ),

                        ft.Container(
                            width=120,
                            content=ft.Row(
                                spacing=0,
                                controls=[
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
                                ],
                            ),
                        ),
                    ],
                ),
            )

            rows.append(row)

            if item != itens[-1]:
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
                        "Nenhum item encontrado.",
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
                            "Nome",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=120,
                        content=ft.Text(
                            "Valor",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            "Descrição",
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
                spacing=0,
                controls=[
                    header,

                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                            expand=True,
                            controls=rows,
                        ),
                    ),
                ],
            ),
        )

        self.tabela.content = tabela

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
            
        except ValueError:
            self.msg_erro.value = "Valor inválidos."
            self._page.update()
            return

        try:
            if self._item_editando_id is None:
                self.service.cadastrar(ItemBaseCreate(
                    nome=nome,
                    valor=valor,
                    
                    descricao=descricao or None,
                ))
            else:
                self.service.atualizar(
                    self._item_editando_id,
                    ItemBaseUpdate(
                        nome=nome,
                        valor=valor,
                        
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
        
    def _hover_row(self, e):
        e.control.bgcolor = (
            ft.Colors.GREY_50
            if e.data == "true"
            else None
        )

        e.control.update()