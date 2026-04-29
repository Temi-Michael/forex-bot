import time
import logging
from bot.mt5_interface import MT5Interface
from bot.strategy import Strategy
import bot.config as config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self, use_mock=False):
        self.mt5 = MT5Interface(use_mock=use_mock)
        self.strategy = Strategy(config)
        self.symbol = config.SYMBOL
        self.timeframe = self.mt5.mt5.TIMEFRAME_M1 if config.TIMEFRAME_MINUTES == 1 else self.mt5.mt5.TIMEFRAME_M5
        self.is_running = False

    def start(self):
        if not self.mt5.initialize():
            logging.error("Failed to initialize MT5")
            return

        # Ensure symbol is available
        symbol_info = self.mt5.get_symbol_info(self.symbol)
        if not symbol_info:
            logging.error(f"Symbol {self.symbol} is not available")
            return

        logging.info(f"Started Scalping Bot for {self.symbol}")
        self.is_running = True
        self.run_loop()

    def stop(self):
        self.is_running = False
        self.mt5.shutdown()
        logging.info("Bot stopped.")

    def run_loop(self):
        while self.is_running:
            try:
                self.process_tick()
                # For a 1-minute chart, checking every few seconds is sufficient to catch the close
                # But to avoid API spam, we sleep 5 seconds
                time.sleep(5)
            except KeyboardInterrupt:
                logging.info("Keyboard interrupt received. Stopping...")
                self.stop()
            except Exception as e:
                logging.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(10)

    def process_tick(self):
        # 1. Check open positions to ensure we only have max 1 trade at a time
        positions = self.mt5.get_open_positions(self.symbol)

        # Risk Management: Only 1 trade at a time for the $100 capital
        if len(positions) > 0:
            # We already have an open trade. We just wait for SL or TP to hit.
            # In a more advanced bot, we could trail the stop loss here.
            return

        # 2. Get Historical Data
        # We need enough bars for the Slow EMA and ATR calculation (e.g., 50 bars)
        df = self.mt5.get_historical_data(self.symbol, self.timeframe, 50)
        if df.empty:
            return

        # 3. Calculate Indicators
        df = self.strategy.calculate_indicators(df)

        # 4. Get Signal
        signal = self.strategy.get_signal(df)
        if not signal:
            return

        # 5. Execute Trade
        logging.info(f"Signal generated: {signal}")

        # Get current price
        symbol_info = self.mt5.get_symbol_info(self.symbol)
        if signal == 'BUY':
            current_price = symbol_info.ask
            order_type = self.mt5.mt5.ORDER_TYPE_BUY
        else:
            current_price = symbol_info.bid
            order_type = self.mt5.mt5.ORDER_TYPE_SELL

        # Get ATR value from the last closed candle
        atr_value = df.iloc[-1]['atr']

        # Calculate Dynamic SL and TP
        sl, tp = self.strategy.calculate_sl_tp(signal, current_price, atr_value)

        logging.info(f"Executing {signal} at {current_price}. SL: {sl}, TP: {tp}")

        self.mt5.send_market_order(
            symbol=self.symbol,
            order_type=order_type,
            volume=config.TRADE_VOLUME,
            price=current_price,
            sl=sl,
            tp=tp,
            magic=config.MAGIC_NUMBER
        )
