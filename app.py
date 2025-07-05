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

# Page configuration
st.set_page_config(
    page_title="Automated Stock Trading System",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()

def main():
    st.title("📈 Automated Stock Trading System")
    st.markdown("---")
    
    # Sidebar for navigation and controls
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard", "Technical Analysis", "Backtesting", "Live Trading", "Portfolio"]
    )
    
    # Stock selection
    st.sidebar.subheader("Stock Selection")
    symbol = st.sidebar.text_input("Enter Stock Symbol", value="AAPL").upper()
    
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
            stock_data = yf.download(symbol, start=start_date, end=end_date)
            
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

def show_dashboard(symbol, data, ta):
    st.header(f"Dashboard - {symbol}")
    
    # Current price and basic info
    current_price = float(data['Close'].iloc[-1])
    prev_price = float(data['Close'].iloc[-2])
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)")
    
    with col2:
        st.metric("High (52W)", f"${float(data['High'].max()):.2f}")
    
    with col3:
        st.metric("Low (52W)", f"${float(data['Low'].min()):.2f}")
    
    with col4:
        volume_avg = float(data['Volume'].mean())
        st.metric("Avg Volume", f"{volume_avg:,.0f}")
    
    # Price chart with volume
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Price"
    ))
    
    fig.update_layout(
        title=f"{symbol} Price Chart",
        yaxis_title="Price ($)",
        xaxis_title="Date",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
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

if __name__ == "__main__":
    main()
