import json
import flet as ft
from sqlmodel import Session

from app.services.historico_services import HistoricoService


# ============================================================
# HELPERS DE BADGE
# ============================================================

_COR_ENTIDADE = {
    "venda":      (ft.Colors.BLUE_50,   ft.Colors.BLUE_800),
    "estoque":    (ft.Colors.GREEN_50,  ft.Colors.GREEN_800),
    "financeiro": (ft.Colors.PURPLE_50, ft.Colors.PURPLE_800),
    "item":       (ft.Colors.ORANGE_50, ft.Colors.ORANGE_800),
    "cliente":    (ft.Colors.TEAL_50,   ft.Colors.TEAL_800),
}

_COR_OPERACAO = {
    "criacao":   (ft.Colors.GREEN_50,  ft.Colors.GREEN_800),
    "edicao":    (ft.Colors.BLUE_50,   ft.Colors.BLUE_800),
    "exclusao":  (ft.Colors.RED_50,    ft.Colors.RED_800),
    "entrada":   (ft.Colors.GREEN_50,  ft.Colors.GREEN_800),
    "ajuste":    (ft.Colors.ORANGE_50, ft.Colors.ORANGE_800),
    "pagamento": (ft.Colors.TEAL_50,   ft.Colors.TEAL_800),
    "perda":     (ft.Colors.RED_50,    ft.Colors.RED_800),
}

_ICON_OPERACAO = {
    "criacao":   ft.Icons.ADD_CIRCLE_OUTLINE,
    "edicao":    ft.Icons.EDIT_NOTE,
    "exclusao":  ft.Icons.DELETE_OUTLINE,
    "entrada":   ft.Icons.ARROW_DOWNWARD,
    "ajuste":    ft.Icons.TUNE,
    "pagamento": ft.Icons.PAID,
    "perda":     ft.Icons.REMOVE_CIRCLE_OUTLINE,
}


def _badge(texto, bg, fg, icon=None):
    controls = []
    if icon:
        controls.append(ft.Icon(icon, size=12, color=fg))
    controls.append(ft.Text(texto, size=11, color=fg, weight=ft.FontWeight.W_500))
    return ft.Container(
        border_radius=4,
        bgcolor=bg,
        padding=ft.Padding(left=7, top=2, right=7, bottom=2),
        content=ft.Row(spacing=3, tight=True, controls=controls),
    )


def _badge_entidade(entidade: str):
    bg, fg = _COR_ENTIDADE.get(entidade.lower(), (ft.Colors.GREY_100, ft.Colors.GREY_700))
    return _badge(entidade.capitalize(), bg, fg)


def _badge_operacao(operacao: str):
    bg, fg = _COR_OPERACAO.get(operacao.lower(), (ft.Colors.GREY_100, ft.Colors.GREY_700))
    icon   = _ICON_OPERACAO.get(operacao.lower())
    return _badge(operacao.capitalize(), bg, fg, icon)


# ============================================================
# DIFF INLINE
# ============================================================

def _parse_json(raw) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _fmt_val(v) -> str:
    if isinstance(v, float):
        return f"R$ {v:.2f}"
    return str(v)


def _build_diff(valor_antes_raw, valor_depois_raw) -> ft.Control | None:
    """
    Retorna um widget com o diff entre antes e depois,
    ou None se não houver nada relevante.
    """
    antes  = _parse_json(valor_antes_raw)
    depois = _parse_json(valor_depois_raw)

    if not antes and not depois:
        return None

    linhas = []

    # Campos que apareceram ou mudaram
    chaves = set()
    if antes:
        chaves |= set(antes.keys())
    if depois:
        chaves |= set(depois.keys())

    for chave in sorted(chaves):
        val_a = antes.get(chave)  if antes  else None
        val_d = depois.get(chave) if depois else None

        if val_a == val_d:
            # sem mudança — mostra apenas o valor atual discretamente
            linhas.append(
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Text(f"{chave}:", size=11, color=ft.Colors.GREY_500, width=100),
                        ft.Text(_fmt_val(val_d), size=11, color=ft.Colors.GREY_600),
                    ],
                )
            )
        elif val_a is None:
            # campo novo
            linhas.append(
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Text(f"{chave}:", size=11, color=ft.Colors.GREY_500, width=100),
                        ft.Text(_fmt_val(val_d), size=11, color=ft.Colors.GREEN_700,
                                weight=ft.FontWeight.W_500),
                    ],
                )
            )
        elif val_d is None:
            # campo removido
            linhas.append(
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Text(f"{chave}:", size=11, color=ft.Colors.GREY_500, width=100),
                        ft.Text(_fmt_val(val_a), size=11, color=ft.Colors.RED_400,
                                weight=ft.FontWeight.W_500),
                        ft.Text("(removido)", size=10, color=ft.Colors.RED_300),
                    ],
                )
            )
        else:
            # valor mudou — mostra antes → depois
            linhas.append(
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Text(f"{chave}:", size=11, color=ft.Colors.GREY_500, width=100),
                        ft.Text(_fmt_val(val_a), size=11, color=ft.Colors.RED_400,
                                weight=ft.FontWeight.W_500),
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=11, color=ft.Colors.GREY_400),
                        ft.Text(_fmt_val(val_d), size=11, color=ft.Colors.GREEN_700,
                                weight=ft.FontWeight.W_500),
                    ],
                )
            )

    if not linhas:
        return None

    return ft.Container(
        bgcolor=ft.Colors.GREY_50,
        border_radius=6,
        padding=ft.Padding(left=10, top=6, right=10, bottom=6),
        margin=ft.Padding(left=0, top=4, right=0, bottom=0),
        content=ft.Column(spacing=3, controls=linhas),
    )


