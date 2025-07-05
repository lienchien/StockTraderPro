import pandas as pd
import numpy as np
from technical_analysis import TechnicalAnalysis

class BacktestEngine:
    """Backtesting engine for trading strategies"""
    
    def __init__(self):
        self.trades = []
        self.portfolio_values = []
    
    def run_backtest(self, data, strategy, params):
        """
        Run backtest for given strategy and parameters
        
        Args:
            data: Stock price data
            strategy: Strategy name
            params: Strategy parameters
            
        Returns:
            dict: Backtest results
        """
        self.trades = []
        self.portfolio_values = []
        
        if strategy == "Moving Average Crossover":
            return self._backtest_ma_crossover(data, params)
        elif strategy == "RSI Mean Reversion":
            return self._backtest_rsi_mean_reversion(data, params)
        elif strategy == "MACD Strategy":
            return self._backtest_macd_strategy(data, params)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _backtest_ma_crossover(self, data, params):
        """
        Backtest Moving Average Crossover strategy
        
        Args:
            data: Stock price data
            params: Strategy parameters
            
        Returns:
            dict: Backtest results
        """
        ta = TechnicalAnalysis(data)
        short_ma = ta.moving_average(params['short_ma'])
        long_ma = ta.moving_average(params['long_ma'])
        
        cash = params['initial_capital']
        shares = 0
        portfolio_value = params['initial_capital']
        portfolio_values = [portfolio_value]
        trades = []
        
        position = 0  # 0: no position, 1: long position
        
        for i in range(1, len(data)):
            current_price = data['Close'].iloc[i]
            prev_short_ma = short_ma.iloc[i-1]
            curr_short_ma = short_ma.iloc[i]
            prev_long_ma = long_ma.iloc[i-1]
            curr_long_ma = long_ma.iloc[i]
            
            # Skip if MA values are NaN
            if pd.isna(curr_short_ma) or pd.isna(curr_long_ma):
                portfolio_value = cash + shares * current_price
                portfolio_values.append(portfolio_value)
                continue
            
            # Buy signal: short MA crosses above long MA
            if (prev_short_ma <= prev_long_ma and curr_short_ma > curr_long_ma and position == 0):
                shares_to_buy = int(cash / current_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price
                    cash -= cost
                    shares += shares_to_buy
                    position = 1
                    
                    trades.append({
                        'date': data.index[i],
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': current_price,
                        'value': cost
                    })
            
            # Sell signal: short MA crosses below long MA
            elif (prev_short_ma >= prev_long_ma and curr_short_ma < curr_long_ma and position == 1):
                if shares > 0:
                    proceeds = shares * current_price
                    cash += proceeds
                    
                    trades.append({
                        'date': data.index[i],
                        'action': 'SELL',
                        'shares': shares,
                        'price': current_price,
                        'value': proceeds
                    })
                    
                    shares = 0
                    position = 0
            
            portfolio_value = cash + shares * current_price
            portfolio_values.append(portfolio_value)
        
        # Close any remaining position
        if shares > 0:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price
            cash += proceeds
            
            trades.append({
                'date': data.index[-1],
                'action': 'SELL',
                'shares': shares,
                'price': final_price,
                'value': proceeds
            })
        
        final_portfolio_value = cash
        portfolio_values_series = pd.Series(portfolio_values, index=data.index)
        
        return self._calculate_metrics(
            params['initial_capital'],
            final_portfolio_value,
            portfolio_values_series,
            trades
        )
    
    def _backtest_rsi_mean_reversion(self, data, params):
        """
        Backtest RSI Mean Reversion strategy
        
        Args:
            data: Stock price data
            params: Strategy parameters
            
        Returns:
            dict: Backtest results
        """
        ta = TechnicalAnalysis(data)
        rsi = ta.rsi(params['rsi_period'])
        
        cash = params['initial_capital']
        shares = 0
        portfolio_value = params['initial_capital']
        portfolio_values = [portfolio_value]
        trades = []
        
        position = 0  # 0: no position, 1: long position
        
        for i in range(1, len(data)):
            current_price = data['Close'].iloc[i]
            current_rsi = rsi.iloc[i]
            
            # Skip if RSI is NaN
            if pd.isna(current_rsi):
                portfolio_value = cash + shares * current_price
                portfolio_values.append(portfolio_value)
                continue
            
            # Buy signal: RSI below oversold level
            if current_rsi < params['oversold'] and position == 0:
                shares_to_buy = int(cash / current_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price
                    cash -= cost
                    shares += shares_to_buy
                    position = 1
                    
                    trades.append({
                        'date': data.index[i],
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': current_price,
                        'value': cost
                    })
            
            # Sell signal: RSI above overbought level
            elif current_rsi > params['overbought'] and position == 1:
                if shares > 0:
                    proceeds = shares * current_price
                    cash += proceeds
                    
                    trades.append({
                        'date': data.index[i],
                        'action': 'SELL',
                        'shares': shares,
                        'price': current_price,
                        'value': proceeds
                    })
                    
                    shares = 0
                    position = 0
            
            portfolio_value = cash + shares * current_price
            portfolio_values.append(portfolio_value)
        
        # Close any remaining position
        if shares > 0:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price
            cash += proceeds
            
            trades.append({
                'date': data.index[-1],
                'action': 'SELL',
                'shares': shares,
                'price': final_price,
                'value': proceeds
            })
        
        final_portfolio_value = cash
        portfolio_values_series = pd.Series(portfolio_values, index=data.index)
        
        return self._calculate_metrics(
            params['initial_capital'],
            final_portfolio_value,
            portfolio_values_series,
            trades
        )
    
    def _backtest_macd_strategy(self, data, params):
        """
        Backtest MACD strategy
        
        Args:
            data: Stock price data
            params: Strategy parameters
            
        Returns:
            dict: Backtest results
        """
        ta = TechnicalAnalysis(data)
        macd_line, signal_line, histogram = ta.macd()
        
        cash = params['initial_capital']
        shares = 0
        portfolio_value = params['initial_capital']
        portfolio_values = [portfolio_value]
        trades = []
        
        position = 0  # 0: no position, 1: long position
        
        for i in range(1, len(data)):
            current_price = data['Close'].iloc[i]
            prev_macd = macd_line.iloc[i-1]
            curr_macd = macd_line.iloc[i]
            prev_signal = signal_line.iloc[i-1]
            curr_signal = signal_line.iloc[i]
            
            # Skip if MACD values are NaN
            if pd.isna(curr_macd) or pd.isna(curr_signal):
                portfolio_value = cash + shares * current_price
                portfolio_values.append(portfolio_value)
                continue
            
            # Buy signal: MACD crosses above signal line
            if (prev_macd <= prev_signal and curr_macd > curr_signal and position == 0):
                shares_to_buy = int(cash / current_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price
                    cash -= cost
                    shares += shares_to_buy
                    position = 1
                    
                    trades.append({
                        'date': data.index[i],
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': current_price,
                        'value': cost
                    })
            
            # Sell signal: MACD crosses below signal line
            elif (prev_macd >= prev_signal and curr_macd < curr_signal and position == 1):
                if shares > 0:
                    proceeds = shares * current_price
                    cash += proceeds
                    
                    trades.append({
                        'date': data.index[i],
                        'action': 'SELL',
                        'shares': shares,
                        'price': current_price,
                        'value': proceeds
                    })
                    
                    shares = 0
                    position = 0
            
            portfolio_value = cash + shares * current_price
            portfolio_values.append(portfolio_value)
        
        # Close any remaining position
        if shares > 0:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price
            cash += proceeds
            
            trades.append({
                'date': data.index[-1],
                'action': 'SELL',
                'shares': shares,
                'price': final_price,
                'value': proceeds
            })
        
        final_portfolio_value = cash
        portfolio_values_series = pd.Series(portfolio_values, index=data.index)
        
        return self._calculate_metrics(
            params['initial_capital'],
            final_portfolio_value,
            portfolio_values_series,
            trades
        )
    
    def _calculate_metrics(self, initial_capital, final_value, portfolio_values, trades):
        """
        Calculate performance metrics
        
        Args:
            initial_capital: Starting capital
            final_value: Final portfolio value
            portfolio_values: Series of portfolio values over time
            trades: List of executed trades
            
        Returns:
            dict: Performance metrics
        """
        # Total return
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Annual return (assuming daily data)
        days = len(portfolio_values)
        years = days / 252  # Assuming 252 trading days per year
        annual_return = ((final_value / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Maximum drawdown
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (simplified - assuming risk-free rate of 2%)
        returns = portfolio_values.pct_change().dropna()
        excess_returns = returns - (0.02 / 252)  # Daily risk-free rate
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() != 0 else 0
        
        # Volatility
        volatility = returns.std() * np.sqrt(252) * 100
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            'final_value': final_value,
            'portfolio_values': portfolio_values,
            'trades': trades,
            'num_trades': len(trades)
        }
