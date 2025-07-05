import os
import pandas as pd
import psycopg2
from datetime import datetime
import json

class SimpleDatabaseManager:
    """Simple database manager using direct SQL queries"""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('PGHOST'),
            'port': os.getenv('PGPORT'),
            'database': os.getenv('PGDATABASE'),
            'user': os.getenv('PGUSER'),
            'password': os.getenv('PGPASSWORD')
        }
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)
    
    def create_tables(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Stock data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    open_price DECIMAL(10,2),
                    high_price DECIMAL(10,2),
                    low_price DECIMAL(10,2),
                    close_price DECIMAL(10,2),
                    volume BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                );
            """)
            
            # Portfolios table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) DEFAULT 'Default Portfolio',
                    initial_cash DECIMAL(12,2) DEFAULT 100000.00,
                    current_cash DECIMAL(12,2) DEFAULT 100000.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Holdings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    id SERIAL PRIMARY KEY,
                    portfolio_id INTEGER REFERENCES portfolios(id),
                    symbol VARCHAR(10) NOT NULL,
                    quantity INTEGER NOT NULL,
                    average_price DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(portfolio_id, symbol)
                );
            """)
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    portfolio_id INTEGER REFERENCES portfolios(id),
                    symbol VARCHAR(10) NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    quantity INTEGER NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    total_value DECIMAL(12,2) NOT NULL,
                    order_type VARCHAR(20) NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Backtest results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id SERIAL PRIMARY KEY,
                    strategy_name VARCHAR(100) NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    initial_capital DECIMAL(12,2),
                    final_value DECIMAL(12,2),
                    total_return DECIMAL(8,4),
                    annual_return DECIMAL(8,4),
                    max_drawdown DECIMAL(8,4),
                    sharpe_ratio DECIMAL(8,4),
                    num_trades INTEGER,
                    results_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            print("Database tables created successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def store_stock_data(self, symbol, data):
        """Store stock data in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete existing data for this symbol
            cursor.execute("DELETE FROM stock_data WHERE symbol = %s", (symbol,))
            
            # Insert new data
            for date, row in data.iterrows():
                cursor.execute("""
                    INSERT INTO stock_data (symbol, date, open_price, high_price, low_price, close_price, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume
                """, (
                    symbol,
                    date.date(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                ))
            
            conn.commit()
            print(f"Stored {len(data)} records for {symbol}")
            
        except Exception as e:
            conn.rollback()
            print(f"Error storing stock data: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """Retrieve stock data from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT date, open_price, high_price, low_price, close_price, volume FROM stock_data WHERE symbol = %s"
            params = [symbol]
            
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            
            query += " ORDER BY date"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Convert to DataFrame
            data = []
            dates = []
            for row in rows:
                dates.append(row[0])
                data.append({
                    'Open': float(row[1]),
                    'High': float(row[2]),
                    'Low': float(row[3]),
                    'Close': float(row[4]),
                    'Volume': int(row[5])
                })
            
            df = pd.DataFrame(data, index=pd.to_datetime(dates))
            return df
            
        finally:
            cursor.close()
            conn.close()
    
    def create_portfolio(self, name="Default Portfolio", initial_cash=100000.0):
        """Create a new portfolio"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO portfolios (name, initial_cash, current_cash)
                VALUES (%s, %s, %s) RETURNING id
            """, (name, initial_cash, initial_cash))
            
            portfolio_id = cursor.fetchone()[0]
            conn.commit()
            print(f"Created portfolio {portfolio_id}: {name}")
            return portfolio_id
            
        except Exception as e:
            conn.rollback()
            print(f"Error creating portfolio: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_portfolio(self, portfolio_id):
        """Get portfolio by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM portfolios WHERE id = %s", (portfolio_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'initial_cash': float(row[2]),
                    'current_cash': float(row[3]),
                    'created_at': row[4],
                    'updated_at': row[5]
                }
            return None
            
        finally:
            cursor.close()
            conn.close()
    
    def update_portfolio_cash(self, portfolio_id, new_cash):
        """Update portfolio cash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE portfolios 
                SET current_cash = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (new_cash, portfolio_id))
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating portfolio cash: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def add_trade(self, portfolio_id, symbol, action, quantity, price, order_type):
        """Add a trade record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            total_value = quantity * price
            cursor.execute("""
                INSERT INTO trades (portfolio_id, symbol, action, quantity, price, total_value, order_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (portfolio_id, symbol, action, quantity, price, total_value, order_type))
            
            trade_id = cursor.fetchone()[0]
            conn.commit()
            return trade_id
            
        except Exception as e:
            conn.rollback()
            print(f"Error adding trade: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_trades(self, portfolio_id, limit=None):
        """Get trade history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM trades WHERE portfolio_id = %s ORDER BY executed_at DESC"
            params = [portfolio_id]
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            trades = []
            for row in rows:
                trades.append({
                    'id': row[0],
                    'portfolio_id': row[1],
                    'symbol': row[2],
                    'action': row[3],
                    'quantity': row[4],
                    'price': float(row[5]),
                    'total_value': float(row[6]),
                    'order_type': row[7],
                    'executed_at': row[8]
                })
            
            return trades
            
        finally:
            cursor.close()
            conn.close()
    
    def update_holding(self, portfolio_id, symbol, quantity, average_price):
        """Update or create holding"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if quantity > 0:
                cursor.execute("""
                    INSERT INTO holdings (portfolio_id, symbol, quantity, average_price)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (portfolio_id, symbol) 
                    DO UPDATE SET 
                        quantity = EXCLUDED.quantity,
                        average_price = EXCLUDED.average_price,
                        updated_at = CURRENT_TIMESTAMP
                """, (portfolio_id, symbol, quantity, average_price))
            else:
                # Delete holding if quantity is 0
                cursor.execute("""
                    DELETE FROM holdings WHERE portfolio_id = %s AND symbol = %s
                """, (portfolio_id, symbol))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating holding: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_holdings(self, portfolio_id):
        """Get all holdings for portfolio"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM holdings WHERE portfolio_id = %s", (portfolio_id,))
            rows = cursor.fetchall()
            
            holdings = []
            for row in rows:
                holdings.append({
                    'id': row[0],
                    'portfolio_id': row[1],
                    'symbol': row[2],
                    'quantity': row[3],
                    'average_price': float(row[4]),
                    'created_at': row[5],
                    'updated_at': row[6]
                })
            
            return holdings
            
        finally:
            cursor.close()
            conn.close()
    
    def store_backtest_result(self, strategy_name, symbol, start_date, end_date, results):
        """Store backtest results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO backtest_results 
                (strategy_name, symbol, start_date, end_date, initial_capital, final_value, 
                 total_return, annual_return, max_drawdown, sharpe_ratio, num_trades, results_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                strategy_name, symbol, start_date, end_date,
                results.get('initial_capital', 0),
                results.get('final_value', 0),
                results.get('total_return', 0),
                results.get('annual_return', 0),
                results.get('max_drawdown', 0),
                results.get('sharpe_ratio', 0),
                results.get('num_trades', 0),
                json.dumps(results)
            ))
            
            backtest_id = cursor.fetchone()[0]
            conn.commit()
            return backtest_id
            
        except Exception as e:
            conn.rollback()
            print(f"Error storing backtest result: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

# Initialize database manager
simple_db = SimpleDatabaseManager()