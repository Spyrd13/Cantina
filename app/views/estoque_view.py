import flet as ft
from sqlmodel import Session
from app.services.movimentacao_services import MovimentacaoService
from app.services.item_services import ItemService
from app.schemas.movimentacao_base import MovimentacaoBaseCreate
from app.utils.enums import TipoMovimentacao


class EstoqueView(ft.Column):
    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)
        self.session = session
        self._page = page
        self.service = MovimentacaoService(session)
        self.item_service = ItemService(session)
        self._build()

    def _build(self):
        self.dd_item_estoque = ft.Dropdown(
            label="Item",
            expand=True,
            options=self._opcoes_itens(),
        )
        self.dd_tipo_estoque = ft.Dropdown(
            label="Tipo",
            width=200,
            value=TipoMovimentacao.entrada.value,
            options=[
                ft.dropdown.Option(
                    key=TipoMovimentacao.entrada.value,
                    text="Entrada",
                ),
                ft.dropdown.Option(
                    key=TipoMovimentacao.ajuste.value,
                    text="Ajuste",
                ),
                ft.dropdown.Option(
                    key=TipoMovimentacao.perda.value,
                    text="Perda",
                ),
            ],
        )

        self.dd_tipo_estoque.on_change = self._on_tipo_change

        

        self.field_valor_pago = ft.TextField(
            label="Valor pago (R$)",
            width=180,
            visible=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self._on_tipo_change(None)

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

        # Tabela mostra estoque atual (um item por linha)
        self.tabela_estoque = ft.Column(expand=True)

        self._carregar_tabela_estoque()

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Movimentação de Estoque",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(),
                    ft.Row([
                        self.dd_item_estoque,
                        self.dd_tipo_estoque,
                        self.field_qtd_estoque,
                        self.field_valor_pago,
                    ]),
                    ft.Row([self.field_desc_estoque]),
                    self.msg_erro_estoque,
                    self.msg_ok_estoque,
                    ft.Row([btn_registrar]),
                    ft.Container(height=16),
                    ft.Text(
                        "Estoque Atual",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.tabela_estoque,
                ]),
                padding=24,
                expand=True,
            )
        ]

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
        
        valor_pago = None

        if self.dd_tipo_estoque.value == TipoMovimentacao.entrada.value:

            try:
                valor_pago = float(
                    self.field_valor_pago.value.replace(",", ".")
                )
            except:
                self.msg_erro_estoque.value = "Valor inválido."
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
                valor_pago=valor_pago,
            ))
            self.msg_ok_estoque.value = "Movimentação registrada com sucesso!"
            self.dd_item_estoque.value = None
            self.dd_tipo_estoque.value = None
            self.field_qtd_estoque.value = "1"
            self.field_desc_estoque.value = ""
            self.field_valor_pago.value = None
            self._carregar_tabela_estoque()
        except ValueError as ex:
            self.msg_erro_estoque.value = str(ex)
            self._page.update()

    def _carregar_tabela_estoque(self):
        itens = self.item_service.listar_todos()

        rows = []

        for item in itens:
            qtd = item.quantidade

            if qtd > 0:
                if qtd <= 5:
                    situacao_texto = "Pouco estoque"
                    situacao_cor = ft.Colors.ORANGE_700
                    situacao_bg = ft.Colors.ORANGE_50
                    situacao_icon = ft.Icons.WARNING_AMBER
                else:
                    situacao_texto = "Disponível"
                    situacao_cor = ft.Colors.GREEN_700
                    situacao_bg = ft.Colors.GREEN_50
                    situacao_icon = ft.Icons.CHECK_CIRCLE
            else:
                situacao_texto = "Sem estoque"
                situacao_cor = ft.Colors.RED_700
                situacao_bg = ft.Colors.RED_50
                situacao_icon = ft.Icons.CANCEL

            badge = ft.Container(
                bgcolor=situacao_bg,
                border_radius=6,
                padding=ft.Padding(
                    left=8,
                    top=3,
                    right=8,
                    bottom=3,
                ),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(
                            situacao_icon,
                            size=13,
                            color=situacao_cor,
                        ),
                        ft.Text(
                            situacao_texto,
                            size=12,
                            color=situacao_cor,
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
                            content=ft.Text(item.nome),
                            expand=True,
                        ),

                        ft.Container(
                            width=200,
                            content=ft.Text(
                                str(qtd),
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),

                        ft.Container(
                            width=270,
                            content=badge,
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
                            "Item",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=200,
                        content=ft.Text(
                            "Estoque",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                        ),
                    ),

                    ft.Container(
                        width=270,
                        content=ft.Text(
                            "Situação",
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
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
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

        self.tabela_estoque.controls = [tabela]

        self._page.update()

    def _opcoes_itens(self) -> list:
        itens = self.item_service.listar_todos()
        return [
            ft.dropdown.Option(key=str(i.id), text=f"{i.nome} (R$ {i.valor:.2f})")
            for i in itens
        ]
    
    def _hover_row(self, e):
        e.control.bgcolor = (
            ft.Colors.GREY_50
            if e.data == "true"
            else None
        )

        e.control.update()

    def _on_tipo_change(self, e):

        self.field_valor_pago.visible = (
            self.dd_tipo_estoque.value
            == TipoMovimentacao.entrada.value
        )

        self._page.update()