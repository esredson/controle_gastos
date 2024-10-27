from enum import Enum

class TipoTransacao(Enum):
    PIX = "PIX"
    TED = "TED"
    DEBITO = "Débito"
    CREDITO = "Crédito"
    TAXA_BANCO = "Taxa banco"
    SALARIO = "Salário"
    PAGTO_BOLETO = "Pagto boleto"
    APLICACAO_RESGATE = "Aplicação/resgate"
    RENDIMENTO = "Rendimento"
    SAQUE = "Saque"
    PAGTO_FATURA_CREDITO = "Pagto fatura crédito"
