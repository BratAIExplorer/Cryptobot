class BaseStrategy:
    def __init__(self, config):
        self.config = config
        self.name = config.get('name', 'Unknown Strategy')
        self.symbol = config.get('symbol', 'BTC/USDT')

    def generate_signal(self, df):
        """
        Analyze data and return a signal.
        Returns:
            dict: {'side': 'BUY'/'SELL', 'amount': float, 'reason': str} or None
        """
        raise NotImplementedError("Strategies must implement generate_signal")
