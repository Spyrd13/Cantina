import flet as ft
from sqlmodel import Session

from app.services.financeiro_services import FinanceiroService

from app.utils.enums import (
    TipoFinanceiro,
    TipoPagamento,
)


class FinanceiroView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):

        super().__init__(
            expand=True,
            spacing=0,
        )

        self.session = session
        self._page = page

        self.service = FinanceiroService(session)

        self._todos_registros = []

        self._build()

    # ============================================================
    # BUILD
    # ============================================================

    def _build(self):

        # ========================================================
        # RESUMO
        # ========================================================

        self.txt_receitas = ft.Text(
            "R$ 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_700,
        )

        self.txt_despesas = ft.Text(
            "R$ 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.RED_700,
        )

        self.txt_saldo = ft.Text(
            "R$ 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
        )

        # ========================================================
        # FILTROS
        # ========================================================

        self.filtro_tipo = ft.Dropdown(
            label="Tipo",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option(
                    key="todos",
                    text="Todos",
                ),

                ft.dropdown.Option(
                    key=TipoFinanceiro.receita.value,
                    text="Receita",
                ),

                ft.dropdown.Option(
                    key=TipoFinanceiro.despesa.value,
                    text="Despesa",
                ),
            ],
        )

        self.filtro_pagamento = ft.Dropdown(
            label="Pagamento",
            width=180,
            value="todos",
            options=[
                ft.dropdown.Option(
                    key="todos",
                    text="Todos",
                ),

                ft.dropdown.Option(
                    key=TipoPagamento.pix.value,
                    text="Pix",
                ),

                ft.dropdown.Option(
                    key=TipoPagamento.dinheiro.value,
                    text="Dinheiro",
                ),

                ft.dropdown.Option(
                    key=TipoPagamento.debito.value,
                    text="Débito",
                ),

                ft.dropdown.Option(
                    key=TipoPagamento.credito.value,
                    text="Crédito",
                ),
            ],
        )

        self.filtro_busca = ft.TextField(
            label="Buscar descrição",
            expand=True,
        )

        self.filtro_tipo.on_change = (
            self._aplicar_filtros
        )

        self.filtro_pagamento.on_change = (
            self._aplicar_filtros
        )

        self.filtro_busca.on_change = (
            self._aplicar_filtros
        )

        # ========================================================
        # TABELA
        # ========================================================

        self.tabela = ft.DataTable(

            expand=True,

            border=ft.BorderSide(
                1,
                ft.Colors.GREY_300,
            ),

            columns=[

                ft.DataColumn(
                    ft.Text("Tipo")
                ),

                ft.DataColumn(
                    ft.Text("Pagamento")
                ),

                ft.DataColumn(
                    ft.Text("Valor")
                ),

                ft.DataColumn(
                    ft.Text("Descrição")
                ),

                ft.DataColumn(
                    ft.Text("Data")
                ),
            ],

            rows=[],
        )

        # ========================================================
        # LAYOUT
        # ========================================================

        self.controls = [

            ft.Container(

                expand=True,
                padding=20,

                content=ft.Column([

                    ft.Text(
                        "Financeiro",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.Divider(),

                    ft.Row([

                        ft.Column([
                            ft.Text("Receitas"),
                            self.txt_receitas,
                        ]),

                        ft.Column([
                            ft.Text("Despesas"),
                            self.txt_despesas,
                        ]),

                        ft.Column([
                            ft.Text("Saldo"),
                            self.txt_saldo,
                        ]),
                    ]),

                    ft.Divider(),

                    ft.Row([
                        self.filtro_tipo,
                        self.filtro_pagamento,
                        self.filtro_busca,
                    ]),

                    ft.Row(
                        [self.tabela],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ])
            )
        ]

        self._carregar_tabela()

    # ============================================================
    # TABELA
    # ============================================================

    def _carregar_tabela(self):

        self._todos_registros = (
            self.service.listar_todos()
        )

        self._aplicar_filtros()

    def _aplicar_filtros(self, e=None):

        registros = self._todos_registros

        if (
            self.filtro_tipo.value
            and self.filtro_tipo.value != "todos"
        ):

            registros = [

                r for r in registros

                if (
                    str(r.tipo)
                    == self.filtro_tipo.value
                )
                or (
                    getattr(
                        r.tipo,
                        "value",
                        ""
                    )
                    == self.filtro_tipo.value
                )
            ]

        if (
            self.filtro_pagamento.value
            and self.filtro_pagamento.value != "todos"
        ):

            registros = [

                r for r in registros

                if (
                    str(r.tipo_pagamento)
                    == self.filtro_pagamento.value
                )
                or (
                    getattr(
                        r.tipo_pagamento,
                        "value",
                        ""
                    )
                    == self.filtro_pagamento.value
                )
            ]

        termo = (
            self.filtro_busca.value
            .strip()
            .lower()
            if self.filtro_busca.value
            else ""
        )

        if termo:

            registros = [

                r for r in registros

                if termo in (
                    r.descricao or ""
                ).lower()
            ]

        self._renderizar_tabela(registros)

        self._atualizar_resumo(registros)

    def _renderizar_tabela(self, registros):

        self.tabela.rows = []

        for r in registros:

            self.tabela.rows.append(

                ft.DataRow(
                    cells=[

                        ft.DataCell(
                            ft.Text(
                                str(
                                    getattr(
                                        r.tipo,
                                        "value",
                                        r.tipo,
                                    )
                                ).capitalize()
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                str(
                                    getattr(
                                        r.tipo_pagamento,
                                        "value",
                                        r.tipo_pagamento,
                                    )
                                ).capitalize()
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                f"R$ {r.valor:.2f}"
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                r.descricao or "-"
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                r.data.strftime(
                                    "%d/%m/%Y %H:%M"
                                )
                            )
                        ),
                    ]
                )
            )

        self._page.update()

    # ============================================================
    # RESUMO
    # ============================================================

    def _atualizar_resumo(self, registros):

        receitas = sum(

            r.valor

            for r in registros

            if (
                str(r.tipo)
                == TipoFinanceiro.receita.value
            )
            or (
                getattr(
                    r.tipo,
                    "value",
                    ""
                )
                == TipoFinanceiro.receita.value
            )
        )

        despesas = sum(

            r.valor

            for r in registros

            if (
                str(r.tipo)
                == TipoFinanceiro.despesa.value
            )
            or (
                getattr(
                    r.tipo,
                    "value",
                    ""
                )
                == TipoFinanceiro.despesa.value
            )
        )

        saldo = receitas - despesas

        self.txt_receitas.value = (
            f"R$ {receitas:.2f}"
        )

        self.txt_despesas.value = (
            f"R$ {despesas:.2f}"
        )

        self.txt_saldo.value = (
            f"R$ {saldo:.2f}"
        )

        self.txt_saldo.color = (
            ft.Colors.GREEN_700
            if saldo >= 0
            else ft.Colors.RED_700
        )

        self._page.update()