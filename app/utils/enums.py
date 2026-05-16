
from enum import Enum


class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste = "ajuste"
    perda = "perda"

class TipoFinanceiro(str, Enum):
    receita = "receita"
    despesa = "despesa"

class TipoPagamento(str, Enum):
    dinheiro = "dinheiro"
    debito = "debito"
    credito = "credito"
    pix = "pix"