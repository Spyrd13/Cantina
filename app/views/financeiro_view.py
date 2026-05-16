import flet as ft
from sqlmodel import Session
from app.services.financeiro_services import FinanceiroService
from app.services.movimentacao_services import MovimentacaoService
from app.schemas.financeiro_base import financeiroCreate
from app.utils.enums import TipoFinanceiro, TipoPagamento


class FinanceiroView(ft.Column):
    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)
        self.session = session
        self._page = page
        self.service = FinanceiroService(session)
        self.mov_service = MovimentacaoService(session)
        self._todos_registros = []
        self._build()

    def _build(self):
        # ── Formulário ───────────────────────────────────────────────
        self.dd_tipo = ft.Dropdown(
            label="Tipo",
            width=180,
            options=[
                ft.dropdown.Option(key=TipoFinanceiro.receita, text="Receita"),
                ft.dropdown.Option(key=TipoFinanceiro.despesa, text="Despesa"),
            ],
        )
        self.dd_pagamento = ft.Dropdown(
            label="Forma de Pagamento",
            width=200,
            options=[
                ft.dropdown.Option(key=TipoPagamento.dinheiro, text="Dinheiro"),
                ft.dropdown.Option(key=TipoPagamento.debito, text="Débito"),
                ft.dropdown.Option(key=TipoPagamento.credito, text="Crédito"),
                ft.dropdown.Option(key=TipoPagamento.pix, text="Pix"),
            ],
        )
        self.field_valor = ft.TextField(
            label="Valor (R$)",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.field_descricao = ft.TextField(label="Descrição", expand=True)
        self.dd_movimentacao = ft.Dropdown(
            label="Movimentação vinculada (opcional)",
            expand=True,
            options=self._opcoes_movimentacoes(),
        )

        self.msg_erro = ft.Text("", color=ft.Colors.RED_400, size=13)
        self.msg_ok = ft.Text("", color=ft.Colors.GREEN_600, size=13)

        btn_salvar = ft.ElevatedButton(
            "Registrar",
            icon=ft.Icons.SAVE,
            on_click=self._registrar,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )

        formulario = ft.Container(
            content=ft.Column([
                ft.Text("Financeiro", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.dd_tipo, self.dd_pagamento, self.field_valor]),
                ft.Row([self.field_descricao]),
                ft.Row([self.dd_movimentacao]),
                self.msg_erro,
                self.msg_ok,
                ft.Row([btn_salvar]),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_200),
        )

        # ── Resumo ───────────────────────────────────────────────────
        self.txt_receitas = ft.Text("R$ 0,00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600)
        self.txt_despesas = ft.Text("R$ 0,00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600)
        self.txt_saldo = ft.Text("R$ 0,00", size=16, weight=ft.FontWeight.BOLD)

        resumo = ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("Receitas", size=12, color=ft.Colors.GREY_600), self.txt_receitas], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.VerticalDivider(),
                ft.Column([ft.Text("Despesas", size=12, color=ft.Colors.GREY_600), self.txt_despesas], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.VerticalDivider(),
                ft.Column([ft.Text("Saldo", size=12, color=ft.Colors.GREY_600), self.txt_saldo], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_200),
        )

        # ── Filtros da tabela ────────────────────────────────────────
        self.filtro_tipo = ft.Dropdown(
            label="Filtrar por tipo",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option(key="todos", text="Todos"),
                ft.dropdown.Option(key=TipoFinanceiro.receita, text="Receita"),
                ft.dropdown.Option(key=TipoFinanceiro.despesa, text="Despesa"),
            ],
            on_change=self._aplicar_filtros,
        )
        self.filtro_pagamento = ft.Dropdown(
            label="Filtrar por pagamento",
            width=200,
            value="todos",
            options=[
                ft.dropdown.Option(key="todos", text="Todos"),
                ft.dropdown.Option(key=TipoPagamento.dinheiro, text="Dinheiro"),
                ft.dropdown.Option(key=TipoPagamento.debito, text="Débito"),
                ft.dropdown.Option(key=TipoPagamento.credito, text="Crédito"),
                ft.dropdown.Option(key=TipoPagamento.pix, text="Pix"),
            ],
            on_change=self._aplicar_filtros,
        )
        self.filtro_pago = ft.Dropdown(
            label="Filtrar por status",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option(key="todos", text="Todos"),
                ft.dropdown.Option(key="pago", text="Pago"),
                ft.dropdown.Option(key="pendente", text="Pendente"),
            ],
            on_change=self._aplicar_filtros,
        )
        self.filtro_busca = ft.TextField(
            label="Buscar descrição...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._aplicar_filtros,
        )

        btn_limpar_filtros = ft.TextButton(
            "Limpar filtros",
            icon=ft.Icons.CLEAR,
            on_click=self._limpar_filtros,
        )

        # ── Tabela ───────────────────────────────────────────────────
        self.tabela = ft.DataTable(
            expand=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            column_spacing=16,
            columns=[
                ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Pagamento", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    formulario,
                    ft.Container(height=12),
                    resumo,
                    ft.Container(height=12),
                    ft.Row([
                        self.filtro_tipo,
                        self.filtro_pagamento,
                        self.filtro_pago,
                        self.filtro_busca,
                        btn_limpar_filtros,
                    ]),
                    ft.Container(height=8),
                    ft.Row([self.tabela], scroll=ft.ScrollMode.AUTO),
                ]),
                padding=24,
                expand=True,
            )
        ]

        self._carregar_tabela()

    # ── Registrar ────────────────────────────────────────────────────

    def _registrar(self, e):
        self.msg_erro.value = ""
        self.msg_ok.value = ""

        if not self.dd_tipo.value:
            self.msg_erro.value = "Selecione o tipo."
            self._page.update()
            return
        if not self.dd_pagamento.value:
            self.msg_erro.value = "Selecione a forma de pagamento."
            self._page.update()
            return
        try:
            valor = float(self.field_valor.value.replace(",", "."))
        except ValueError:
            self.msg_erro.value = "Valor inválido."
            self._page.update()
            return

        mov_id = int(self.dd_movimentacao.value) if self.dd_movimentacao.value else None

        try:
            self.service.registrar(financeiroCreate(
                tipo=TipoFinanceiro(self.dd_tipo.value),
                tipo_pagamento=TipoPagamento(self.dd_pagamento.value),
                valor=valor,
                descricao=self.field_descricao.value.strip() or None,
                movimentacao_id=mov_id,
            ))
            self.msg_ok.value = "Registro financeiro salvo com sucesso!"
            self.dd_tipo.value = None
            self.dd_pagamento.value = None
            self.field_valor.value = ""
            self.field_descricao.value = ""
            self.dd_movimentacao.value = None
            self._carregar_tabela()
        except ValueError as ex:
            self.msg_erro.value = str(ex)
            self._page.update()

    # ── Tabela e filtros ─────────────────────────────────────────────

    def _carregar_tabela(self):
        self._todos_registros = self.service.listar_todos()
        self._atualizar_resumo(self._todos_registros)
        self._renderizar_tabela(self._todos_registros)

    def _aplicar_filtros(self, e=None):
        registros = self._todos_registros

        # Filtro tipo
        if self.filtro_tipo.value and self.filtro_tipo.value != "todos":
            registros = [r for r in registros if r.tipo == self.filtro_tipo.value]

        # Filtro pagamento
        if self.filtro_pagamento.value and self.filtro_pagamento.value != "todos":
            registros = [r for r in registros if r.tipo_pagamento == self.filtro_pagamento.value]

        # Filtro status pago
        if self.filtro_pago.value and self.filtro_pago.value != "todos":
            pago = self.filtro_pago.value == "pago"
            registros = [r for r in registros if r.pago == pago]

        # Filtro busca descrição
        termo = self.filtro_busca.value.strip().lower() if self.filtro_busca.value else ""
        if termo:
            registros = [r for r in registros if termo in (r.descricao or "").lower()]

        self._atualizar_resumo(registros)
        self._renderizar_tabela(registros)

    def _limpar_filtros(self, e):
        self.filtro_tipo.value = "todos"
        self.filtro_pagamento.value = "todos"
        self.filtro_pago.value = "todos"
        self.filtro_busca.value = ""
        self._atualizar_resumo(self._todos_registros)
        self._renderizar_tabela(self._todos_registros)
        self._page.update()

    def _renderizar_tabela(self, registros):
        labels_tipo = {TipoFinanceiro.receita: "Receita", TipoFinanceiro.despesa: "Despesa"}
        labels_pag = {
            TipoPagamento.dinheiro: "Dinheiro",
            TipoPagamento.debito: "Débito",
            TipoPagamento.credito: "Crédito",
            TipoPagamento.pix: "Pix",
        }

        self.tabela.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(
                    labels_tipo.get(r.tipo, r.tipo),
                    color=ft.Colors.GREEN_600 if r.tipo == TipoFinanceiro.receita else ft.Colors.RED_600,
                )),
                ft.DataCell(ft.Text(labels_pag.get(r.tipo_pagamento, r.tipo_pagamento))),
                ft.DataCell(ft.Text(f"R$ {r.valor:.2f}")),
                ft.DataCell(ft.Text(r.descricao or "")),
                ft.DataCell(
                    ft.Container(
                        content=ft.Text(
                            "Pago" if r.pago else "Pendente",
                            color=ft.Colors.WHITE,
                            size=12,
                        ),
                        bgcolor=ft.Colors.GREEN_600 if r.pago else ft.Colors.ORANGE_600,
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    )
                ),
                ft.DataCell(ft.Text(r.data.strftime("%d/%m/%Y %H:%M"))),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.CHECK_CIRCLE_OUTLINE,
                            tooltip="Marcar como pago",
                            icon_color=ft.Colors.GREEN_600,
                            data=r.id,
                            on_click=self._marcar_pago,
                            disabled=r.pago,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            tooltip="Remover",
                            icon_color=ft.Colors.RED_400,
                            data=r.id,
                            on_click=self._confirmar_remover,
                            disabled=r.pago,
                        ),
                    ])
                ),
            ])
            for r in registros
        ]
        self._page.update()

    def _atualizar_resumo(self, registros):
        receitas = sum(r.valor for r in registros if r.tipo == TipoFinanceiro.receita)
        despesas = sum(r.valor for r in registros if r.tipo == TipoFinanceiro.despesa)
        saldo = receitas - despesas

        self.txt_receitas.value = f"R$ {receitas:.2f}"
        self.txt_despesas.value = f"R$ {despesas:.2f}"
        self.txt_saldo.value = f"R$ {saldo:.2f}"
        self.txt_saldo.color = ft.Colors.GREEN_600 if saldo >= 0 else ft.Colors.RED_600

    # ── Ações ────────────────────────────────────────────────────────

    def _marcar_pago(self, e):
        try:
            self.service.marcar_como_pago(e.control.data)
            self._carregar_tabela()
        except ValueError as ex:
            self.msg_erro.value = str(ex)
            self._page.update()

    def _confirmar_remover(self, e):
        registro_id = e.control.data

        def fechar(ev):
            dialog.open = False
            self._page.update()

        def confirmar(ev):
            try:
                self.service.remover(registro_id)
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
            content=ft.Text("Tem certeza que deseja remover este registro?"),
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

    # ── Helpers ──────────────────────────────────────────────────────

    def _opcoes_movimentacoes(self) -> list:
        movs = self.mov_service.listar_todas()
        return [
            ft.dropdown.Option(key=str(m.id), text=f"#{m.id} — item {m.item_id} ({m.tipo}) {m.data.strftime('%d/%m/%Y')}")
            for m in movs
        ]