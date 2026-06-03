import logging
import flet as ft
from sqlmodel import Session
from app.core.database import engine, init_db

logger = logging.getLogger(__name__)


def main(page: ft.Page):
    try:
        page.title = "Cantina TUFI"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0

        content = ft.Container(expand=True)
        session = Session(engine)

        def navegar(view):
            content.content = view
            page.update()

        def on_nav_change(e):
            try:
                index = e.control.selected_index
                if index == 0:
                    from app.views.vendas_view import VendasView
                    navegar(VendasView(session, page))
                elif index == 1:
                    from app.views.estoque_view import EstoqueView
                    navegar(EstoqueView(session, page))
                elif index == 2:
                    from app.views.items_view import ItemsView
                    navegar(ItemsView(session, page))
                elif index == 3:
                    from app.views.clientes_view import ClientesView
                    navegar(ClientesView(session, page))
                elif index == 4:
                    from app.views.financeiro_view import FinanceiroView
                    navegar(FinanceiroView(session, page))
                elif index == 5:
                    from app.views.historico_view import HistoricoView
                    navegar(HistoricoView(session, page))
                elif index == 6:
                    from app.views.relatorio_view import RelatorioView
                    navegar(RelatorioView(session, page))
            except Exception as ex:
                logger.error(f"Erro ao navegar: {ex}", exc_info=True)
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao carregar página: {str(ex)}"))
                page.snack_bar.open = True
                page.update()

        page.on_close = lambda e: session.close()

        nav = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            bgcolor=ft.Colors.GREEN_200,
            indicator_color=ft.Colors.BLUE_400,
            pin_trailing_to_bottom=True,  # 👈 fixa o trailing no rodapé
            trailing=ft.Container(
                content=ft.Text(
                    "by Rodrigo Assis",
                    size=11,
                    color=ft.Colors.GREEN_900,
                    italic=True,
                ),
                padding=ft.Padding(left=0, top=0, right=0, bottom=10),
            ),
        
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
                ft.NavigationRailDestination(
                    icon=ft.Icons.HISTORY,
                    selected_icon=ft.Icons.HISTORY,
                    label="Histórico",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INSIGHTS_OUTLINED,
                    selected_icon=ft.Icons.INSIGHTS,
                    label="Relatório",
                ),
            ],
            on_change=on_nav_change,
        )

        from app.views.vendas_view import VendasView
        content.content = VendasView(session, page)

        page.add(
            ft.Row(
                controls=[nav, ft.VerticalDivider(width=1), content],
                expand=True,
                spacing=0,
            )
        )

        logger.info("Aplicação Cantina TUFI iniciada com sucesso")

    except Exception as ex:
        logger.error(f"Erro fatal ao inicializar aplicação: {ex}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        init_db()
        ft.run(main)
    except Exception as ex:
        logger.error(f"Erro ao executar aplicação: {ex}", exc_info=True)
        raise
