import pathlib
import yaml

from datetime import datetime
from dateutil.relativedelta import relativedelta

class Extrator:
    
    def _parse_valor(self, value: str) -> float:
        value = value.replace(".", "").replace(",", ".")  # Handle thousands and decimal separator
        return float(value)

    def _parse_data(self, value: str) -> datetime:
        today = datetime.today()
       
        patterns = [
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%d/%m %H:%M",
            "%d/%m"
        ]
        
        for pattern in patterns:
            try:
                parsed_date = datetime.strptime(value, pattern)
                
                if pattern == "%d/%m" or pattern == "%d/%m %H:%M":
                    year = today.year if parsed_date.month <= today.month else today.year - 1
                    parsed_date = parsed_date.replace(year=year)
                
                return parsed_date
            
            except ValueError:
                continue
        
        raise ValueError(f"Data não reconhecida: '{value}'")
    
    def _extrair_parcela(self, value, transacao):
        if value is None:
            return
        parcela = int(value.split("/")[0])
        transacao['data'] = transacao['data'] + relativedelta(months=parcela  -1)
        transacao['data_lancamento'] = transacao['data']
    
    def _extrair_tipo_transacao(self, descr, transacao, tipo_default = None):
        transacao["descr_tipo"] = descr
        try:
            transacao["tipo"] = self.marcadores_tipos_transacao[
                [key for key in self.marcadores_tipos_transacao.keys() if key in descr][0]
            ]
        except:
            if tipo_default:
                transacao["tipo"] = tipo_default
            else:
                raise ValueError(f"Tipo de transação não identificado: {descr}")

    def _processar_tipo_transacao(self, transacao, transacoes):
        processador = self.processadores_tipo_transacao.get(transacao["tipo"])
        if processador:
            processador(transacao, transacoes)

    def _carregar_config(self):
        module_name = self.__class__.__module__.split('.')[-1]
        config_path = pathlib.Path("config", "extrator") / f"{module_name}.yaml"

        with open(config_path, "r") as file:
            config_data = yaml.safe_load(file)

        return config_data
    
    def _is_transacao_ignoravel_por_configuracao(self, transacao):
        config = self._carregar_config()
        transacoes_ignorar = config.get("transacoes_ignorar", {})
        if not transacao["tipo"].value in transacoes_ignorar.get("tipo", []):
            return False
        transacao_descr_lower = transacao["descr"].lower()
        if not any(descr.lower() in transacao_descr_lower for descr in transacoes_ignorar.get("descr", [])):
            return False
        return True
    
    def _remover_transacao_por_config_se_necessario(self, transacao, transacoes):
        if transacao in transacoes and self._is_transacao_ignoravel_por_configuracao(transacao):
            transacoes.remove(transacao)
