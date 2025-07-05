import pandas as pd
import numpy as np
from technical_analysis import TechnicalAnalysis

class TradingSignals:
    """Generate trading signals based on technical analysis"""
    
    def __init__(self):
        pass
    
    def moving_average_signal(self, data, short_period=20, long_period=50):
        """
        Generate signal based on moving average crossover
        
        Args:
            data: Stock price data
            short_period: Short MA period
            long_period: Long MA period
            
        Returns:
            int: 1 for buy, -1 for sell, 0 for hold
        """
        ta = TechnicalAnalysis(data)
        short_ma = ta.moving_average(short_period)
        long_ma = ta.moving_average(long_period)
        
        if len(short_ma) < 2 or len(long_ma) < 2:
            return 0
        
        # Current and previous values
        curr_short = short_ma.iloc[-1]
        prev_short = short_ma.iloc[-2]
        curr_long = long_ma.iloc[-1]
        prev_long = long_ma.iloc[-2]
        
        # Check for crossover
        if prev_short <= prev_long and curr_short > curr_long:
            return 1  # Buy signal
        elif prev_short >= prev_long and curr_short < curr_long:
            return -1  # Sell signal
        else:
            return 0  # Hold
    
    def rsi_signal(self, data, period=14, oversold=30, overbought=70):
        """
        Generate signal based on RSI levels
        
        Args:
            data: Stock price data
            period: RSI period
            oversold: Oversold threshold
            overbought: Overbought threshold
            
        Returns:
            int: 1 for buy, -1 for sell, 0 for hold
        """
        ta = TechnicalAnalysis(data)
        rsi = ta.rsi(period)
        
        if len(rsi) < 2:
            return 0
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        
        # Buy signal: RSI crosses above oversold level
        if prev_rsi <= oversold and current_rsi > oversold:
            return 1
        # Sell signal: RSI crosses below overbought level
        elif prev_rsi >= overbought and current_rsi < overbought:
            return -1
        else:
            return 0
    
    def macd_signal(self, data):
        """
        Generate signal based on MACD crossover
        
        Args:
            data: Stock price data
            
        Returns:
            int: 1 for buy, -1 for sell, 0 for hold
        """
        ta = TechnicalAnalysis(data)
        macd_line, signal_line, histogram = ta.macd()
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return 0
        
        # Current and previous values
        curr_macd = macd_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        curr_signal = signal_line.iloc[-1]
        prev_signal = signal_line.iloc[-2]
        
        # Check for crossover
        if prev_macd <= prev_signal and curr_macd > curr_signal:
            return 1  # Buy signal
        elif prev_macd >= prev_signal and curr_macd < curr_signal:
            return -1  # Sell signal
        else:
            return 0  # Hold
    
    def bollinger_bands_signal(self, data, period=20, std_dev=2):
        """
        Generate signal based on Bollinger Bands
        
        Args:
            data: Stock price data
            period: BB period
            std_dev: Standard deviations
            
        Returns:
            int: 1 for buy, -1 for sell, 0 for hold
        """
        ta = TechnicalAnalysis(data)
        upper_band, middle_band, lower_band = ta.bollinger_bands(period, std_dev)
        
        if len(data) < 2:
            return 0
        
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        current_lower = lower_band.iloc[-1]
        current_upper = upper_band.iloc[-1]
        prev_lower = lower_band.iloc[-2]
        prev_upper = upper_band.iloc[-2]
        
        # Buy signal: price crosses above lower band (oversold bounce)
        if prev_price <= prev_lower and current_price > current_lower:
            return 1
        # Sell signal: price crosses below upper band (overbought reversal)
        elif prev_price >= prev_upper and current_price < current_upper:
            return -1
        else:
            return 0
    
    def stochastic_signal(self, data, k_period=14, d_period=3, oversold=20, overbought=80):
        """
        Generate signal based on Stochastic Oscillator
        
        Args:
            data: Stock price data
            k_period: %K period
            d_period: %D period
            oversold: Oversold threshold
            overbought: Overbought threshold
            
        Returns:
            int: 1 for buy, -1 for sell, 0 for hold
        """
        ta = TechnicalAnalysis(data)
        k_percent, d_percent = ta.stochastic_oscillator(k_period, d_period)
        
        if len(k_percent) < 2 or len(d_percent) < 2:
            return 0
        
        current_k = k_percent.iloc[-1]
        prev_k = k_percent.iloc[-2]
        current_d = d_percent.iloc[-1]
        prev_d = d_percent.iloc[-2]
        
        # Buy signal: %K crosses above %D in oversold region
        if (prev_k <= prev_d and current_k > current_d and 
            current_k < oversold and current_d < oversold):
            return 1
        # Sell signal: %K crosses below %D in overbought region
        elif (prev_k >= prev_d and current_k < current_d and 
              current_k > overbought and current_d > overbought):
            return -1
        else:
            return 0
    
    def composite_signal(self, data, weights=None):
        """
        Generate composite signal based on multiple indicators
        
        Args:
            data: Stock price data
            weights: Dictionary of weights for each signal
            
        Returns:
            dict: Composite signal with individual signals and weighted score
        """
        if weights is None:
            weights = {
                'ma': 0.25,
                'rsi': 0.25,
                'macd': 0.25,
                'bb': 0.25
            }
        
        # Get individual signals
        signals = {
            'ma': self.moving_average_signal(data),
            'rsi': self.rsi_signal(data),
            'macd': self.macd_signal(data),
            'bb': self.bollinger_bands_signal(data)
        }
        
        # Calculate weighted score
        weighted_score = sum(signals[key] * weights[key] for key in signals.keys())
        
        # Determine composite signal
        if weighted_score > 0.5:
            composite_signal = 1  # Strong buy
        elif weighted_score > 0.2:
            composite_signal = 0.5  # Weak buy
        elif weighted_score < -0.5:
            composite_signal = -1  # Strong sell
        elif weighted_score < -0.2:
            composite_signal = -0.5  # Weak sell
        else:
            composite_signal = 0  # Hold
        
        return {
            'individual_signals': signals,
            'weighted_score': weighted_score,
            'composite_signal': composite_signal,
            'signal_strength': abs(weighted_score)
        }
    
    def get_signal_explanation(self, signal_value):
        """
        Get human-readable explanation of signal
        
        Args:
            signal_value: Signal value
            
        Returns:
            str: Signal explanation
        """
        if signal_value == 1:
            return "Strong Buy Signal"
        elif signal_value == 0.5:
            return "Weak Buy Signal"
        elif signal_value == 0:
            return "Hold/Neutral Signal"
        elif signal_value == -0.5:
            return "Weak Sell Signal"
        elif signal_value == -1:
            return "Strong Sell Signal"
        else:
            return "Unknown Signal"
    
    def backtest_signals(self, data, signal_func, **kwargs):
        """
        Backtest a specific signal function
        
        Args:
            data: Stock price data
            signal_func: Signal function to test
            **kwargs: Additional arguments for signal function
            
        Returns:
            dict: Backtest results for the signal
        """
        signals = []
        returns = []
        
        # Generate signals for each day
        for i in range(50, len(data)):  # Start after 50 days to ensure indicators are stable
            subset_data = data.iloc[:i+1]
            signal = signal_func(subset_data, **kwargs)
            signals.append(signal)
            
            # Calculate next-day return if signal is not hold
            if i < len(data) - 1 and signal != 0:
                next_return = (data['Close'].iloc[i+1] - data['Close'].iloc[i]) / data['Close'].iloc[i]
                returns.append(signal * next_return)  # Multiply by signal direction
            else:
                returns.append(0)
        
        # Calculate performance metrics
        total_return = sum(returns)
        win_rate = len([r for r in returns if r > 0]) / len(returns) if returns else 0
        avg_return = np.mean(returns) if returns else 0
        volatility = np.std(returns) if returns else 0
        
        return {
            'total_return': total_return * 100,
            'win_rate': win_rate * 100,
            'average_return': avg_return * 100,
            'volatility': volatility * 100,
            'num_signals': len([s for s in signals if s != 0]),
            'signals': signals,
            'returns': returns
        }
