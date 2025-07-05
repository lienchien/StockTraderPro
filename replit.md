# Automated Stock Trading System

## Overview

This is a Streamlit-based automated stock trading system that provides technical analysis, backtesting capabilities, and portfolio management for stock trading strategies. The application uses real-time market data from Yahoo Finance and implements various technical indicators to generate trading signals.

## System Architecture

The system follows a modular architecture with separate components for different functionalities:

- **Frontend**: Streamlit web application providing an interactive dashboard
- **Data Source**: Yahoo Finance API (yfinance) for real-time and historical stock data
- **Technical Analysis Engine**: Custom implementation of technical indicators
- **Backtesting Engine**: Strategy testing framework
- **Portfolio Management**: Trade tracking and performance monitoring
- **Signal Generation**: Automated trading signal generation

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Streamlit frontend application and navigation
- **Key Features**:
  - Multi-page dashboard interface
  - Stock symbol selection
  - Date range controls
  - Session state management for portfolio
- **Technology**: Streamlit, Plotly for visualizations

### 2. Technical Analysis (`technical_analysis.py`)
- **Purpose**: Calculate technical indicators
- **Indicators Implemented**:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
- **Design Pattern**: Class-based approach with data encapsulation

### 3. Trading Signals (`trading_signals.py`)
- **Purpose**: Generate buy/sell/hold signals based on technical analysis
- **Strategies**:
  - Moving Average Crossover
  - RSI Mean Reversion
- **Output**: Integer signals (1 = buy, -1 = sell, 0 = hold)

### 4. Backtesting Engine (`backtesting.py`)
- **Purpose**: Test trading strategies against historical data
- **Features**:
  - Strategy performance evaluation
  - Trade history tracking
  - Portfolio value tracking
- **Supported Strategies**: MA Crossover, RSI Mean Reversion, MACD

### 5. Portfolio Management (`portfolio.py`)
- **Purpose**: Track holdings, cash, and performance metrics
- **Key Metrics**:
  - Total portfolio value
  - Total return percentage
  - Daily change tracking
- **Data Storage**: In-memory Python objects

## Data Flow

1. **Data Ingestion**: Yahoo Finance API provides real-time/historical stock data
2. **Technical Analysis**: Raw price data is processed to calculate indicators
3. **Signal Generation**: Technical indicators are analyzed to generate trading signals
4. **Strategy Execution**: Signals are processed through backtesting or live trading
5. **Portfolio Updates**: Trades update portfolio holdings and cash positions
6. **Performance Tracking**: Portfolio values and returns are calculated and displayed

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **yfinance**: Yahoo Finance data provider
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **plotly**: Interactive visualizations

### Data Sources
- **Yahoo Finance**: Primary data source for stock prices and market data

## Deployment Strategy

- **Platform**: Replit-based deployment
- **Architecture**: Single-instance Streamlit application
- **Session Management**: Streamlit session state for user data persistence
- **Scalability**: Designed for individual user sessions

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 05, 2025. Initial setup