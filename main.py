import flet as ft
from sqlmodel import Session
from app.core.database import engine
from app.views.items_view import ItemsView
from app.views.clientes_view import ClientesView
from app.views.vendas_view import VendasView
from app.views.estoque_view import EstoqueView
from app.views.financeiro_view import FinanceiroView


def main(page: ft.Page):
    page.title = "Cantina TUFI"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    content = ft.Container(expand=True)

    def navegar(view):
        content.content = view
        page.update()

    def on_nav_change(e):
        index = e.control.selected_index
        with Session(engine) as session:
            if index == 0:
                navegar(VendasView(session, page))
            elif index == 1:
                navegar(EstoqueView(session, page))
            elif index == 2:
                navegar(ItemsView(session, page))
            elif index == 3:
                navegar(ClientesView(session, page))
            elif index == 4:
                navegar(FinanceiroView(session, page))

    nav = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        bgcolor=ft.Colors.GREEN_200,
        indicator_color=ft.Colors.BLUE_400,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.POINT_OF_SALE_OUTLINED,
                selected_icon=ft.Icons.POINT_OF_SALE,
                label="Vendas",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                selected_icon=ft.Icons.INVENTORY_2,
                label="Estoque",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.FASTFOOD_OUTLINED,
                selected_icon=ft.Icons.FASTFOOD,
                label="Itens",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINED,
                selected_icon=ft.Icons.PEOPLE,
                label="Clientes",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ATTACH_MONEY_OUTLINED,
                selected_icon=ft.Icons.ATTACH_MONEY,
                label="Financeiro",
            ),
        ],
        on_change=on_nav_change,
    )

    with Session(engine) as session:
        content.content = VendasView(session, page)

    page.add(
        ft.Row(
            controls=[nav, ft.VerticalDivider(width=1), content],
            expand=True,
            spacing=0,
        )
    )


ft.run(main)