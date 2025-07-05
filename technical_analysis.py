import pandas as pd
import numpy as np

class TechnicalAnalysis:
    """Technical analysis indicators for stock data"""
    
    def __init__(self, data):
        """
        Initialize with stock data
        
        Args:
            data: DataFrame with OHLCV data
        """
        self.data = data
    
    def moving_average(self, period):
        """
        Calculate Simple Moving Average
        
        Args:
            period: Number of periods for moving average
            
        Returns:
            pandas.Series: Moving average values
        """
        return self.data['Close'].rolling(window=period).mean()
    
    def exponential_moving_average(self, period):
        """
        Calculate Exponential Moving Average
        
        Args:
            period: Number of periods for EMA
            
        Returns:
            pandas.Series: EMA values
        """
        return self.data['Close'].ewm(span=period).mean()
    
    def rsi(self, period=14):
        """
        Calculate Relative Strength Index
        
        Args:
            period: Period for RSI calculation (default 14)
            
        Returns:
            pandas.Series: RSI values
        """
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def macd(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            
        Returns:
            tuple: (MACD line, Signal line, Histogram)
        """
        ema_fast = self.exponential_moving_average(fast_period)
        ema_slow = self.exponential_moving_average(slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def bollinger_bands(self, period=20, std_dev=2):
        """
        Calculate Bollinger Bands
        
        Args:
            period: Period for moving average (default 20)
            std_dev: Number of standard deviations (default 2)
            
        Returns:
            tuple: (Upper band, Middle band, Lower band)
        """
        middle_band = self.moving_average(period)
        std = self.data['Close'].rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    def stochastic_oscillator(self, k_period=14, d_period=3):
        """
        Calculate Stochastic Oscillator
        
        Args:
            k_period: Period for %K calculation (default 14)
            d_period: Period for %D calculation (default 3)
            
        Returns:
            tuple: (%K, %D)
        """
        lowest_low = self.data['Low'].rolling(window=k_period).min()
        highest_high = self.data['High'].rolling(window=k_period).max()
        
        k_percent = 100 * ((self.data['Close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    def average_true_range(self, period=14):
        """
        Calculate Average True Range (ATR)
        
        Args:
            period: Period for ATR calculation (default 14)
            
        Returns:
            pandas.Series: ATR values
        """
        high_low = self.data['High'] - self.data['Low']
        high_close_prev = np.abs(self.data['High'] - self.data['Close'].shift(1))
        low_close_prev = np.abs(self.data['Low'] - self.data['Close'].shift(1))
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def williams_r(self, period=14):
        """
        Calculate Williams %R
        
        Args:
            period: Period for calculation (default 14)
            
        Returns:
            pandas.Series: Williams %R values
        """
        highest_high = self.data['High'].rolling(window=period).max()
        lowest_low = self.data['Low'].rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - self.data['Close']) / (highest_high - lowest_low))
        
        return williams_r
    
    def commodity_channel_index(self, period=20):
        """
        Calculate Commodity Channel Index (CCI)
        
        Args:
            period: Period for calculation (default 20)
            
        Returns:
            pandas.Series: CCI values
        """
        typical_price = (self.data['High'] + self.data['Low'] + self.data['Close']) / 3
        ma_typical = typical_price.rolling(window=period).mean()
        mean_deviation = np.abs(typical_price - ma_typical).rolling(window=period).mean()
        
        cci = (typical_price - ma_typical) / (0.015 * mean_deviation)
        
        return cci
    
    def on_balance_volume(self):
        """
        Calculate On Balance Volume (OBV)
        
        Returns:
            pandas.Series: OBV values
        """
        obv = []
        obv_value = 0
        
        for i in range(len(self.data)):
            if i == 0:
                obv.append(self.data['Volume'].iloc[i])
                obv_value = self.data['Volume'].iloc[i]
            else:
                if self.data['Close'].iloc[i] > self.data['Close'].iloc[i-1]:
                    obv_value += self.data['Volume'].iloc[i]
                elif self.data['Close'].iloc[i] < self.data['Close'].iloc[i-1]:
                    obv_value -= self.data['Volume'].iloc[i]
                # If close is unchanged, OBV remains the same
                obv.append(obv_value)
        
        return pd.Series(obv, index=self.data.index)
