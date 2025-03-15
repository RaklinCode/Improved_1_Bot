import ccxt.async_support as ccxt  # Use asynchronous ccxt
import asyncio
import csv
from datetime import datetime
import pandas as pd
import numpy as np
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



def check_trade_signal(df):
    """Determine buy/sell signal based on EMA crossover and RSI."""
    latest = df.iloc[-1]
    if latest['ema_9'] > latest['ema_21'] and latest['rsi'] < 30:
        return 'buy'
    elif latest['ema_9'] < latest['ema_21'] and latest['rsi'] > 70:
        return 'sell'
    return None


class OptimizedTradingBot:
    def __init__(self, api_key, secret, leverage, investment_balance, stop_loss_pct, take_profit_pct, symbol, timeframe):
        self.api_key = api_key
        self.secret = secret
        self.leverage = leverage
        self.investment_balance = investment_balance
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange = None
        self.open_orders = []
        self.log_file = 'trade_log.csv'
        self.initialize_log_file()

    def initialize_log_file(self):
        """Initialize CSV log file with headers."""
        with open(self.log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'symbol', 'direction', 'order_size', 'entry_price', 'exit_price', 'stop_loss', 'take_profit'])

    async def connect_to_binance(self):
        """Connect to Binance Futures Testnet and set leverage."""
        print("Connecting to Binance Futures Testnet...")
        self.exchange = ccxt.binanceusdm({
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
        })
        self.exchange.set_sandbox_mode(True)
        await self.exchange.load_markets()
        # Remove '/' from symbol for leverage setting if required by API
        await self.exchange.set_leverage(self.leverage, self.symbol.replace('/', ''))
        print(f"Connected and set leverage to {self.leverage}x for {self.symbol}.")

    async def fetch_account_balance(self):
        """Fetch available USDT balance."""
        if self.exchange is None:
            raise Exception("Exchange not connected.")
        balance = await self.exchange.fetch_balance()
        available_balance = balance.get('total', {}).get('USDT', 0)
        print(f"Fetched account balance: {available_balance} USDT")
        return available_balance

    async def get_ohlcv(self):
        """Fetch historical OHLCV data and return as DataFrame."""
        print("Fetching OHLCV data...")
        ohlcv = await self.exchange.fetch_ohlcv(self.symbol, self.timeframe)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def calculate_indicators(self, df):
        """Calculate EMA, MACD, and RSI indicators."""
        print("Calculating indicators...")
        df['ema_9'] = df['close'].ewm(span=9).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        df['macd'] = df['ema_9'] - df['ema_21']
        df['rsi'] = self.rsi(df['close'])
        return df

    @staticmethod
    def rsi(prices, period=14):
        """Calculate Relative Strength Index (RSI)."""
        delta = prices.diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=period, min_periods=1).mean()
        avg_loss = pd.Series(loss).rolling(window=period, min_periods=1).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    async def place_trade(self):
        """Check for trade signals and place an order if conditions are met."""
        df = await self.get_ohlcv()
        df = self.calculate_indicators(df)
        signal = check_trade_signal(df)
        if not signal:
            print("No trade signal detected.")
            return

        last_close = df.iloc[-1]['close']
        usdt_balance = await self.fetch_account_balance()
        trade_balance = min(usdt_balance, self.investment_balance)
        order_size = (trade_balance * self.leverage) / last_close
        order_size = float(self.exchange.amount_to_precision(self.symbol, order_size))

        # Calculate stop loss and take profit prices based on direction
        if signal == 'buy':
            stop_loss_price = last_close * (1 - self.stop_loss_pct / 100)
            take_profit_price = last_close * (1 + self.take_profit_pct / 100)
        else:
            stop_loss_price = last_close * (1 + self.stop_loss_pct / 100)
            take_profit_price = last_close * (1 - self.take_profit_pct / 100)

        try:
            order = await self.exchange.create_limit_order(self.symbol, signal, order_size, last_close)
            print(f"Order placed: {order}")
            self.open_orders.append({
                'id': order.get('id'),
                'symbol': self.symbol,
                'direction': signal,
                'order_size': order_size,
                'entry_price': last_close,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price
            })
        except Exception as e:
            print(f"Error placing order: {e}")

    async def monitor_trades(self):
        """Monitor open trades and close them if stop loss or take profit is hit."""
        print("Monitoring trades...")
        for order in list(self.open_orders):
            try:
                ticker = await self.exchange.fetch_ticker(order['symbol'])
                current_price = ticker['last']
                if order['direction'] == 'buy' and (current_price <= order['stop_loss_price'] or current_price >= order['take_profit_price']):
                    await self.close_trade(order, current_price)
                elif order['direction'] == 'sell' and (current_price >= order['stop_loss_price'] or current_price <= order['take_profit_price']):
                    await self.close_trade(order, current_price)
            except Exception as e:
                print(f"Error monitoring order {order.get('id')}: {e}")

    async def close_trade(self, order, current_price):
        """Close an open trade with a market order and log the trade."""
        # For simplicity, we use a market order to close the position.
        opposite_side = 'sell' if order['direction'] == 'buy' else 'buy'
        try:
            close_order = await self.exchange.create_market_order(self.symbol, opposite_side, order['order_size'])
            print(f"Closed order {order.get('id')} at price {current_price}: {close_order}")
            self.log_trade(order, current_price)
            self.open_orders.remove(order)
        except Exception as e:
            print(f"Error closing order {order.get('id')}: {e}")

    def log_trade(self, order, exit_price):
        """Log trade details to CSV file."""
        with open(self.log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                order['symbol'],
                order['direction'],
                order['order_size'],
                order['entry_price'],
                exit_price,
                order['stop_loss_price'],
                order['take_profit_price']
            ])
        print(f"Logged trade at exit price {exit_price}.")

    async def backtest(self, df):
        """Backtest the strategy using historical data from the DataFrame."""
        print("Starting backtest...")
        df = self.calculate_indicators(df)
        signals = []
        for i in range(1, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1]
            # Simple signal based on EMA crossover and RSI thresholds
            if previous['ema_9'] <= previous['ema_21'] and current['ema_9'] > current['ema_21'] and current['rsi'] < 30:
                signals.append((current['timestamp'], 'buy', current['close']))
            elif previous['ema_9'] >= previous['ema_21'] and current['ema_9'] < current['ema_21'] and current['rsi'] > 70:
                signals.append((current['timestamp'], 'sell', current['close']))
        print("Backtest signals:")
        for signal in signals:
            print(signal)
        return signals

    async def start_trading(self):
        """Main trading loop."""
        await self.fetch_account_balance()
        while True:
            try:
                await self.place_trade()
                await self.monitor_trades()
            except Exception as e:
                print(f"An error occurred in the main loop: {e}")
            # Use asynchronous sleep to avoid blocking the event loop
            await asyncio.sleep(5)


# Example usage:
API_KEY = "2b61bb8697a5967f5d088d7fd30fc38b59d6ef14cc138e93a96d239c8b694bcd"
API_SECRET = "7380053c52328a4250b2c5c7f7e83d7d7f2181e3276829c80ff73e49bf048151"

async def main():
    bot = OptimizedTradingBot(
        api_key=API_KEY,
        secret=API_SECRET,
        leverage=20,
        investment_balance=10,  # USDT
        stop_loss_pct=2,
        take_profit_pct=5,
        symbol='BTC/USDT',
        timeframe='1m'
    )
    await bot.connect_to_binance()
    # Optionally run backtest on historical data:
    # df = await bot.get_ohlcv()
    # await bot.backtest(df)
    await bot.start_trading()

if __name__ == '__main__':
    asyncio.run(main())
