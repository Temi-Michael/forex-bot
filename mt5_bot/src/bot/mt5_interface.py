import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MT5Interface:
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        if not self.use_mock:
            try:
                import MetaTrader5 as mt5
                self.mt5 = mt5
            except ImportError:
                logging.warning("MetaTrader5 library not found. Assuming non-Windows or mock environment.")
                self.use_mock = True

        if self.use_mock:
            from bot.mock_mt5 import MockMT5
            self.mt5 = MockMT5()

    def initialize(self):
        if not self.mt5.initialize():
            logging.error("initialize() failed, error code =", self.mt5.last_error())
            return False
        logging.info("MT5 initialized successfully.")
        return True

    def shutdown(self):
        self.mt5.shutdown()

    def get_account_info(self):
        account_info = self.mt5.account_info()
        if account_info is None:
            logging.error(f"Failed to get account info, error code: {self.mt5.last_error()}")
            return None
        # Convert tuple/object to dict-like structure if needed, MT5 returns namedtuple
        return account_info._asdict() if hasattr(account_info, '_asdict') else account_info

    def get_symbol_info(self, symbol):
        symbol_info = self.mt5.symbol_info(symbol)
        if symbol_info is None:
            logging.error(f"Symbol {symbol} not found, error code: {self.mt5.last_error()}")
            return None
        if not symbol_info.visible:
            logging.info(f"{symbol} is not visible, trying to switch on")
            if not self.mt5.symbol_select(symbol, True):
                logging.error(f"symbol_select({symbol}) failed, error code: {self.mt5.last_error()}")
                return None
        return symbol_info

    def get_historical_data(self, symbol, timeframe, num_bars):
        """
        Timeframe should be an mt5 constant like mt5.TIMEFRAME_M1
        """
        rates = self.mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)
        if rates is None:
            logging.error(f"Failed to get historical data for {symbol}, error code: {self.mt5.last_error()}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def send_market_order(self, symbol, order_type, volume, price, sl=None, tp=None, magic=123456):
        """
        order_type: mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL
        """
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "deviation": 20, # Slip tolerance
            "magic": magic,
            "comment": "python script open",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC, # Usually safest for market orders
        }

        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)

        result = self.mt5.order_send(request)
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logging.error(f"Order failed, retcode={result.retcode}")
            return None

        logging.info(f"Order sent successfully: {result.dict()}")
        return result

    def get_open_positions(self, symbol=None):
        if symbol:
            positions = self.mt5.positions_get(symbol=symbol)
        else:
            positions = self.mt5.positions_get()

        if positions is None:
            logging.error(f"Failed to get positions, error code: {self.mt5.last_error()}")
            return []
        return positions
