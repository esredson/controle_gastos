
from datetime import datetime
import io
import re

from extrator.extrator import Extrator
from tipo_transacao import TipoTransacao

class CreditoBB(Extrator):

    @staticmethod
    def pode_usar(txt):
        return "Resumo da fatura" in txt
    
    def __init__(self, txt):
        self.text = txt
        self.marcadores_tipos_transacao = {
            "PGTO DEBITO CONTA": TipoTransacao.PAGTO_FATURA_CREDITO
        }
        self.processadores_tipo_transacao = {
            TipoTransacao.PAGTO_FATURA_CREDITO: self._processar_pagto_fatura_credito
        }

        self.pattern = re.compile(
            r"(?P<data>\d{2}/\d{2})\s{5}"
            r"(?P<descr>.+?)"
            r"(\s{5}Parcela (?P<parcela>\d{2}/\d{2}))?"
            r"\s{7}BR\s{5}"
            r"(?P<valor>-?[\d\-,.]+)"
        )

    def extrair(self):
        text_stream = io.StringIO(self.text)

        transacoes = []

        for line in text_stream:
            match = self.pattern.match(line.strip())
            if not match:
                continue
            transacao = {}
            transacao['data'] = self._parse_data(match.group("data"))
            transacao['valor'] = self._parse_valor(match.group("valor"))         
            
            self._extrair_parcela(match.group("parcela"), transacao)

            transacoes.append(transacao)

            self._extrair_tipo_transacao(match.group("descr"), transacao, TipoTransacao.CREDITO)
            self._processar_tipo_transacao(transacao, transacoes)

        return transacoes

    def _processar_pagto_fatura_credito(self, transacao, transacoes):
        transacoes.remove(transacao)