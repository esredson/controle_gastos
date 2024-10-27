
from datetime import datetime
import io
import re

from extrator.extrator import Extrator
from tipo_transacao import TipoTransacao

class DebitoBB(Extrator):

    @staticmethod
    def pode_usar(txt):
        return "Extrato de Conta Corrente" in txt
    
    def __init__(self, txt):
        self.text = txt
        self.pattern_linha_1 = re.compile(
            r"(?P<valor>[\d.]+,\d{2})\s\((?P<sinal>[+-])\)"
            r"(?P<data>\d{2}/\d{2}/\d{4})\s?"
            r"(?P<descr>.+)"
        )
        self.pattern_linha_2 = re.compile(
            r"(?:(?P<data>\d{2}/\d{2})\s)?"
            r"(?:(?P<hora>\d{2}:\d{2})\s)?"
            r"(?P<descr>.+)"
        )
        self.linhas_desconsiderar = [
            "Cliente:",
            "Agência:",
            "Lançamentos",
            "Dia Histórico",
            "Saldo Anterior",
        ]
        self.marcadores_tipos_transacao = {
            "Pix": TipoTransacao.PIX,
            "TEDpessoal": TipoTransacao.TAXA_BANCO,
            "TED": TipoTransacao.TED,
            "Pagamento ": TipoTransacao.PAGTO_BOLETO,
            "Pagto conta": TipoTransacao.PAGTO_BOLETO,
            "Compra com Cartão": TipoTransacao.DEBITO,
            "Cobrança de Juros": TipoTransacao.TAXA_BANCO,
            "Recebimento de Proventos": TipoTransacao.SALARIO,
            "Pagto cartão crédito": TipoTransacao.PAGTO_FATURA_CREDITO,
            "BB ": TipoTransacao.APLICACAO_RESGATE,
            "MM ": TipoTransacao.APLICACAO_RESGATE,
            "Dep dinheiro": TipoTransacao.SAQUE,
            "Depósito Online": TipoTransacao.SAQUE, 
        }

        self.processadores_tipo_transacao = {
            TipoTransacao.SALARIO: self._processar_salario,
            TipoTransacao.RENDIMENTO: self._processar_rendimentos,
            TipoTransacao.PAGTO_FATURA_CREDITO: self._processar_pagto_fatura_credito,
            TipoTransacao.APLICACAO_RESGATE: self._processar_aplicacao_resgate,
            TipoTransacao.SAQUE: self._processar_saque,
            TipoTransacao.PAGTO_BOLETO: self._processar_pagto_boleto
        }

    def extrair(self):
        text_stream = io.StringIO(self.text)

        transacoes = []
        for line in text_stream:
            line = line.replace("Extrato de Conta Corrente", "").strip()
            if not line:
                continue

            if any(lixo in line for lixo in self.linhas_desconsiderar):
                continue
            if "S A L D O" in line:
                break

            if not self._processar_linha_1(line, transacoes):
                self._processar_linha_2(line, transacoes)
                
        self._processar_transacao_anterior(transacoes)

        return transacoes

    def _processar_linha_1(self, line, transacoes):
        match = self.pattern_linha_1.match(line.strip())
        if not match:
            return False
        
        self._processar_transacao_anterior(transacoes)

        transacao = {}

        transacao['valor'] = self._parse_valor(match.group("sinal") + match.group("valor")) * -1
        transacao['data'] = transacao['data_lancamento'] = self._parse_data(match.group("data"))
        
        descr = match.group("descr")
        self._extrair_tipo_transacao(descr, transacao)

        transacoes.append(transacao)
        
        return True
    
    def _processar_linha_2(self, line, transacoes):
        if len(transacoes) == 0:
            raise ValueError(f"Tentando iniciar a linha 2 sem que haja uma transação: {line}")
        match = self.pattern_linha_2.match(line.strip())
        if not match:
            return False
        
        transacao = transacoes[-1]

        if match.group("data"):
            transacao['data'] = self._parse_data(match.group("data") + " " + match.group("hora"))
        
        transacao['descr'] = match.group("descr")
        
        return True
    
    # Este método é necessário pq, no caso do débito BB, só na linha seguinte é que se pode
    # saber se a transação tem uma segunda linha ou se fechou na primeira
    def _processar_transacao_anterior(self, transacoes):
        if len(transacoes) > 0:
            self._processar_tipo_transacao(transacoes[-1], transacoes)
            self._remover_transacao_por_config_se_necessario(transacoes[-1], transacoes)
        
    def _processar_salario(self, transacao, transacoes):
        transacao["descr"] = ""

    def _processar_rendimentos(self, transacao, transacoes):
        transacao["descr"] = ""

    def _processar_pagto_fatura_credito(self, transacao, transacoes):
        transacoes.remove(transacao)

    def _processar_aplicacao_resgate(self, transacao, transacoes):
        transacoes.remove(transacao)

    def _processar_pagto_boleto(self, transacao, transacoes):
        transacao["descr"] = transacao["descr_tipo"] + " " + transacao["descr"]

    def _processar_saque(self, transacao, transacoes):
        transacao["descr"] = ""

    def _processar_taxa_banco(self, transacao, transacoes):
        transacao["descr"] = transacao["descr_tipo"] + " " + transacao["descr"]