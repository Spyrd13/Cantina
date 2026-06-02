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

        self.field_inicio = ft.TextField(
            label="Data início",
            hint_text="dd/mm/aaaa",
            width=180,
        )

        self.field_fim = ft.TextField(
            label="Data fim",
            hint_text="dd/mm/aaaa",
            width=180,
        )

        hoje = datetime.now().strftime("%d/%m/%Y")

        self.field_inicio.value = hoje
        self.field_fim.value = hoje

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
            ft.Row([
                self.field_inicio,
                self.field_fim,
                btn,
                btn_copy,
            ]),
            self.txt
        ]

    def _gerar(self, e=None):

        try:

            inicio = datetime.strptime(
                self.field_inicio.value,
                "%d/%m/%Y"
            )

            fim = datetime.strptime(
                self.field_fim.value,
                "%d/%m/%Y"
            )

            inicio = inicio.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            fim = fim.replace(
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
            )

        except ValueError:

            self.show_snack_bar(
                "Datas inválidas. Use dd/mm/aaaa"
            )

            return

        r = self.service.gerar(inicio, fim)

        texto = []

        texto.append("📊 RELATÓRIO DO DIA")
        texto.append(
            f"Período: "
            f"{inicio.strftime('%d/%m/%Y')} até "
            f"{fim.strftime('%d/%m/%Y')}"
        )
        texto.append("")
        texto.append("🛒 ITENS VENDIDOS")

        for nome, d in r["itens"].items():
            texto.append(f"- {nome}: {d['qtd']}x | R$ {d['valor']:.2f}")

        total_recebido = (
            r["dinheiro"]
            + r["debito"]
            + r["credito"]
            + r["pix"]
        )

        texto.append("")
        texto.append("💰 RESUMO FINANCEIRO")
        texto.append(f"Total vendido: R$ {r['total_vendas']:.2f}")

        texto.append("")
        texto.append("Recebido:")
        texto.append(f"- Dinheiro: R$ {r['dinheiro']:.2f}")
        texto.append(f"- Débito: R$ {r['debito']:.2f}")
        texto.append(f"- Crédito: R$ {r['credito']:.2f}")
        texto.append(f"- Pix: R$ {r['pix']:.2f}")
        texto.append(f"- Pendurado: R$ {r['pendurado_total']:.2f}")

        texto.append("")
        texto.append(f"Total recebido: R$ {total_recebido:.2f}")
        texto.append(f"Saldo pendente: R$ {r['pendurado_total']:.2f}")

        texto.append("")
        texto.append("🧾 PENDURADOS POR CLIENTE")

        for cid, d in r["clientes"].items():
            if cid is None:
                nome = "❌ SEM CLIENTE (erro de dados)"
            else:
                nome = self._clientes_map.get(cid, f"#{cid}")
            status_pago = "✔" if d["saldo"] <= 0 else "✘"

            texto.append(
                f"- {nome} | "
                f"Total: R$ {d['total']:.2f} | "
                f"Saldo: R$ {d['saldo']:.2f} | "
                f"Pago: {status_pago}"
            )

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