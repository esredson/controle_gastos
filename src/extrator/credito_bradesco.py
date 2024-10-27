
from datetime import datetime
import io
import re

from extrator.extrator import Extrator
from tipo_transacao import TipoTransacao

class CreditoBradesco(Extrator):

    @staticmethod
    def pode_usar(txt):
        return "Resumo das Despesas" in txt
    
    def __init__(self, txt):
        self.text = txt
        self.marcadores_tipos_transacao = {
            "PAGTO. POR DEB EM C/C": TipoTransacao.PAGTO_FATURA_CREDITO
        }
        self.processadores_tipo_transacao = {
            TipoTransacao.PAGTO_FATURA_CREDITO: self._processar_pagto_fatura_credito
        }
        self.pattern = re.compile(
            r"(?P<data>\d{2}/\d{2})"
            r"(?P<descr>.+?)\s"
            r"(?P<valor>(?:\d{1,2}(?:\.\d{3}){0,2}|\d{1,3})(,\d{2}))(?P<sinal>\s-)?"
        )
        self.pattern_parcela = re.compile(r".*?(?P<parcela>\d{2}/\d{2}).*?")

    def extrair(self):
        text_stream = io.StringIO(self.text)

        transacoes = []

        for line in text_stream:
            match = self.pattern.match(line.strip())
            if not match:
                continue
            transacao = {}
            transacao['data'] = self._parse_data(match.group("data"))
            transacao['valor'] = self._parse_valor((match.group("sinal") or "") + match.group("valor"))

            descr, parcela = self._parse_descricao(match.group("descr"))
            self._extrair_parcela(parcela, transacao)

            transacoes.append(transacao)

            self._extrair_tipo_transacao(descr, transacao, TipoTransacao.CREDITO)
            self._processar_tipo_transacao(transacao, transacoes)

        return transacoes

    def _parse_descricao(self, descr):
        match = self.pattern_parcela.match(descr.strip())
        parcela = match.group("parcela") if match else None
        return (
            descr.replace(parcela, "") if parcela else descr,
            parcela
        )
    
    def _processar_pagto_fatura_credito(self, transacao, transacoes):
        transacoes.remove(transacao)