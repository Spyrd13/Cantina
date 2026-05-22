# -*- coding: utf-8 -*-
import flet as ft
from datetime import datetime, timedelta
import json
from pyperclip import copy

from app.services.relatorio_services import RelatorioService
from app.services.cliente_services import ClienteService


class RelatorioView(ft.Column):

    def __init__(self, session, page):
        super().__init__(expand=True, spacing=10)

        self._page = page

        self.service = RelatorioService(session)
        self.cliente_service = ClienteService(session)

        self._clientes_map = {
            c.id: c.nome for c in self.cliente_service.listar_todos()
        }

        self._build()
        self._gerar(None)

    def _build(self):

        self.txt = ft.TextField(
            multiline=True,
            read_only=True,
            expand=True,
        )

        btn = ft.FilledButton(
            "Gerar relatório",
            icon=ft.Icons.REFRESH,
            on_click=self._gerar
        )

        btn_copy = ft.FilledButton(
            "Copiar",
            icon=ft.Icons.CONTENT_COPY,
            on_click=self._copiar
        )

        self.controls = [
            ft.Text("📊 Relatório do Dia", size=22, weight=ft.FontWeight.BOLD),
            ft.Row([btn, btn_copy]),
            self.txt
        ]

    def _gerar(self, e=None):

        inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fim = inicio + timedelta(days=1)

        r = self.service.gerar(inicio, fim)

        texto = []

        texto.append("📊 RELATÓRIO DO DIA")
        texto.append(f"Data: {inicio.strftime('%d/%m/%Y')}")
        texto.append("")
        texto.append("🛒 ITENS VENDIDOS")

        for nome, d in r["itens"].items():
            texto.append(f"- {nome}: {d['qtd']}x | R$ {d['valor']:.2f}")

        texto.append("")
        texto.append("💰 RESUMO FINANCEIRO")
        texto.append(f"Total vendas: R$ {r['total_vendas']:.2f}")
        texto.append(f"Dinheiro: R$ {r['dinheiro']:.2f}")
        texto.append(f"Débito: R$ {r['debito']:.2f}")
        texto.append(f"Crédito: R$ {r['credito']:.2f}")
        texto.append(f"Pix: R$ {r['pix']:.2f}")
        texto.append(f"Pendurado total: R$ {r['pendurado_total']:.2f}")

        texto.append("")
        texto.append("🧾 PENDURADOS POR CLIENTE")

        for cid, valor in r["pendurado_por_cliente"].items():
            nome = self._clientes_map.get(cid, f"#{cid}")
            texto.append(f"- {nome}: R$ {valor:.2f}")

        self.txt.value = "\n".join(texto)
        self._page.update()

    def _copiar(self, e):
        text = self.txt.value or ""
        
        try:
            # Garante encoding UTF-8 correto
            text = text.encode('utf-8', errors='replace').decode('utf-8')
            
            import pyperclip
            pyperclip.copy(text)
            self.show_snack_bar("Relatório copiado! ✓")
        except:
            try:
                import subprocess
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                self.show_snack_bar("Relatório copiado! ✓")
            except Exception as ex:
                self.show_snack_bar(f"Erro ao copiar: {str(ex)}")

    def show_snack_bar(self, message):
        snack = ft.SnackBar(ft.Text(message))
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()