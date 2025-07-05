import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from technical_analysis import TechnicalAnalysis
from backtesting import BacktestEngine
from portfolio import Portfolio
from trading_signals import TradingSignals
from database import db_manager
from market_config import MarketConfig
import os

# Page configuration
st.set_page_config(
    page_title="Automated Stock Trading System",
    page_icon="📈",
    layout="wide"
)

# Initialize database and session state
@st.cache_resource
def init_database():
    """Initialize database tables"""
    try:
        db_manager.create_tables()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

# Initialize database
db_initialized = init_database()

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()
    
if 'portfolio_id' not in st.session_state and db_initialized:
    try:
        # Create or get default portfolio
        portfolio_id = db_manager.create_portfolio("Default Portfolio", 100000)
        st.session_state.portfolio_id = portfolio_id
    except Exception as e:
        st.warning(f"Could not create database portfolio: {e}")
        st.session_state.portfolio_id = None

def main():
    st.title("📈 Automated Stock Trading System")
    st.markdown("---")
    
    # Sidebar for navigation and controls
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard", "Technical Analysis", "Backtesting", "Live Trading", "Portfolio", "Database"]
    )
    
    # Market and stock symbol input
    st.sidebar.subheader("Stock Selection")
    
    # Market selection
    market_code = st.sidebar.selectbox(
        "選擇股市 (Select Market)",
        MarketConfig.get_market_list(),
        format_func=lambda x: MarketConfig.get_market_info(x)["name"]
    )
    
    # Store market in session state
    if 'selected_market' not in st.session_state:
        st.session_state.selected_market = market_code
    
    # Update session state when market changes
    if st.session_state.selected_market != market_code:
        st.session_state.selected_market = market_code
        st.rerun()
    
    market_info = MarketConfig.get_market_info(market_code)
    
    # Symbol input with popular stocks
    col1, col2 = st.sidebar.columns([3, 1])
    
    with col1:
        symbol_input = st.text_input(
            "股票代碼 (Stock Symbol)", 
            value="2330" if market_code == "TW" else "AAPL"
        ).upper()
    
    with col2:
        show_popular = st.button("📋", help="顯示熱門股票")
    
    if show_popular:
        st.sidebar.write("**熱門股票 (Popular Stocks):**")
        for code, name in market_info["popular_stocks"]:
            if st.sidebar.button(f"{code} - {name}", key=f"stock_{code}"):
                symbol_input = code
                st.rerun()
    
    # Validate and format symbol
    symbol = MarketConfig.format_symbol(symbol_input, market_code)
    is_valid, validation_msg = MarketConfig.validate_symbol(symbol_input, market_code)
    
    if not is_valid:
        st.sidebar.warning(validation_msg)
    else:
        st.sidebar.success(f"交易代碼: {symbol} ({market_info['currency']})")
        st.sidebar.info(f"交易時間: {market_info['trading_hours']}")
    
    # Date range selection
    st.sidebar.subheader("Date Range")
    end_date = datetime.now()
    start_date = st.sidebar.date_input(
        "Start Date",
        value=end_date - timedelta(days=365)
    )
    end_date = st.sidebar.date_input("End Date", value=end_date)
    
    # Fetch stock data
    try:
        with st.spinner(f"Fetching data for {symbol}..."):
            # Try to get from database first
            if db_initialized:
                stock_data = db_manager.get_stock_data(symbol, start_date, end_date)
            else:
                stock_data = None
            
            # If not in database or data is incomplete, fetch from Yahoo Finance
            if stock_data is None or len(stock_data) == 0:
                stock_data = yf.download(symbol, start=start_date, end=end_date)
                
                # Store in database for future use
                if db_initialized and stock_data is not None and len(stock_data) > 0:
                    try:
                        db_manager.store_stock_data(symbol, stock_data)
                        st.success(f"Stock data cached in database")
                    except Exception as db_e:
                        st.warning(f"Could not cache data: {db_e}")
            else:
                st.info(f"Using cached data from database")
            
        if stock_data is None or len(stock_data) == 0:
            st.error(f"No data found for symbol {symbol}")
            return
            
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return
    
    # Initialize components
    ta = TechnicalAnalysis(stock_data)
    backtest_engine = BacktestEngine()
    signals = TradingSignals()
    
    # Route to selected page
    if page == "Dashboard":
        show_dashboard(symbol, stock_data, ta)
    elif page == "Technical Analysis":
        show_technical_analysis(symbol, stock_data, ta)
    elif page == "Backtesting":
        show_backtesting(symbol, stock_data, backtest_engine, signals)
    elif page == "Live Trading":
        show_live_trading(symbol, stock_data, signals)
    elif page == "Portfolio":
        show_portfolio()
    elif page == "Database":
        show_database()

