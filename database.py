import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StockData(Base):
    """Store historical stock price data"""
    __tablename__ = 'stock_data'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True)
    date = Column(DateTime, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    """Store portfolio information"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="Default Portfolio")
    initial_cash = Column(Float, default=100000.0)
    current_cash = Column(Float, default=100000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    holdings = relationship("Holding", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")

class Holding(Base):
    """Store current stock holdings"""
    __tablename__ = 'holdings'
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    symbol = Column(String(10), index=True)
    quantity = Column(Integer)
    average_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

class Trade(Base):
    """Store trade history"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    symbol = Column(String(10), index=True)
    action = Column(String(10))  # BUY or SELL
    quantity = Column(Integer)
    price = Column(Float)
    total_value = Column(Float)
    order_type = Column(String(20))  # Market or Limit
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")

class Strategy(Base):
    """Store trading strategies and their parameters"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text)
    parameters = Column(Text)  # JSON string of parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    backtests = relationship("BacktestResult", back_populates="strategy")

class BacktestResult(Base):
    """Store backtest results"""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    symbol = Column(String(10))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(Float)
    final_value = Column(Float)
    total_return = Column(Float)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    num_trades = Column(Integer)
    results_data = Column(Text)  # JSON string of detailed results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")

class TechnicalIndicator(Base):
    """Store calculated technical indicators"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True)
    date = Column(DateTime, index=True)
    indicator_name = Column(String(50))
    value = Column(Float)
    parameters = Column(Text)  # JSON string of indicator parameters
    created_at = Column(DateTime, default=datetime.utcnow)

class TradingSignal(Base):
    """Store trading signals"""
    __tablename__ = 'trading_signals'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True)
    signal_type = Column(String(50))  # ma_crossover, rsi, macd, etc.
    signal_value = Column(Integer)  # 1 (buy), -1 (sell), 0 (hold)
    confidence = Column(Float)  # Signal confidence/strength
    generated_at = Column(DateTime, default=datetime.utcnow)
    parameters = Column(Text)  # JSON string of signal parameters

# Database operations class
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def store_stock_data(self, symbol, data):
        """Store stock price data"""
        session = self.get_session()
        try:
            # Clear existing data for this symbol
            session.query(StockData).filter(StockData.symbol == symbol).delete()
            
            # Insert new data
            for date, row in data.iterrows():
                stock_data = StockData(
                    symbol=symbol,
                    date=date,
                    open_price=float(row['Open']),
                    high_price=float(row['High']),
                    low_price=float(row['Low']),
                    close_price=float(row['Close']),
                    volume=int(row['Volume'])
                )
                session.add(stock_data)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """Retrieve stock data from database"""
        session = self.get_session()
        try:
            query = session.query(StockData).filter(StockData.symbol == symbol)
            
            if start_date:
                query = query.filter(StockData.date >= start_date)
            if end_date:
                query = query.filter(StockData.date <= end_date)
            
            query = query.order_by(StockData.date)
            
            data = query.all()
            
            if not data:
                return None
            
            # Convert to pandas DataFrame
            df_data = []
            for row in data:
                df_data.append({
                    'Open': row.open_price,
                    'High': row.high_price,
                    'Low': row.low_price,
                    'Close': row.close_price,
                    'Volume': row.volume
                })
            
            dates = [row.date for row in data]
            df = pd.DataFrame(df_data, index=dates)
            return df
            
        finally:
            session.close()
    
    def create_portfolio(self, name="Default Portfolio", initial_cash=100000.0):
        """Create a new portfolio"""
        session = self.get_session()
        try:
            portfolio = Portfolio(
                name=name,
                initial_cash=initial_cash,
                current_cash=initial_cash
            )
            session.add(portfolio)
            session.commit()
            return portfolio.id
        finally:
            session.close()
    
    def get_portfolio(self, portfolio_id):
        """Get portfolio by ID"""
        session = self.get_session()
        try:
            return session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        finally:
            session.close()
    
    def update_portfolio_cash(self, portfolio_id, new_cash):
        """Update portfolio cash amount"""
        session = self.get_session()
        try:
            portfolio = session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if portfolio:
                portfolio.current_cash = new_cash
                session.commit()
        finally:
            session.close()
    
    def add_trade(self, portfolio_id, symbol, action, quantity, price, order_type):
        """Add a trade record"""
        session = self.get_session()
        try:
            trade = Trade(
                portfolio_id=portfolio_id,
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                total_value=quantity * price,
                order_type=order_type
            )
            session.add(trade)
            session.commit()
            return trade.id
        finally:
            session.close()
    
    def get_trades(self, portfolio_id, limit=None):
        """Get trade history for portfolio"""
        session = self.get_session()
        try:
            query = session.query(Trade).filter(Trade.portfolio_id == portfolio_id).order_by(Trade.executed_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()
    
    def update_holding(self, portfolio_id, symbol, quantity, average_price):
        """Update or create holding"""
        session = self.get_session()
        try:
            holding = session.query(Holding).filter(
                Holding.portfolio_id == portfolio_id,
                Holding.symbol == symbol
            ).first()
            
            if holding:
                holding.quantity = quantity
                holding.average_price = average_price
            else:
                holding = Holding(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    average_price=average_price
                )
                session.add(holding)
            
            session.commit()
        finally:
            session.close()
    
    def get_holdings(self, portfolio_id):
        """Get all holdings for portfolio"""
        session = self.get_session()
        try:
            return session.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
        finally:
            session.close()
    
    def delete_holding(self, portfolio_id, symbol):
        """Delete a holding"""
        session = self.get_session()
        try:
            session.query(Holding).filter(
                Holding.portfolio_id == portfolio_id,
                Holding.symbol == symbol
            ).delete()
            session.commit()
        finally:
            session.close()
    
    def store_backtest_result(self, strategy_name, symbol, start_date, end_date, results):
        """Store backtest results"""
        session = self.get_session()
        try:
            # Get or create strategy
            strategy = session.query(Strategy).filter(Strategy.name == strategy_name).first()
            if not strategy:
                strategy = Strategy(name=strategy_name, description=f"Strategy: {strategy_name}")
                session.add(strategy)
                session.flush()
            
            # Store backtest result
            backtest = BacktestResult(
                strategy_id=strategy.id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=results.get('initial_capital', 0),
                final_value=results.get('final_value', 0),
                total_return=results.get('total_return', 0),
                annual_return=results.get('annual_return', 0),
                max_drawdown=results.get('max_drawdown', 0),
                sharpe_ratio=results.get('sharpe_ratio', 0),
                num_trades=results.get('num_trades', 0),
                results_data=json.dumps(results)
            )
            session.add(backtest)
            session.commit()
            return backtest.id
        finally:
            session.close()
    
    def get_backtest_results(self, strategy_name=None, symbol=None, limit=10):
        """Get backtest results"""
        session = self.get_session()
        try:
            query = session.query(BacktestResult)
            
            if strategy_name:
                strategy = session.query(Strategy).filter(Strategy.name == strategy_name).first()
                if strategy:
                    query = query.filter(BacktestResult.strategy_id == strategy.id)
            
            if symbol:
                query = query.filter(BacktestResult.symbol == symbol)
            
            query = query.order_by(BacktestResult.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()

# Initialize database manager
db_manager = DatabaseManager()
