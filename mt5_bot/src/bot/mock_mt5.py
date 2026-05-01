import numpy as np
import time
from datetime import datetime, timedelta

class MockAccountInfo:
    def __init__(self):
        self.balance = 100.0
        self.equity = 100.0
        self.margin_free = 100.0

    def _asdict(self):
        return {
            "balance": self.balance,
            "equity": self.equity,
            "margin_free": self.margin_free
        }

class MockSymbolInfo:
    def __init__(self, symbol):
        self.name = symbol
        self.visible = True
        self.ask = 1.1000
        self.bid = 1.0998
        self.point = 0.00001
        self.trade_calc_mode = 0 # forex

class MockOrderResult:
    def __init__(self, request):
        self.retcode = 10009 # TRADE_RETCODE_DONE
        self.request = request
        self.order = int(time.time())
        self.price = request['price']
        self.volume = request['volume']

    def dict(self):
        return {
            "retcode": self.retcode,
            "order": self.order,
            "price": self.price,
            "volume": self.volume
        }

class MockPosition:
    def __init__(self, ticket, symbol, type, volume, price_open, sl, tp):
        self.ticket = ticket
        self.symbol = symbol
        self.type = type
        self.volume = volume
        self.price_open = price_open
        self.sl = sl
        self.tp = tp

class MockMT5:
    def __init__(self):
        self.TIMEFRAME_M1 = 1
        self.TIMEFRAME_M5 = 5
        self.ORDER_TYPE_BUY = 0
        self.ORDER_TYPE_SELL = 1
        self.TRADE_ACTION_DEAL = 1
        self.ORDER_TIME_GTC = 0
        self.ORDER_FILLING_IOC = 1
        self.TRADE_RETCODE_DONE = 10009

        self._positions = []
        self._last_error = (1, "Success")
        self._current_price = 1.1000
        self._mock_data_index = 0

    def initialize(self):
        return True

    def shutdown(self):
        pass

    def last_error(self):
        return self._last_error

    def account_info(self):
        return MockAccountInfo()

    def symbol_info(self, symbol):
        return MockSymbolInfo(symbol)

    def symbol_select(self, symbol, select):
        return True

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        # Generate some dummy wave data for testing strategy
        # Creates a sine wave pattern for prices to trigger both buy and sell
        base_time = int(time.time()) - (count * 60)
        rates = []
        for i in range(count):
            idx = self._mock_data_index + i
            # Create a wave between 1.0900 and 1.1100
            price_wave = 1.1000 + np.sin(idx / 10.0) * 0.01

            # Add some randomness
            high = price_wave + 0.0005
            low = price_wave - 0.0005

            rates.append({
                'time': base_time + (i * 60),
                'open': price_wave,
                'high': high,
                'low': low,
                'close': price_wave + np.random.uniform(-0.0002, 0.0002),
                'tick_volume': 100,
                'spread': 2,
                'real_volume': 0
            })

        # Update price for order execution
        self._current_price = rates[-1]['close']
        # Advance time for next call
        self._mock_data_index += 1

        # return structured array like real MT5
        dtype = [('time', '<i8'), ('open', '<f8'), ('high', '<f8'), ('low', '<f8'),
                 ('close', '<f8'), ('tick_volume', '<u8'), ('spread', '<i4'), ('real_volume', '<u8')]
        return np.array([tuple(r.values()) for r in rates], dtype=dtype)

    def order_send(self, request):
        if 'sl' not in request or 'tp' not in request:
            # Enforce strict SL/TP for scalping even in mock
            pass

        res = MockOrderResult(request)

        # Add to positions
        pos = MockPosition(
            ticket=res.order,
            symbol=request['symbol'],
            type=request['type'],
            volume=request['volume'],
            price_open=request['price'],
            sl=request.get('sl', 0.0),
            tp=request.get('tp', 0.0)
        )
        self._positions.append(pos)

        return res

    def positions_get(self, symbol=None):
        if symbol:
            return [p for p in self._positions if p.symbol == symbol]
        return self._positions

    def _simulate_market_movement(self, close_ticket=None):
        """Helper to clear positions for testing"""
        if close_ticket is not None:
            self._positions = [p for p in self._positions if p.ticket != close_ticket]
        else:
            self._positions = []
