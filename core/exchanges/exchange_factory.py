from .mexc_adapter import MexcAdapter
from .binance_adapter import BinanceAdapter
# from .luno_adapter import LunoAdapter # TODO: Implement Luno

class ExchangeFactory:
    """
    Factory to create exchange adapters.
    """
    
    @staticmethod
    def create_adapter(exchange_name: str, mode: str = 'paper'):
        exchange_name = exchange_name.upper()
        
        if exchange_name == 'MEXC':
            return MexcAdapter(mode)
        elif exchange_name == 'BINANCE':
            return BinanceAdapter(mode)
        elif exchange_name == 'LUNO':
             # Return None or raise until implemented
             return None 
        else:
            raise ValueError(f"Unsupported Exchange: {exchange_name}")
