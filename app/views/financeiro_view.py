# financeiro_view.py

from datetime import datetime, timedelta

import flet as ft
from sqlmodel import Session

from app.schemas.financeiro_base import financeiroCreate

from app.services.financeiro_services import FinanceiroService
from app.services.movimentacao_services import MovimentacaoService
from app.services.cliente_services import ClienteService
from app.services.item_services import ItemService

from app.utils.enums import (
    TipoFinanceiro,
    TipoPagamento,
    TipoMovimentacao,
)


# ============================================================
# HELPERS
# ============================================================

def _badge(texto, bg, fg, icon):
    return ft.Container(
        border_radius=6,
        bgcolor=bg,
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
                ft.Icon(icon, size=13, color=fg),
                ft.Text(texto, size=12, color=fg),
            ],
        ),
    )


def _badge_tipo(valor):
    v = valor.lower()

    if v == "receita":
        return _badge(
            valor,
            ft.Colors.GREEN_50,
            ft.Colors.GREEN_800,
            ft.Icons.ARROW_DOWNWARD,
        )

    if v == "despesa":
        return _badge(
            valor,
            ft.Colors.RED_50,
            ft.Colors.RED_800,
            ft.Icons.ARROW_UPWARD,
        )

    return _badge(
        valor,
        ft.Colors.ORANGE_50,
        ft.Colors.ORANGE_800,
        ft.Icons.WATCH_LATER,
    )


def _badge_pag(valor):
    mapa = {
        "pix": ft.Icons.PIX,
        "dinheiro": ft.Icons.ATTACH_MONEY,
        "debito": ft.Icons.CREDIT_CARD,
        "débito": ft.Icons.CREDIT_CARD,
        "credito": ft.Icons.CREDIT_CARD,
        "crédito": ft.Icons.CREDIT_CARD,
    }

    return _badge(
        valor,
        ft.Colors.BLUE_50,
        ft.Colors.BLUE_800,
        mapa.get(valor.lower(), ft.Icons.PAYMENT),
    )


def _cell(content, width=None, expand=False):
    return ft.Container(
        content=content,
        width=width,
        expand=expand,
    )


def _hover_row(e):
    e.control.bgcolor = (
        ft.Colors.GREY_50
        if e.data == "true"
        else None
    )

    e.control.update()


def _header_row(cols):
    return ft.Container(
        bgcolor=ft.Colors.GREY_100,
        padding=10,
        content=ft.Row(
            spacing=8,
            controls=[
                _cell(
                    ft.Text(
                        label,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_700,
                    ),
                    width=width,
                    expand=(width is None),
                )
                for label, width in cols
            ],
        ),
    )


def _row_financeiro(r):
    tipo = str(getattr(r.tipo, "value", r.tipo)).capitalize()
    pag = str(getattr(r.pagamento, "value", r.pagamento)).capitalize()

    return ft.Container(
        padding=10,
        on_hover=_hover_row,
        content=ft.Row(
            spacing=8,
            controls=[
                _cell(_badge_tipo(tipo), width=110),

                _cell(_badge_pag(pag), width=110),

                _cell(
                    ft.Text(f"R$ {r.valor:.2f}"),
                    width=90,
                ),

                _cell(
                    ft.Text(
                        r.descricao or "-",
                        color=ft.Colors.GREY_700,
                    ),
                    expand=True,
                ),

                _cell(
                    ft.Text(
                        r.data.strftime("%d/%m/%Y %H:%M"),
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                    width=130,
                ),
            ],
        ),
    )


def _build_table(header, rows, altura=320):

    body = []

    for i, row in enumerate(rows):

        body.append(row)

        if i < len(rows) - 1:

            body.append(
                ft.Divider(
                    height=1,
                    thickness=0.5,
                    color=ft.Colors.GREY_200,
                )
            )

    return ft.Container(

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

                    height=altura,

                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0,
                        controls=body,
                    ),
                ),
            ],
        ),
    )


# ============================================================
# VIEW
# ============================================================

