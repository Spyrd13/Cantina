import logging
from pathlib import Path
import flet as ft
from sqlmodel import Session
from app.core.database import engine, init_db
from app.models import Cliente, Financeiro, Item, Movimentacao, Historico

logger = logging.getLogger(__name__)
# Ensure a file handler exists for detailed logs
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

log_file = Path(__file__).parent / "tufi.log"
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logging.getLogger().addHandler(file_handler)


def main(page: ft.Page):
    try:
        page.title = "Cantina TUFI"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0
        page.window.icon = "favicon.ico"

        content = ft.Container(expand=True)
        session = Session(engine)

        def navegar(view):
            content.content = view
            page.update()

        def on_nav_change(e):
            try:
                # O index funciona igual tanto para o Rail quanto para a NavigationBar
                index = e.control.selected_index
                
                # Sincroniza os dois menus para mudarem juntos se a tela for redimensionada
                nav_rail.selected_index = index
                nav_bar.selected_index = index
                
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

        # 1. MENU LATERAL (Para PC/Tablet)
        nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            bgcolor=ft.Colors.GREEN_200,
            indicator_color=ft.Colors.BLUE_400,
            pin_trailing_to_bottom=True,
            trailing=ft.Container(
                content=ft.Text("by Rodrigo Assis", size=11, color=ft.Colors.GREEN_900, italic=True),
                padding=ft.Padding(left=0, top=0, right=0, bottom=10),
            ),
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.POINT_OF_SALE_OUTLINED, selected_icon=ft.Icons.POINT_OF_SALE, label="Vendas"),
                ft.NavigationRailDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label="Estoque"),
                ft.NavigationRailDestination(icon=ft.Icons.FASTFOOD_OUTLINED, selected_icon=ft.Icons.FASTFOOD, label="Itens"),
                ft.NavigationRailDestination(icon=ft.Icons.PEOPLE_OUTLINED, selected_icon=ft.Icons.PEOPLE, label="Clientes"),
                ft.NavigationRailDestination(icon=ft.Icons.ATTACH_MONEY_OUTLINED, selected_icon=ft.Icons.ATTACH_MONEY, label="Financeiro"),
                ft.NavigationRailDestination(icon=ft.Icons.HISTORY, selected_icon=ft.Icons.HISTORY, label="Histórico"),
                ft.NavigationRailDestination(icon=ft.Icons.INSIGHTS_OUTLINED, selected_icon=ft.Icons.INSIGHTS, label="Relatório"),
            ],
            on_change=on_nav_change,
        )

        # 2. MENU INFERIOR (Para Celular)
        nav_bar = ft.NavigationBar(
            selected_index=0,
            bgcolor=ft.Colors.GREEN_200,
            indicator_color=ft.Colors.BLUE_400,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.POINT_OF_SALE_OUTLINED, selected_icon=ft.Icons.POINT_OF_SALE, label="Vendas"),
                ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label="Estoque"),
                ft.NavigationBarDestination(icon=ft.Icons.FASTFOOD_OUTLINED, selected_icon=ft.Icons.FASTFOOD, label="Itens"),
                ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINED, selected_icon=ft.Icons.PEOPLE, label="Clientes"),
                ft.NavigationBarDestination(icon=ft.Icons.ATTACH_MONEY_OUTLINED, selected_icon=ft.Icons.ATTACH_MONEY, label="Finan."),
                ft.NavigationBarDestination(icon=ft.Icons.HISTORY, selected_icon=ft.Icons.HISTORY, label="Hist."),
                ft.NavigationBarDestination(icon=ft.Icons.INSIGHTS_OUTLINED, selected_icon=ft.Icons.INSIGHTS, label="Relat."),
            ],
            on_change=on_nav_change,
        )

        # Container principal que segura o Menu Lateral + Conteúdo
        layout_row = ft.Row(
            controls=[nav_rail, ft.VerticalDivider(width=1), content],
            expand=True,
            spacing=0,
        )

        # Carrega a view inicial
        from app.views.vendas_view import VendasView
        content.content = VendasView(session, page)

        # 3. A FUNÇÃO MÁGICA DA RESPONSIVIDADE
        def redimensionar(e):
            # 500 a 600 pixels é o limite padrão para celulares em pé
            if page.width < 600:
                # Modo Celular: Esconde menu lateral, mostra menu inferior
                nav_rail.visible = False
                page.navigation_bar = nav_bar
            else:
                # Modo PC/Tablet: Mostra menu lateral, remove menu inferior
                nav_rail.visible = True
                page.navigation_bar = None
            page.update()

        # Vincula o evento de mudança de tamanho de tela à função
        page.on_resize = redimensionar
        
        # Executa uma vez no início para definir o layout correto de abertura
        redimensionar(None)

        # Adiciona o layout na página
        page.add(layout_row)

        logger.info("Aplicação Cantina TUFI iniciada com sucesso")

    except Exception as ex:
        logger.error(f"Erro fatal ao inicializar aplicação: {ex}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        init_db()
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            assets_dir="assets",
        )
    except Exception as ex:
        logger.error(f"Erro ao executar aplicação: {ex}", exc_info=True)
        raise
