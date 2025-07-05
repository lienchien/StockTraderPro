import pandas as pd
import numpy as np
from datetime import datetime
from database import db_manager

class Portfolio:
    """Portfolio management for tracking holdings and trades"""
    
    def __init__(self, initial_cash=100000):
        """
        Initialize portfolio
        
        Args:
            initial_cash: Starting cash amount
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.holdings = {}  # {symbol: {'quantity': int, 'average_price': float}}
        self.trade_history = []
        self.daily_values = []
    
    @property
    def total_value(self):
        """Calculate total portfolio value"""
        holdings_value = sum(
            data['quantity'] * self._get_current_price(symbol)
            for symbol, data in self.holdings.items()
        )
        return self.cash + holdings_value
    
    @property
    def total_return(self):
        """Calculate total return percentage"""
        return ((self.total_value - self.initial_cash) / self.initial_cash) * 100
    
    @property
    def day_change(self):
        """Calculate day change percentage (mock calculation)"""
        # This would normally use yesterday's closing values
        return np.random.uniform(-2, 2)  # Mock day change
    
    def _get_current_price(self, symbol):
        """
        Get current price for a symbol (mock implementation)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Current price
        """
        # In a real implementation, this would fetch live prices
        # For now, we'll use the average price with some variation
        if symbol in self.holdings:
            base_price = self.holdings[symbol]['average_price']
            return base_price * (1 + np.random.uniform(-0.05, 0.05))
        return 100.0  # Default price if not found
    
    def execute_order(self, order):
        """
        Execute a buy/sell order
        
        Args:
            order: Dictionary containing order details
                - symbol: Stock symbol
                - action: 'BUY' or 'SELL'
                - quantity: Number of shares
                - price: Price per share
                - timestamp: Order timestamp
                - order_type: 'Market' or 'Limit'
                
        Returns:
            bool: True if order executed successfully, False otherwise
        """
        symbol = order['symbol']
        action = order['action'].upper()
        quantity = order['quantity']
        price = order['price']
        total_cost = quantity * price
        
        if action == 'BUY':
            # Check if we have enough cash
            if total_cost > self.cash:
                return False
            
            # Execute buy order
            self.cash -= total_cost
            
            if symbol in self.holdings:
                # Update average price for existing holding
                current_quantity = self.holdings[symbol]['quantity']
                current_value = current_quantity * self.holdings[symbol]['average_price']
                new_quantity = current_quantity + quantity
                new_average_price = (current_value + total_cost) / new_quantity
                
                self.holdings[symbol] = {
                    'quantity': new_quantity,
                    'average_price': new_average_price
                }
            else:
                # New holding
                self.holdings[symbol] = {
                    'quantity': quantity,
                    'average_price': price
                }
        
        elif action == 'SELL':
            # Check if we have enough shares
            if symbol not in self.holdings or self.holdings[symbol]['quantity'] < quantity:
                return False
            
            # Execute sell order
            self.cash += total_cost
            self.holdings[symbol]['quantity'] -= quantity
            
            # Remove holding if quantity becomes zero
            if self.holdings[symbol]['quantity'] == 0:
                del self.holdings[symbol]
        
        else:
            return False
        
        # Record trade
        trade_record = {
            'timestamp': order['timestamp'],
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'total_value': total_cost,
            'order_type': order['order_type']
        }
        
        self.trade_history.append(trade_record)
        return True
    
    def get_position(self, symbol):
        """
        Get current position for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: Position details or None if no position
        """
        if symbol in self.holdings:
            current_price = self._get_current_price(symbol)
            holding = self.holdings[symbol]
            market_value = holding['quantity'] * current_price
            cost_basis = holding['quantity'] * holding['average_price']
            unrealized_pnl = market_value - cost_basis
            
            return {
                'symbol': symbol,
                'quantity': holding['quantity'],
                'average_price': holding['average_price'],
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': (unrealized_pnl / cost_basis) * 100 if cost_basis != 0 else 0
            }
        return None
    
    def get_all_positions(self):
        """
        Get all current positions
        
        Returns:
            list: List of position dictionaries
        """
        return [self.get_position(symbol) for symbol in self.holdings.keys()]
    
    def calculate_portfolio_metrics(self):
        """
        Calculate various portfolio performance metrics
        
        Returns:
            dict: Portfolio metrics
        """
        total_invested = self.initial_cash - self.cash
        positions = self.get_all_positions()
        
        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
        total_market_value = sum(pos['market_value'] for pos in positions)
        
        # Calculate sector allocation (simplified)
        sector_allocation = {}
        for pos in positions:
            # In a real implementation, you'd map symbols to sectors
            sector = "Technology"  # Simplified
            if sector not in sector_allocation:
                sector_allocation[sector] = 0
            sector_allocation[sector] += pos['market_value']
        
        # Normalize sector allocation to percentages
        if total_market_value > 0:
            sector_allocation = {
                sector: (value / total_market_value) * 100
                for sector, value in sector_allocation.items()
            }
        
        return {
            'total_value': self.total_value,
            'cash': self.cash,
            'invested_amount': total_invested,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_return_pct': self.total_return,
            'cash_allocation_pct': (self.cash / self.total_value) * 100 if self.total_value > 0 else 0,
            'equity_allocation_pct': (total_market_value / self.total_value) * 100 if self.total_value > 0 else 0,
            'sector_allocation': sector_allocation,
            'number_of_positions': len(self.holdings),
            'largest_position': max(positions, key=lambda x: x['market_value']) if positions else None
        }
    
    def export_trade_history(self):
        """
        Export trade history as DataFrame
        
        Returns:
            pandas.DataFrame: Trade history
        """
        if not self.trade_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.trade_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp', ascending=False)
    
    def reset_portfolio(self, initial_cash=None):
        """
        Reset portfolio to initial state
        
        Args:
            initial_cash: New initial cash amount (optional)
        """
        if initial_cash is not None:
            self.initial_cash = initial_cash
        
        self.cash = self.initial_cash
        self.holdings = {}
        self.trade_history = []
        self.daily_values = []