class FinanceiroView(ft.Column):

    def __init__(self, session: Session, page: ft.Page):

        super().__init__(
            expand=True,
            spacing=0,
        )

        self.session = session
        self._page = page

        self.service = FinanceiroService(session)
        self.mov_service = MovimentacaoService(session)
        self.cliente_service = ClienteService(session)
        self.item_service = ItemService(session)

        self._todos_registros = []
        self._penduradas_cache = []

        self._clientes_map = {}
        self._itens_map = {}

        self._build()

        self._carregar_tabela()

    # ============================================================
    # SAFE UPDATE
    # ============================================================

    def _safe_update(self, control=None):

        try:

            if control and control.page:
                control.update()

            elif self.page:
                self.update()

        except Exception:
            pass

    # ============================================================
    # BUILD
    # ============================================================

    def _build(self):

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

        self.txt_pendente = ft.Text(
            "R$ 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ORANGE_700,
        )

        # ======================================================
        # FILTROS
        # ======================================================

        self.filtro_tipo = ft.Dropdown(
            label="Tipo",
            width=160,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),

                ft.dropdown.Option(
                    TipoFinanceiro.receita.value,
                    "Receita",
                ),

                ft.dropdown.Option(
                    TipoFinanceiro.despesa.value,
                    "Despesa",
                ),
            ],
        )

        self.filtro_tipo.on_change = self._aplicar_filtros

        self.filtro_pagamento = ft.Dropdown(
            label="Pagamento",
            width=160,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option(TipoPagamento.pix.value, "Pix"),
                ft.dropdown.Option(TipoPagamento.dinheiro.value, "Dinheiro"),
                ft.dropdown.Option(TipoPagamento.debito.value, "Débito"),
                ft.dropdown.Option(TipoPagamento.credito.value, "Crédito"),
            ],
        )

        self.filtro_pagamento.on_change = self._aplicar_filtros

        self.filtro_busca = ft.TextField(
            label="Buscar descrição",
            expand=True,
        )

        self.filtro_busca.on_change = self._aplicar_filtros

        self.filtro_cliente = ft.Dropdown(
            label="Cliente",
            width=220,
            value="todos",
            options=[
                ft.dropdown.Option(
                    "todos",
                    "Todos os clientes",
                )
            ],
        )

        

        # ======================================================
        # BOTÕES
        # ======================================================

        btn_filtrar = ft.FilledButton(
            "Filtrar pendentes",
            icon=ft.Icons.FILTER_ALT,
            on_click=self._aplicar_filtro_pendurados,
        )

        btn_reload = ft.FilledButton(
            "Atualizar",
            icon=ft.Icons.REFRESH,
            on_click=self._carregar_tabela,
        )

        btn_quitar = ft.FilledButton(
            "Quitar pendurado",
            icon=ft.Icons.PAID,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=self._abrir_quitacao_cliente,
        )

        self.tabela_box = ft.Column()

        self.tabela_pend_box = ft.Column()

        # ======================================================
        # LAYOUT
        # ======================================================

        self.controls = [

            ft.Container(
                expand=True,
                padding=20,

                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,

                    controls=[

                        ft.Text(
                            "Financeiro",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Divider(),

                        ft.Row(
                            spacing=32,

                            controls=[

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

                                ft.Column([
                                    ft.Text("Pendente"),
                                    self.txt_pendente,
                                ]),
                            ],
                        ),

                        ft.Divider(),

                        ft.Row([
                            self.filtro_tipo,
                            self.filtro_pagamento,
                            self.filtro_busca,
                        ]),

                        ft.Row([
                            btn_reload,
                        ]),

                        ft.Container(height=10),

                        self.tabela_box,

                        ft.Container(height=20),

                        ft.Text(
                            "Vendas penduradas",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Row([
                            self.filtro_cliente,
                            btn_filtrar,
                            
                        ]),

                        ft.Container(height=10),

                        self.tabela_pend_box,
                    ],
                ),
            )
        ]

    # ============================================================
    # QUITAR PENDURADO
    # ============================================================
    def _abrir_quitacao_cliente(self, e):

        clientes_ids = sorted({
            m.cliente_id
            for m in self._penduradas_cache
            if m.cliente_id is not None
        })

        if not clientes_ids:

            self._page.snack_bar = ft.SnackBar(
                ft.Text("Nenhum pendurado encontrado."),
                bgcolor=ft.Colors.RED_700,
            )

            self._page.snack_bar.open = True
            self._page.update()

            return

        dropdown_cliente = ft.Dropdown(
            label="Cliente",
            width=350,
            options=[
                ft.dropdown.Option(
                    str(cid),
                    self._clientes_map.get(cid, f"#{cid}")
                )
                for cid in clientes_ids
            ]
        )

        txt_saldo = ft.Text(
            "Saldo pendente: R$ 0.00",
            color=ft.Colors.ORANGE_700,
            weight=ft.FontWeight.BOLD,
        )

        field_valor = ft.TextField(
            label="Valor recebido",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        msg = ft.Text(
            "",
            color=ft.Colors.RED,
        )

        def atualizar_saldo(ev):

            if not dropdown_cliente.value:
                return

            cliente_id = int(dropdown_cliente.value)

            pendencias = [
                m
                for m in self._penduradas_cache
                if m.cliente_id == cliente_id
            ]

            total = sum(
                (m.valor_unitario * m.quantidade)
                - (m.valor_pago or 0)
                for m in pendencias
            )

            txt_saldo.value = f"Saldo pendente: R$ {total:.2f}"

            self._page.update()

        dropdown_cliente.on_change = atualizar_saldo

        def confirmar(ev):

            try:

                if not dropdown_cliente.value:
                    raise ValueError("Selecione um cliente.")

                valor = float(
                    field_valor.value.replace(",", ".")
                )

                if valor <= 0:
                    raise ValueError("Valor inválido.")

                cliente_id = int(dropdown_cliente.value)

                pendencias = [
                    m
                    for m in self._penduradas_cache
                    if m.cliente_id == cliente_id
                ]

                restante = valor

                for mov in pendencias:

                    saldo_mov = (
                        (mov.valor_unitario * mov.quantidade)
                        - (mov.valor_pago or 0)
                    )

                    if restante <= 0:
                        break

                    pagar = min(restante, saldo_mov)

                    novo_pago = (
                        (mov.valor_pago or 0)
                        + pagar
                    )

                    self.mov_service.atualizar(
                        mov.id,
                        {
                            "valor_pago": novo_pago
                        }
                    )

                    restante -= pagar

                self.service.registrar(
                    financeiroCreate(
                        tipo=TipoFinanceiro.receita,
                        pagamento=TipoPagamento.pix,
                        valor=valor,
                        descricao=f"Quitação pendurado - {self._clientes_map.get(cliente_id)}",
                        movimentacao_id=None,
                    )
                )

                dialog.open = False

                self._page.update()

                self._carregar_tabela()

            except Exception as ex:

                msg.value = str(ex)

                self._page.update()

        dialog = ft.AlertDialog(

            modal=True,

            title=ft.Text(
                "Quitar pendurado"
            ),

            content=ft.Column(
                tight=True,

                controls=[

                    dropdown_cliente,

                    txt_saldo,

                    field_valor,

                    msg,
                ],
            ),

            actions=[

                ft.TextButton(
                    "Cancelar",
                    on_click=lambda ev: self._fechar_dialog(dialog),
                ),

                ft.ElevatedButton(
                    "Quitar",
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE,
                    on_click=confirmar,
                ),
            ],
        )

        self._page.dialog = dialog

        dialog.open = True

        self._page.update()

    

    def _fechar_dialog(self, dialog):

        dialog.open = False

        self._page.update()

    # ============================================================
    # LOAD
    # ============================================================

    def _carregar_tabela(self, e=None):

        clientes = self.cliente_service.listar_todos()

        itens = self.item_service.listar_todos()

        self._clientes_map = {
            c.id: c.nome
            for c in clientes
        }

        self._itens_map = {
            i.id: i.nome
            for i in itens
        }

        # ======================================================
        # SOMENTE HOJE
        # ======================================================

        inicio = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        fim = inicio + timedelta(days=1)

        self._todos_registros = self.service.listar_por_periodo(
            inicio,
            fim,
        )

        self._carregar_pendurados(
            inicio,
            fim,
        )

        self._atualizar_filtro_clientes()

        self._aplicar_filtros()
        
        self._renderizar_pendurados(
            self._penduradas_cache
        )

    def _carregar_pendurados(self, inicio, fim):

        movs = self.mov_service.listar_por_periodo(
            inicio,
            fim,
        )

        self._penduradas_cache = []

        for m in movs:

            if m.tipo != TipoMovimentacao.saida:
                continue

            if m.cliente_id is None:
                continue

            total = (
                m.valor_unitario
                * m.quantidade
            )

            valor_pago = (
                m.valor_pago or 0
            )

            # SOMENTE O QUE AINDA TEM SALDO

            if valor_pago < total:
                self._penduradas_cache.append(m)

        total_pendente = sum(
            (
                m.valor_unitario * m.quantidade
            ) - (
                m.valor_pago or 0
            )
            for m in self._penduradas_cache
        )

        self.txt_pendente.value = (
            f"R$ {total_pendente:.2f}"
        )

    def _atualizar_filtro_clientes(self):

        ids = {
            m.cliente_id
            for m in self._penduradas_cache
        }

        self.filtro_cliente.options = [

            ft.dropdown.Option(
                "todos",
                "Todos os clientes",
            ),

            *[
                ft.dropdown.Option(
                    str(cid),
                    self._clientes_map.get(
                        cid,
                        f"#{cid}",
                    ),
                )
                for cid in ids
            ],
        ]

    # ============================================================
    # FILTROS
    # ============================================================

    def _aplicar_filtros(self, e=None):

        registros = self._todos_registros

        if self.filtro_tipo.value != "todos":

            registros = [

                r

                for r in registros

                if getattr(
                    r.tipo,
                    "value",
                    r.tipo,
                ) == self.filtro_tipo.value
            ]

        if self.filtro_pagamento.value != "todos":

            registros = [

                r

                for r in registros

                if getattr(
                    r.pagamento,
                    "value",
                    r.pagamento,
                ) == self.filtro_pagamento.value
            ]

        termo = (
            self.filtro_busca.value or ""
        ).strip().lower()

        if termo:

            registros = [

                r

                for r in registros

                if termo in (
                    r.descricao or ""
                ).lower()
            ]

        self._renderizar_tabela(
            registros
        )

        self._atualizar_resumo(
            registros
        )

    def _aplicar_filtro_pendurados(self, e=None):

        val = self.filtro_cliente.value

        penduradas = (
            self._penduradas_cache
            if val == "todos"
            else [
                m
                for m in self._penduradas_cache
                if str(m.cliente_id) == val
            ]
        )

        self._renderizar_pendurados(
            penduradas
        )

    # ============================================================
    # RENDER
    # ============================================================

    def _renderizar_tabela(self, registros):

        header = _header_row([

            ("Tipo", 110),
            ("Pagamento", 110),
            ("Valor", 90),
            ("Descrição", None),
            ("Data", 130),
        ])

        rows = (

            [
                _row_financeiro(r)
                for r in registros
            ]

            or [

                ft.Container(
                    padding=20,

                    content=ft.Text(
                        "Nenhum registro encontrado.",
                        color=ft.Colors.GREY_500,
                    ),
                )
            ]
        )

        self.tabela_box.controls = [

            _build_table(
                header,
                rows,
            )
        ]

        self._safe_update(
            self.tabela_box
        )

    def _renderizar_pendurados(self, penduradas):

        header = _header_row([

            ("Cliente", 160),
            ("Item", None),
            ("Qtd", 50),
            ("Saldo", 90),
            ("Data", 130),
            
        ])

        rows = []

        if not penduradas:

            rows.append(

                ft.Container(
                    padding=20,

                    content=ft.Text(
                        "Nenhuma venda pendurada.",
                        color=ft.Colors.GREY_500,
                    ),
                )
            )

        else:

            for m in penduradas:

                saldo = (
                    (
                        m.valor_unitario
                        * m.quantidade
                    ) - (
                        m.valor_pago or 0
                    )
                )

                row = ft.Container(
                    padding=10,
                    on_hover=_hover_row,

                    content=ft.Row(
                        spacing=8,

                        controls=[

                            _cell(
                                ft.Text(
                                    self._clientes_map.get(
                                        m.cliente_id,
                                        "-",
                                    )
                                ),
                                width=160,
                            ),

                            _cell(
                                ft.Text(
                                    self._itens_map.get(
                                        m.item_id,
                                        "-",
                                    ),
                                    color=ft.Colors.GREY_700,
                                ),
                                expand=True,
                            ),

                            _cell(
                                ft.Text(
                                    str(m.quantidade)
                                ),
                                width=50,
                            ),

                            _cell(
                                ft.Text(
                                    f"R$ {saldo:.2f}",
                                    color=ft.Colors.ORANGE_800,
                                ),
                                width=90,
                            ),

                            _cell(
                                ft.Text(
                                    m.data.strftime(
                                        "%d/%m/%Y %H:%M"
                                    ),
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                ),
                                width=130,
                            ),

                            
                        ],
                    ),
                )

                rows.append(row)

        self.tabela_pend_box.controls = [

            _build_table(
                header,
                rows,
                altura=320,
            )
        ]

        self._safe_update(
            self.tabela_pend_box
        )

    # ============================================================
    # RESUMO
    # ============================================================

    def _atualizar_resumo(self, registros):

        receitas = sum(

            r.valor

            for r in registros

            if getattr(
                r.tipo,
                "value",
                r.tipo,
            ) == TipoFinanceiro.receita.value
        )

        despesas = sum(

            r.valor

            for r in registros

            if getattr(
                r.tipo,
                "value",
                r.tipo,
            ) == TipoFinanceiro.despesa.value
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

        self._safe_update()