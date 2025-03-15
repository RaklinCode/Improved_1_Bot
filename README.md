Optimized Trading Bot
This is a Python-based cryptocurrency trading bot built to interact with the Binance Futures Testnet using the ccxt library. The bot utilizes multiple technical indicators (EMA, RSI, MACD) to determine buy and sell signals, place trades, and manage open positions based on defined strategies. It is designed for automated trading with features like risk management (stop loss and take profit) and logging trade details for performance tracking.

Features
Asynchronous Trading: Leverages Python's asyncio to handle multiple operations concurrently, ensuring efficiency when fetching data and placing orders.
Trade Signal Generation: Determines buy and sell signals based on the Exponential Moving Average (EMA) crossover and Relative Strength Index (RSI).
Risk Management: Implements stop loss and take profit levels to manage risks and secure profits.
Backtesting: Backtest the strategy with historical data to evaluate performance before deploying in live environments.
Trade Logging: Logs trade details (timestamp, symbol, direction, order size, entry/exit price) to a CSV file for record-keeping.
Binance Integration: Uses the Binance Futures API (Testnet) for placing and monitoring orders.
Installation
Clone the repository:

bash
Copy
Edit
git clone https://github.com/yourusername/optimized-trading-bot.git
cd optimized-trading-bot
Install required dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Required libraries:

ccxt
pandas
numpy
asyncio
csv
Configuration
Before running the bot, make sure to set up your API keys and other parameters in the script:

python
Copy
Edit
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

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
API_KEY and API_SECRET: Your Binance API credentials (Testnet recommended for testing).
leverage: The leverage you want to use for margin trading.
investment_balance: The amount of USDT to invest per trade.
stop_loss_pct: The percentage of loss before stopping the trade.
take_profit_pct: The percentage of profit before taking the profit.
symbol: The trading pair (e.g., 'BTC/USDT').
timeframe: The timeframe for historical OHLCV data (e.g., '1m' for 1-minute candles).
How to Use
Run the bot:

To start trading, execute the script:

bash
Copy
Edit
python bot.py
Backtest (Optional):

You can backtest the strategy with historical data by uncommenting the following lines in the script:

python
Copy
Edit
# df = await bot.get_ohlcv()
# await bot.backtest(df)
Monitoring Trades:

The bot will continuously monitor open trades and close them when either the stop loss or take profit is hit.

Log Files:

The bot logs all trade actions (including the timestamp, order size, entry and exit price, stop loss, and take profit) into a CSV file named trade_log.csv.

Methods
connect_to_binance(): Connects to the Binance Futures Testnet and sets leverage.
fetch_account_balance(): Fetches the available balance in USDT.
get_ohlcv(): Fetches historical OHLCV data for the specified symbol and timeframe.
calculate_indicators(): Calculates EMA, MACD, and RSI indicators.
place_trade(): Checks for trade signals and places an order if conditions are met.
monitor_trades(): Monitors open trades and closes them when stop loss or take profit is triggered.
close_trade(): Closes an open trade and logs the trade details.
log_trade(): Logs trade details to the CSV file.
backtest(): Backtests the strategy using historical data.
start_trading(): Main trading loop that continuously fetches data and places/monitors trades.
Example Usage
To run the bot, make sure to replace API_KEY and API_SECRET with your own Binance Testnet credentials. The bot will automatically start trading based on the strategy.

python
Copy
Edit
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

async def main():
    bot = OptimizedTradingBot(
        api_key=API_KEY,
        secret=API_SECRET,
        leverage=20,
        investment_balance=10,
        stop_loss_pct=2,
        take_profit_pct=5,
        symbol='BTC/USDT',
        timeframe='1m'
    )
    await bot.connect_to_binance()
    await bot.start_trading()

if __name__ == '__main__':
    asyncio.run(main())
Logging
Trade actions (buy/sell) are logged in the trade_log.csv file. Each entry includes the following:

timestamp: Time of trade
symbol: Trading pair (e.g., BTC/USDT)
direction: Buy or Sell
order_size: The size of the trade
entry_price: The price at which the trade was entered
exit_price: The price at which the trade was exited
stop_loss: The stop loss price
take_profit: The take profit price
Contribution
Feel free to fork this repository and contribute by submitting pull requests. If you find any bugs or issues, please open an issue so we can improve the bot.

License
This project is licensed under the MIT License.
