
import io
import re

from extrator.extrator import Extrator
from tipo_transacao import TipoTransacao

class DebitoBradesco(Extrator):

    @staticmethod
    def pode_usar(txt):
        return "Bradesco Celular" in txt
    
    def __init__(self, txt):
        self.text = txt
        self.pattern_linha_1 = re.compile(
            r"(?P<data>\d{2}/\d{2}/\d{4})?(?P<descr>.+)"
        )
        self.pattern_linha_2 = re.compile(
            r"(?P<descr>.+?)"
            r"(?:\s(?P<data>\d{2}/\d{2}))?"
            r"(?:\d{7})\s+"
            r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
            r"(?:\d{1,3}(?:\.\d{3})*,\d{2})"
        )
        self.pattern_linha_unica = re.compile(
            r"(?:(?P<data>\d{2}/\d{2}/\d{4})\s)?(?P<descr>.+?)"
            r"(?:\d{7})\s+"
            r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
            r"(?:\d{1,3}(?:\.\d{3})*,\d{2})"
        )
        self.linhas_desconsiderar = [
            "Bradesco Celular",
            "Data:",
            "Nome:",
            "Extrato de:",
            "Data Histórico Docto",
            "Total "
        ]
        self.marcadores_tipos_transacao = {
            "PIX": TipoTransacao.PIX,
            "TED DIF.TITUL.CC H.BANK": TipoTransacao.TED,
            "TED-TRANSF ELET DISPON": TipoTransacao.TED,
            "CONTA DE": TipoTransacao.PAGTO_BOLETO,
            "PAGTO ELETRON": TipoTransacao.PAGTO_BOLETO,
            "CARTAO VISA": TipoTransacao.DEBITO,
            "IOF ": TipoTransacao.TAXA_BANCO,
            "TRANSF SALDO C/SAL P/CC": TipoTransacao.SALARIO,
            "GASTOS CARTAO": TipoTransacao.PAGTO_FATURA_CREDITO,
            "APLIC/RESG": TipoTransacao.APLICACAO_RESGATE,
            "APLICACAO EM FUNDOS": TipoTransacao.APLICACAO_RESGATE,
            "SAQUE": TipoTransacao.SAQUE,
            "RENDIMENTOS": TipoTransacao.RENDIMENTO,
        }
        self.processadores_tipo_transacao = {
            TipoTransacao.PIX: self._processar_pix,
            TipoTransacao.SALARIO: self._processar_salario,
            TipoTransacao.RENDIMENTO: self._processar_rendimentos,
            TipoTransacao.PAGTO_FATURA_CREDITO: self._processar_pagto_fatura_credito,
            TipoTransacao.APLICACAO_RESGATE: self._processar_aplicacao_resgate,
            TipoTransacao.TED: self._processar_ted,
            TipoTransacao.SAQUE: self._processar_saque,
            TipoTransacao.PAGTO_BOLETO: self._processar_pagto_boleto
        }

    def extrair(self):
        text_stream = io.StringIO(self.text)

        transacoes = []

        # Evita confundir uma linha 2 com uma linha única, q tem o mesmo padrão, porém
        # só vai aparecer se uma linha 1 acabou de iniciar uma transação
        processando_transacao = False 
        
        for line in text_stream:
            if any(line.startswith(lixo) for lixo in self.linhas_desconsiderar):
                continue

            if processando_transacao and self._processar_linha_2(line, transacoes):
                processando_transacao = False
            elif self._processar_linha_unica(line, transacoes):
                processando_transacao = False
            elif self._processar_linha_1(line, transacoes):
                processando_transacao = True

        return transacoes

    def _processar_linha_1(self, line, transacoes):
        match = self.pattern_linha_1.match(line.strip())
        if not match:
            return False
        
        transacao = {}
        
        self._extrair_data_lancamento(match.group("data"), transacao, transacoes)
        self._extrair_tipo_transacao(match.group("descr"), transacao)        

        transacoes.append(transacao)

        return True
    
    def _processar_linha_2(self, line, transacoes):
        if len(transacoes) == 0:
            raise ValueError(f"Tentando iniciar a linha 2 sem que haja uma transação: {line}")
        
        match = self.pattern_linha_2.match(line.strip())
        if not match:
            return False
        
        transacao = transacoes[-1]

        self._extrair_data(match.group("data"), transacao)

        transacao['descr'] = match.group("descr")
        transacao['valor'] = self._parse_valor(match.group("valor"))

        self._processar_tipo_transacao(transacao, transacoes)
        self._remover_transacao_por_config_se_necessario(transacao, transacoes)

        return True
    
    def _processar_linha_unica(self, line, transacoes):
        match = self.pattern_linha_unica.match(line.strip())
        if not match:
            return False
        
        transacao = {}

        self._extrair_data_lancamento(match.group("data"), transacao, transacoes)
        self._extrair_data(match.group("data"), transacao)
        self._extrair_tipo_transacao(match.group("descr"), transacao)
        

        transacao["descr"] = match.group("descr")
        transacao['valor'] = self._parse_valor(match.group("valor"))

        transacoes.append(transacao)

        self._processar_tipo_transacao(transacao, transacoes)
        self._remover_transacao_por_config_se_necessario(transacao, transacoes)
        
        return True
    
    def _extrair_data_lancamento(self, data, transacao, transacoes):
        if data:
            transacao["data_lancamento"] = self._parse_data(data)
        else:
            transacao["data_lancamento"] = transacoes[-1]["data_lancamento"]

    def _extrair_data(self, data, transacao):
        if data:
            transacao["data"] = self._parse_data(data)
        else:
            transacao["data"] = transacao["data_lancamento"]

    def _processar_pix(self, transacao, transacoes):
        sentidos = {"DES": 1, "REM": -1}
        try:
            sentido = [key for key in sentidos.keys() if transacao["descr"].startswith(key)][0]
            transacao["valor"] *= sentidos[sentido]
            transacao["descr"] = transacao["descr"].replace(f"{sentido}: ", "")
        except: 
            raise ValueError(f"Transação PIX inválida: {transacao['descr']}")
        
    def _processar_salario(self, transacao, transacoes):
        transacao["valor"] *= -1
        transacao["descr"] = ""

    def _processar_rendimentos(self, transacao, transacoes):
        if not "ESTORNO" in transacao["descr_tipo"]:
            transacao["valor"] *= -1
        transacao["descr"] = ""

    def _processar_pagto_fatura_credito(self, transacao, transacoes):
        transacoes.remove(transacao)

    def _processar_aplicacao_resgate(self, transacao, transacoes):
        transacoes.remove(transacao)

    def _processar_ted(self, transacao, transacoes):
        sentidos = {"DEST": 1, "REMET": -1}
        try:
            sentido = [key for key in sentidos.keys() if transacao["descr"].startswith(key)][0]
            transacao["valor"] *= sentidos[sentido]
            transacao["descr"] = transacao["descr"].replace(f"{sentido}.", "").strip()
        except: 
            raise ValueError(f"Transação TED inválida: {transacao['descr']}")
        
        transacao["descr"] = transacao["descr"].replace("DEST. ", "")

    def _processar_pagto_boleto(self, transacao, transacoes):
        transacao["descr"] = transacao["descr_tipo"] + " " + transacao["descr"]

    def _processar_saque(self, transacao, transacoes):
        transacao["descr"] = ""