# ============================================================
# VIEW
# ============================================================

class HistoricoView(ft.Column):
    def __init__(self, session: Session, page: ft.Page):
        super().__init__(expand=True)

        self._page   = page
        self.service = HistoricoService(session)
        self.limite  = 150
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
            label="Buscar na descrição",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._carregar,
        )

        self.dd_entidade = ft.Dropdown(
            label="Categoria",
            width=160,
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todas"),
                ft.dropdown.Option("venda",      "Venda"),
                ft.dropdown.Option("estoque",    "Estoque"),
                ft.dropdown.Option("financeiro", "Financeiro"),
                ft.dropdown.Option("item",       "Item"),
                ft.dropdown.Option("cliente",    "Cliente"),
            ],
        )
        self.dd_entidade.on_change = self._carregar

        self.dd_operacao = ft.Dropdown(
            label="Operação",
            width=160,
            value="todos",
            options=[
                ft.dropdown.Option("todos",     "Todas"),
                ft.dropdown.Option("criacao",   "Criação"),
                ft.dropdown.Option("edicao",    "Edição"),
                ft.dropdown.Option("exclusao",  "Exclusão"),
                ft.dropdown.Option("entrada",   "Entrada"),
                ft.dropdown.Option("ajuste",    "Ajuste"),
                ft.dropdown.Option("pagamento", "Pagamento"),
                ft.dropdown.Option("perda",     "Perda"),
            ],
        )
        self.dd_operacao.on_change = self._carregar

        self.lista = ft.Column(
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
                        ft.Text("Histórico", size=24, weight=ft.FontWeight.BOLD),
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
                        ft.Container(height=8),
                        ft.Container(
                            expand=True,
                            border=ft.Border(
                                left=ft.BorderSide(1, ft.Colors.GREY_300),
                                top=ft.BorderSide(1, ft.Colors.GREY_300),
                                right=ft.BorderSide(1, ft.Colors.GREY_300),
                                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
                            ),
                            border_radius=10,
                            content=self.lista,
                        ),
                    ],
                ),
            )
        ]

    # ==================================================
    # CARREGAR
    # ==================================================

    def _carregar(self, e=None):

        entidade = self.dd_entidade.value if self.dd_entidade.value != "todos" else None
        operacao = self.dd_operacao.value if self.dd_operacao.value != "todos" else None
        descricao = self.tf_busca.value.strip() or None

        registros = self.service.buscar(
            limite=self.limite,
            entidade=entidade,
            operacao=operacao,
            descricao=descricao,
        )

        itens = []

        # Cabeçalho
        itens.append(
            ft.Container(
                bgcolor=ft.Colors.GREY_100,
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                content=ft.Row(
                    controls=[
                        ft.Text("Data",      width=150, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Text("Categoria", width=110, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Text("Operação",  width=110, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Text("O que aconteceu", expand=True, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ]
                ),
            )
        )

        if not registros:
            itens.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("Nenhum registro encontrado.", color=ft.Colors.GREY_500),
                )
            )

        for i, h in enumerate(registros):
            diff = _build_diff(h.valor_antes, h.valor_depois)

            # Conteúdo principal da linha
            conteudo_direito = ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    ft.Text(
                        h.descricao,
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.GREY_800,
                    ),
                    *([diff] if diff else []),
                ],
            )

            linha = ft.Container(
                padding=ft.Padding(left=12, top=10, right=12, bottom=10),
                bgcolor=ft.Colors.WHITE if i % 2 == 0 else ft.Colors.GREY_50,
                border=ft.Border(
                    bottom=ft.BorderSide(1, ft.Colors.GREY_200)
                ),
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text(
                            h.data.strftime("%d/%m/%Y %H:%M"),
                            width=150,
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Container(
                            width=110,
                            content=_badge_entidade(h.entidade),
                        ),
                        ft.Container(
                            width=110,
                            content=_badge_operacao(h.operacao),
                        ),
                        conteudo_direito,
                    ],
                ),
            )

            itens.append(linha)

        self.lista.controls = itens
        if self._montado:
            self.update()