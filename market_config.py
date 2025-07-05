"""
Market configuration for different stock exchanges
"""

class MarketConfig:
    """Configuration for different stock markets"""
    
    MARKETS = {
        "US": {
            "name": "美國股市 (US Market)",
            "suffix": "",
            "currency": "USD",
            "popular_stocks": [
                ("AAPL", "Apple Inc."),
                ("GOOGL", "Alphabet Inc."),
                ("MSFT", "Microsoft Corporation"),
                ("AMZN", "Amazon.com Inc."),
                ("TSLA", "Tesla Inc."),
                ("NVDA", "NVIDIA Corporation"),
                ("META", "Meta Platforms Inc."),
                ("TSM", "Taiwan Semiconductor")
            ],
            "index": "^GSPC",
            "index_name": "S&P 500",
            "timezone": "America/New_York",
            "trading_hours": "09:30-16:00 EST"
        },
        "TW": {
            "name": "台灣股市 (Taiwan Market)",
            "suffix": ".TW",
            "currency": "TWD",
            "popular_stocks": [
                ("2330", "台積電 (TSMC)"),
                ("2317", "鴻海 (Hon Hai)"),
                ("2454", "聯發科 (MediaTek)"),
                ("2412", "中華電 (Chunghwa Telecom)"),
                ("2303", "聯電 (UMC)"),
                ("2881", "富邦金 (Fubon Financial)"),
                ("2882", "國泰金 (Cathay Financial)"),
                ("2891", "中信金 (CTBC Financial)")
            ],
            "index": "^TWII",
            "index_name": "台股加權指數 (TWSE Index)",
            "timezone": "Asia/Taipei",
            "trading_hours": "09:00-13:45 TST"
        }
    }
    
    @classmethod
    def get_market_list(cls):
        """Get list of available markets"""
        return list(cls.MARKETS.keys())
    
    @classmethod
    def get_market_info(cls, market_code):
        """Get market information"""
        return cls.MARKETS.get(market_code, cls.MARKETS["US"])
    
    @classmethod
    def format_symbol(cls, symbol, market_code):
        """Format symbol with market suffix"""
        market_info = cls.get_market_info(market_code)
        suffix = market_info["suffix"]
        
        # Remove existing suffix if present
        if "." in symbol:
            symbol = symbol.split(".")[0]
        
        return f"{symbol}{suffix}" if suffix else symbol
    
    @classmethod
    def get_popular_stocks(cls, market_code):
        """Get popular stocks for a market"""
        market_info = cls.get_market_info(market_code)
        return market_info["popular_stocks"]
    
    @classmethod
    def get_market_index(cls, market_code):
        """Get market index symbol"""
        market_info = cls.get_market_info(market_code)
        return market_info["index"]
    
    @classmethod
    def validate_symbol(cls, symbol, market_code):
        """Validate symbol format for market"""
        market_info = cls.get_market_info(market_code)
        
        if market_code == "TW":
            # Taiwan stocks are usually 4-digit numbers
            base_symbol = symbol.replace(".TW", "")
            if not base_symbol.isdigit() or len(base_symbol) != 4:
                return False, "台灣股票代碼應為4位數字 (例: 2330)"
        elif market_code == "US":
            # US stocks are usually alphabetic
            base_symbol = symbol.replace(".", "")
            if not base_symbol.isalpha():
                return False, "美國股票代碼應為英文字母 (例: AAPL)"
        
        return True, "有效的股票代碼"