def show_dashboard(symbol, data, ta):
    # Get market info for display
    market_code = st.session_state.get('selected_market', 'US')
    market_info = MarketConfig.get_market_info(market_code)
    
    st.header(f"📊 Dashboard - {symbol}")
    st.caption(f"{market_info['name']} | {market_info['currency']} | {market_info['trading_hours']}")
    
    # Current price and basic info
    current_price = float(data['Close'].iloc[-1])
    prev_price = float(data['Close'].iloc[-2])
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    
    # Get currency symbol
    currency = market_info['currency']
    currency_symbol = "$" if currency == "USD" else "NT$" if currency == "TWD" else currency
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "當前價格 (Current Price)", 
            f"{currency_symbol}{current_price:.2f}", 
            f"{price_change:.2f} ({price_change_pct:.2f}%)"
        )
    
    with col2:
        st.metric("年度最高 (52W High)", f"{currency_symbol}{float(data['High'].max()):.2f}")
    
    with col3:
        st.metric("年度最低 (52W Low)", f"{currency_symbol}{float(data['Low'].min()):.2f}")
    
    with col4:
        volume_avg = float(data['Volume'].mean())
        st.metric("平均成交量 (Avg Volume)", f"{volume_avg:,.0f}")
    
    # Price chart with volume
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(f"{symbol} Price Chart", "Volume"),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Add volume chart
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(158,202,225,0.8)'
        ),
        row=2, col=1
    )
    
    # Add moving averages to price chart
    ma20 = ta.moving_average(20)
    ma50 = ta.moving_average(50)
    
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ma20,
            name="MA20",
            line=dict(color='orange', width=1)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ma50,
            name="MA50",
            line=dict(color='red', width=1)
        ),
        row=1, col=1
    )
    
    fig.update_layout(
        title=f"{symbol} Historical Data",
        yaxis_title="Price ($)",
        yaxis2_title="Volume",
        xaxis_title="Date",
        height=600,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Historical data summary table
    st.subheader("Recent Price Data")
    recent_data = data.tail(10).copy()
    recent_data = recent_data.round(2)
    recent_data.index = recent_data.index.strftime('%Y-%m-%d')
    st.dataframe(recent_data, use_container_width=True)
    
    # Price statistics
    st.subheader("Historical Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Price Range**")
        price_range = float(data['High'].max() - data['Low'].min())
        st.write(f"Range: ${price_range:.2f}")
        st.write(f"High: ${float(data['High'].max()):.2f}")
        st.write(f"Low: ${float(data['Low'].min()):.2f}")
    
    with col2:
        st.write("**Volatility**")
        returns = data['Close'].pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252) * 100)
        st.write(f"Annual Volatility: {volatility:.2f}%")
        
        daily_vol = float(returns.std() * 100)
        st.write(f"Daily Volatility: {daily_vol:.2f}%")
    
    with col3:
        st.write("**Volume Analysis**")
        avg_volume = float(data['Volume'].mean())
        recent_volume = float(data['Volume'].tail(5).mean())
        volume_trend = "📈" if recent_volume > avg_volume else "📉"
        
        st.write(f"Avg Volume: {avg_volume:,.0f}")
        st.write(f"Recent Avg: {recent_volume:,.0f} {volume_trend}")
    
    # Performance over different periods
    st.subheader("Performance Summary")
    
    periods = {
        "1 Week": 7,
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 252
    }
    
    performance_data = []
    for period_name, days in periods.items():
        if len(data) > days:
            start_price = float(data['Close'].iloc[-days])
            end_price = float(data['Close'].iloc[-1])
            return_pct = ((end_price - start_price) / start_price) * 100
            
            performance_data.append({
                "Period": period_name,
                "Start Price": f"${start_price:.2f}",
                "End Price": f"${end_price:.2f}",
                "Return": f"{return_pct:.2f}%"
            })
    
    if performance_data:
        perf_df = pd.DataFrame(performance_data)
        st.dataframe(perf_df, use_container_width=True)
    
    # Quick technical indicators
    st.subheader("Quick Technical Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Moving averages
        ma20 = ta.moving_average(20)
        ma50 = ta.moving_average(50)
        
        current_ma20 = float(ma20.iloc[-1])
        current_ma50 = float(ma50.iloc[-1])
        
        st.write("**Moving Averages**")
        st.write(f"MA20: ${current_ma20:.2f}")
        st.write(f"MA50: ${current_ma50:.2f}")
        
        if current_price > current_ma20 > current_ma50:
            st.success("Bullish Trend")
        elif current_price < current_ma20 < current_ma50:
            st.error("Bearish Trend")
        else:
            st.warning("Sideways Trend")
    
    with col2:
        # RSI
        rsi = ta.rsi()
        current_rsi = float(rsi.iloc[-1])
        
        st.write("**RSI (14)**")
        st.write(f"Current RSI: {current_rsi:.2f}")
        
        if current_rsi > 70:
            st.error("Overbought")
        elif current_rsi < 30:
            st.success("Oversold")
        else:
            st.info("Neutral")

def show_technical_analysis(symbol, data, ta):
    st.header(f"Technical Analysis - {symbol}")
    
    # Indicator selection
    indicators = st.multiselect(
        "Select Technical Indicators",
        ["Moving Averages", "RSI", "MACD", "Bollinger Bands"],
        default=["Moving Averages", "RSI"]
    )
    
    if "Moving Averages" in indicators:
        st.subheader("Moving Averages")
        
        col1, col2 = st.columns(2)
        with col1:
            ma_short = st.number_input("Short MA Period", value=20, min_value=1)
        with col2:
            ma_long = st.number_input("Long MA Period", value=50, min_value=1)
        
        ma_short_data = ta.moving_average(ma_short)
        ma_long_data = ta.moving_average(ma_long)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"))
        fig.add_trace(go.Scatter(x=data.index, y=ma_short_data, name=f"MA{ma_short}"))
        fig.add_trace(go.Scatter(x=data.index, y=ma_long_data, name=f"MA{ma_long}"))
        
        fig.update_layout(title="Moving Averages", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    if "RSI" in indicators:
        st.subheader("RSI (Relative Strength Index)")
        
        rsi_period = st.number_input("RSI Period", value=14, min_value=1)
        rsi_data = ta.rsi(rsi_period)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=rsi_data, name="RSI"))
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        
        fig.update_layout(title="RSI", yaxis_title="RSI", height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    if "MACD" in indicators:
        st.subheader("MACD")
        
        macd_line, macd_signal, macd_histogram = ta.macd()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=macd_line, name="MACD"))
        fig.add_trace(go.Scatter(x=data.index, y=macd_signal, name="Signal"))
        fig.add_trace(go.Bar(x=data.index, y=macd_histogram, name="Histogram"))
        
        fig.update_layout(title="MACD", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    if "Bollinger Bands" in indicators:
        st.subheader("Bollinger Bands")
        
        bb_period = st.number_input("BB Period", value=20, min_value=1)
        bb_std = st.number_input("Standard Deviations", value=2.0, min_value=0.1)
        
        bb_upper, bb_middle, bb_lower = ta.bollinger_bands(bb_period, bb_std)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"))
        fig.add_trace(go.Scatter(x=data.index, y=bb_upper, name="Upper Band"))
        fig.add_trace(go.Scatter(x=data.index, y=bb_middle, name="Middle Band"))
        fig.add_trace(go.Scatter(x=data.index, y=bb_lower, name="Lower Band"))
        
        fig.update_layout(title="Bollinger Bands", height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_backtesting(symbol, data, backtest_engine, signals):
    st.header(f"Backtesting - {symbol}")
    
    # Strategy selection
    strategy = st.selectbox(
        "Select Trading Strategy",
        ["Moving Average Crossover", "RSI Mean Reversion", "MACD Strategy"]
    )
    
    # Strategy parameters
    st.subheader("Strategy Parameters")
    
    if strategy == "Moving Average Crossover":
        col1, col2, col3 = st.columns(3)
        with col1:
            short_ma = st.number_input("Short MA", value=20, min_value=1)
        with col2:
            long_ma = st.number_input("Long MA", value=50, min_value=1)
        with col3:
            initial_capital = st.number_input("Initial Capital", value=10000, min_value=1000)
        
        strategy_params = {
            'short_ma': short_ma,
            'long_ma': long_ma,
            'initial_capital': initial_capital
        }
    
    elif strategy == "RSI Mean Reversion":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rsi_period = st.number_input("RSI Period", value=14, min_value=1)
        with col2:
            oversold = st.number_input("Oversold Level", value=30, min_value=1, max_value=50)
        with col3:
            overbought = st.number_input("Overbought Level", value=70, min_value=50, max_value=100)
        with col4:
            initial_capital = st.number_input("Initial Capital", value=10000, min_value=1000)
        
        strategy_params = {
            'rsi_period': rsi_period,
            'oversold': oversold,
            'overbought': overbought,
            'initial_capital': initial_capital
        }
    
    else:  # MACD Strategy
        col1, col2 = st.columns(2)
        with col1:
            initial_capital = st.number_input("Initial Capital", value=10000, min_value=1000)
        with col2:
            st.write("")  # Placeholder
        
        strategy_params = {
            'initial_capital': initial_capital
        }
    
    # Run backtest button
    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            results = backtest_engine.run_backtest(data, strategy, strategy_params)
            
            # Store backtest results in database
            if db_initialized and results:
                try:
                    backtest_id = db_manager.store_backtest_result(
                        strategy, symbol, data.index[0].date(), data.index[-1].date(), results
                    )
                    st.success(f"Backtest results saved to database (ID: {backtest_id})")
                except Exception as db_e:
                    st.warning(f"Could not save backtest results: {db_e}")
        
        # Display results
        st.subheader("Backtest Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{results['total_return']:.2f}%")
        with col2:
            st.metric("Annual Return", f"{results['annual_return']:.2f}%")
        with col3:
            st.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
        with col4:
            st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
        
        # Portfolio value chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=results['portfolio_values'].index,
            y=results['portfolio_values'],
            name="Portfolio Value"
        ))
        
        fig.update_layout(
            title="Portfolio Value Over Time",
            yaxis_title="Portfolio Value ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Trades table
        if len(results['trades']) > 0:
            st.subheader("Trade History")
            trades_df = pd.DataFrame(results['trades'])
            st.dataframe(trades_df, use_container_width=True)

def show_live_trading(symbol, data, signals):
    st.header(f"Live Trading - {symbol}")
    
    st.warning("⚠️ This is a mock trading system. No real money transactions are executed.")
    
    # Current signals
    st.subheader("Current Trading Signals")
    
    # Calculate current signals
    ma_signal = signals.moving_average_signal(data)
    rsi_signal = signals.rsi_signal(data)
    macd_signal = signals.macd_signal(data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Moving Average Signal**")
        if ma_signal == 1:
            st.success("BUY")
        elif ma_signal == -1:
            st.error("SELL")
        else:
            st.info("HOLD")
    
    with col2:
        st.write("**RSI Signal**")
        if rsi_signal == 1:
            st.success("BUY")
        elif rsi_signal == -1:
            st.error("SELL")
        else:
            st.info("HOLD")
    
    with col3:
        st.write("**MACD Signal**")
        if macd_signal == 1:
            st.success("BUY")
        elif macd_signal == -1:
            st.error("SELL")
        else:
            st.info("HOLD")
    
    # Manual trading interface
    st.subheader("Manual Trading")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action = st.selectbox("Action", ["BUY", "SELL"])
    with col2:
        quantity = st.number_input("Quantity", value=100, min_value=1)
    with col3:
        order_type = st.selectbox("Order Type", ["Market", "Limit"])
    
    if order_type == "Limit":
        limit_price = st.number_input("Limit Price", value=float(data['Close'].iloc[-1]))
    else:
        limit_price = None
    
    if st.button("Execute Order"):
        current_price = float(data['Close'].iloc[-1])
        
        order = {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': limit_price if limit_price else current_price,
            'timestamp': datetime.now(),
            'order_type': order_type
        }
        
        # Add to portfolio
        success = st.session_state.portfolio.execute_order(order)
        
        if success:
            st.success(f"Order executed: {action} {quantity} shares of {symbol}")
            st.rerun()
        else:
            st.error("Insufficient funds or invalid order")

def show_portfolio():
    st.header("Portfolio Management")
    
    portfolio = st.session_state.portfolio
    
    # Portfolio summary
    st.subheader("Portfolio Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"${float(portfolio.total_value):.2f}")
    with col2:
        st.metric("Cash", f"${float(portfolio.cash):.2f}")
    with col3:
        st.metric("Total Return", f"{float(portfolio.total_return):.2f}%")
    with col4:
        st.metric("Day Change", f"{float(portfolio.day_change):.2f}%")
    
    # Holdings
    if portfolio.holdings:
        st.subheader("Current Holdings")
        holdings_data = []
        
        for symbol, data in portfolio.holdings.items():
            # Get current price (mock for demonstration)
            current_price = data['average_price'] * (1 + np.random.uniform(-0.05, 0.05))
            market_value = current_price * data['quantity']
            unrealized_pnl = market_value - (data['average_price'] * data['quantity'])
            
            holdings_data.append({
                'Symbol': symbol,
                'Quantity': data['quantity'],
                'Avg Price': f"${data['average_price']:.2f}",
                'Current Price': f"${current_price:.2f}",
                'Market Value': f"${market_value:.2f}",
                'Unrealized P&L': f"${unrealized_pnl:.2f}"
            })
        
        holdings_df = pd.DataFrame(holdings_data)
        st.dataframe(holdings_df, use_container_width=True)
    else:
        st.info("No current holdings")
    
    # Trade history
    if portfolio.trade_history:
        st.subheader("Trade History")
        trades_df = pd.DataFrame(portfolio.trade_history)
        st.dataframe(trades_df, use_container_width=True)
    else:
        st.info("No trade history")

def show_database():
    st.header("Database Management")
    
    if not db_initialized:
        st.error("Database is not initialized. Please check your database connection.")
        return
    
    # Database status
    st.subheader("Database Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ Database Connected")
        st.write(f"Host: {os.getenv('PGHOST', 'N/A')}")
        st.write(f"Database: {os.getenv('PGDATABASE', 'N/A')}")
    
    with col2:
        if st.button("Reset Database"):
            if st.button("Confirm Reset", key="confirm_reset"):
                try:
                    db_manager.create_tables()
                    st.success("Database reset successfully")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resetting database: {e}")
    
    # Stock data management
    st.subheader("Stock Data Cache")
    
    # Show available symbols in database
    try:
        stock_records = db_manager.list_cached_symbols()
        if stock_records:
            st.write("**Cached Stock Data:**")
            cache_data = [
                {
                    "Symbol": rec['symbol'],
                    "Records": rec['records'],
                    "Start Date": rec['start_date'],
                    "End Date": rec['end_date'],
                }
                for rec in stock_records
            ]
            cache_df = pd.DataFrame(cache_data)
            st.dataframe(cache_df, use_container_width=True)
        else:
            st.info("No stock data cached yet")
            
    except Exception as e:
        st.error(f"Error retrieving stock data cache: {e}")
    
    # Portfolio management
    st.subheader("Portfolio Data")
    
    try:
        portfolio_records = db_manager.list_portfolios()
        if portfolio_records:
            st.write("**Portfolios in Database:**")
            portfolio_data = [
                {
                    "ID": p.id,
                    "Name": p.name,
                    "Initial Cash": f"${p.initial_cash:,.2f}",
                    "Current Cash": f"${p.current_cash:,.2f}",
                    "Created": p.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for p in portfolio_records
            ]
            portfolio_df = pd.DataFrame(portfolio_data)
            st.dataframe(portfolio_df, use_container_width=True)
        else:
            st.info("No portfolios in database")
            
    except Exception as e:
        st.error(f"Error retrieving portfolio data: {e}")
    
    # Backtest results
    st.subheader("Backtest Results History")
    
    try:
        backtest_records = db_manager.list_recent_backtests()
        if backtest_records:
            st.write("**Recent Backtest Results:**")
            backtest_data = [
                {
                    "Strategy": rec['strategy'],
                    "Symbol": rec['symbol'],
                    "Total Return": f"{rec['total_return']:.2f}%",
                    "Annual Return": f"{rec['annual_return']:.2f}%",
                    "Max Drawdown": f"{rec['max_drawdown']:.2f}%",
                    "Sharpe Ratio": f"{rec['sharpe_ratio']:.2f}",
                    "Trades": rec['num_trades'],
                    "Date": rec['created_at'].strftime("%Y-%m-%d %H:%M"),
                }
                for rec in backtest_records
            ]
            backtest_df = pd.DataFrame(backtest_data)
            st.dataframe(backtest_df, use_container_width=True)
        else:
            st.info("No backtest results yet")
            
    except Exception as e:
        st.error(f"Error retrieving backtest results: {e}")

if __name__ == "__main__":
    main()
