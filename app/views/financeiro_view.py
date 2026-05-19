import flet as ft
from sqlmodel import Session

from app.services.financeiro_services import FinanceiroService
from app.services.movimentacao_services import MovimentacaoService
from app.services.cliente_services import ClienteService
from app.services.item_services import ItemService

from app.utils.enums import (
    TipoFinanceiro,
    TipoPagamento,
    TipoMovimentacao,
)


class FinanceiroView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True, spacing=0)

        self.session = session
        self._page = page

        self.service             = FinanceiroService(session)
        self.mov_service         = MovimentacaoService(session)
        self.cliente_service     = ClienteService(session)
        self.item_service        = ItemService(session)

        self._todos_registros    = []

        self._build()

    # ============================================================
    # BUILD
    # ============================================================

    def _build(self):

        # ── Resumo ──────────────────────────────────────────────
        self.txt_receitas = ft.Text("R$ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        self.txt_despesas = ft.Text("R$ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
        self.txt_saldo    = ft.Text("R$ 0.00", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pendente = ft.Text("R$ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)

        # ── Filtros ─────────────────────────────────────────────
        self.filtro_tipo = ft.Dropdown(
            label="Tipo",
            width=180,
            value="todos",
            on_change=self._aplicar_filtros,
            options=[
                ft.dropdown.Option(key="todos",                      text="Todos"),
                ft.dropdown.Option(key=TipoFinanceiro.receita.value, text="Receita"),
                ft.dropdown.Option(key=TipoFinanceiro.despesa.value, text="Despesa"),
                ft.dropdown.Option(key="pendurado",                  text="Pendurado"),
            ],
        )

        self.filtro_pagamento = ft.Dropdown(
            label="Pagamento",
            width=180,
            value="todos",
            on_change=self._aplicar_filtros,
            options=[
                ft.dropdown.Option(key="todos",                       text="Todos"),
                ft.dropdown.Option(key=TipoPagamento.pix.value,       text="Pix"),
                ft.dropdown.Option(key=TipoPagamento.dinheiro.value,  text="Dinheiro"),
                ft.dropdown.Option(key=TipoPagamento.debito.value,    text="Débito"),
                ft.dropdown.Option(key=TipoPagamento.credito.value,   text="Crédito"),
            ],
        )

        self.filtro_busca = ft.TextField(
            label="Buscar descrição",
            expand=True,
            on_change=self._aplicar_filtros,
        )

        btn_recarregar = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Recarregar",
            on_click=lambda _: self._carregar_tabela(),
        )

        # ── Tabela financeiro (receitas/despesas) ────────────────
        self.tabela = ft.DataTable(
            expand=True,
            border=ft.BorderSide(1, ft.Colors.GREY_300),
            columns=[
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Pagamento")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Data")),
            ],
            rows=[],
        )

        # ── Tabela pendurados (vendas a prazo) ───────────────────
        self.tabela_pendurados = ft.DataTable(
            expand=True,
            border=ft.BorderSide(1, ft.Colors.ORANGE_200),
            columns=[
                ft.DataColumn(ft.Text("Cliente")),
                ft.DataColumn(ft.Text("Item")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Data")),
            ],
            rows=[],
        )

        # ── Layout ──────────────────────────────────────────────
        self.controls = [
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[

                        ft.Text("Financeiro", size=24, weight=ft.FontWeight.BOLD),
                        ft.Divider(),

                        # Resumo
                        ft.Row([
                            ft.Column([ft.Text("Receitas"),  self.txt_receitas]),
                            ft.Column([ft.Text("Despesas"),  self.txt_despesas]),
                            ft.Column([ft.Text("Saldo"),     self.txt_saldo]),
                            ft.Column([ft.Text("Pendente"),  self.txt_pendente]),
                        ]),

                        ft.Divider(),

                        # Filtros
                        ft.Row([
                            self.filtro_tipo,
                            self.filtro_pagamento,
                            self.filtro_busca,
                            btn_recarregar,
                        ]),

                        # Tabela principal
                        self.tabela,

                        ft.Container(height=16),

                        # Seção pendurados
                        ft.Text(
                            "Vendas Penduradas (a receber)",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_800,
                        ),
                        self.tabela_pendurados,
                    ],
                ),
            )
        ]

        # Carrega dados imediatamente ao construir a view
        self._carregar_tabela()

    # ============================================================
    # CARREGAMENTO
    # ============================================================

    def _carregar_tabela(self, e=None):
        self._todos_registros = self.service.listar_todos()
        self._carregar_pendurados()
        self._aplicar_filtros()

    def _carregar_pendurados(self):
        """Busca vendas com cliente vinculado (penduradas)."""
        movs     = self.mov_service.listar_por_tipo(TipoMovimentacao.saida)
        itens    = {i.id: i.nome    for i in self.item_service.listar_todos()}
        clientes = {c.id: c.nome    for c in self.cliente_service.listar_todos()}

        penduradas = [m for m in movs if m.cliente_id is not None]

        self.tabela_pendurados.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(clientes.get(m.cliente_id, "-"))),
                ft.DataCell(ft.Text(itens.get(m.item_id, "-"))),
                ft.DataCell(ft.Text(str(m.quantidade))),
                ft.DataCell(ft.Text(f"R$ {m.valor_unitario * m.quantidade:.2f}")),
                ft.DataCell(ft.Text(m.data.strftime("%d/%m/%Y %H:%M"))),
            ])
            for m in penduradas
        ]

        total_pendente = sum(m.valor_unitario * m.quantidade for m in penduradas)
        self.txt_pendente.value = f"R$ {total_pendente:.2f}"

    # ============================================================
    # FILTROS
    # ============================================================

    def _aplicar_filtros(self, e=None):
        registros = self._todos_registros

        if self.filtro_tipo.value and self.filtro_tipo.value != "todos":
            registros = [
                r for r in registros
                if getattr(r.tipo, "value", r.tipo) == self.filtro_tipo.value
            ]

        if self.filtro_pagamento.value and self.filtro_pagamento.value != "todos":
            registros = [
                r for r in registros
                if getattr(r.pagamento, "value", r.pagamento) == self.filtro_pagamento.value
            ]

        termo = (self.filtro_busca.value or "").strip().lower()
        if termo:
            registros = [r for r in registros if termo in (r.descricao or "").lower()]

        self._renderizar_tabela(registros)
        self._atualizar_resumo(registros)

    def _renderizar_tabela(self, registros):
        self.tabela.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(
                    str(getattr(r.tipo,     "value", r.tipo)).capitalize()
                )),
                ft.DataCell(ft.Text(
                    str(getattr(r.pagamento,"value", r.pagamento)).capitalize()
                )),
                ft.DataCell(ft.Text(f"R$ {r.valor:.2f}")),
                ft.DataCell(ft.Text(r.descricao or "-")),
                ft.DataCell(ft.Text(r.data.strftime("%d/%m/%Y %H:%M"))),
            ])
            for r in registros
        ]
        self._page.update()

    # ============================================================
    # RESUMO
    # ============================================================

    def _atualizar_resumo(self, registros):
        receitas = sum(
            r.valor for r in registros
            if getattr(r.tipo, "value", r.tipo) == TipoFinanceiro.receita.value
        )
        despesas = sum(
            r.valor for r in registros
            if getattr(r.tipo, "value", r.tipo) == TipoFinanceiro.despesa.value
        )
        saldo = receitas - despesas

        self.txt_receitas.value = f"R$ {receitas:.2f}"
        self.txt_despesas.value = f"R$ {despesas:.2f}"
        self.txt_saldo.value    = f"R$ {saldo:.2f}"
        self.txt_saldo.color    = ft.Colors.GREEN_700 if saldo >= 0 else ft.Colors.RED_700

        self._page.update()