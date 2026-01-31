---
name: money-agent-data-fetcher
description: Use when fetching A-share market data via AKShare, normalizing Chinese column names to English, adding new data sources, or understanding data retrieval patterns for stocks/ETFs/LOFs/convertible bonds/indices. Covers AKShareFetcher class methods including convertible bond details, LOF/ETF history, and column mapping patterns.
---

# Data Fetcher Module

## Overview

The data fetcher module provides a unified interface for fetching A-share market data via AKShare. It normalizes column names from Chinese to English and provides consistent data structures across all asset types.

## Architecture

```
data/fetchers/
└── akshare_fetcher.py    # AKShare integration class
```

## AKShareFetcher Class

Location: `data/fetchers/akshare_fetcher.py`

The `AKShareFetcher` class wraps AKShare API calls and normalizes response data.

### Usage

```python
from data.fetchers.akshare_fetcher import AKShareFetcher

fetcher = AKShareFetcher()

# Fetch stock list
stocks = fetcher.get_stock_list()

# Fetch stock daily data
df = fetcher.get_stock_daily("600519", "2026-01-01", "2026-01-28")

# Fetch ETF data
etf_list = fetcher.get_etf_list()
etf_df = fetcher.get_etf_daily("510300", "2026-01-01", "2026-01-28")

# Fetch convertible bond data
cb_list = fetcher.get_convertible_list()
cb_df = fetcher.get_convertible_daily("113527", "2026-01-01", "2026-01-28")

# Fetch market stats
stats = fetcher.get_market_stats()
```

## Column Normalization

AKShare returns data with Chinese column names. `AKShareFetcher` automatically maps these to English:

```python
COLUMN_MAPPING = {
    '日期': 'date',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'amount'
}
```

### Normalized Output

After processing, DataFrames have consistent English columns:

| Chinese | English | Type |
|---------|---------|------|
| 日期 | date | datetime |
| 开盘 | open | float |
| 收盘 | close | float |
| 最高 | high | float |
| 最低 | low | float |
| 成交量 | volume | int/float |
| 成交额 | amount | float |

## API Methods

### Stock Data

```python
def get_stock_list(self) -> List[Dict]:
    """Get all A-share stocks list"""

def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get stock daily OHLCV data
    Args:
        symbol: Stock code (e.g., "600519")
        start_date: Start date "YYYY-MM-DD"
        end_date: End date "YYYY-MM-DD"
    Returns:
        DataFrame with normalized columns
    """

def get_stock_info(self, symbol: str) -> Dict:
    """Get stock basic information"""
```

### ETF Data

```python
def get_etf_list(self) -> List[Dict]:
    """Get all ETF list"""

def get_etf_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get ETF daily OHLCV data
    Args:
        symbol: ETF code (e.g., "510300")
        start_date: Start date "YYYY-MM-DD"
        end_date: End date "YYYY-MM-DD"
    Returns:
        DataFrame with normalized columns
    """
```

### Convertible Bond Data

```python
def get_convertible_list(self) -> List[Dict]:
    """Get all convertible bonds list"""

def get_convertible_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get convertible bond daily data
    Note: AKShare doesn't support date filtering, done post-fetch
    """
```

### Index Data

```python
def get_index_daily(self, index_code: str, date: str) -> pd.DataFrame:
    """Get index daily data
    Args:
        index_code: Index code (e.g., "000001" for Shanghai)
        date: Target date "YYYY-MM-DD"
    Returns:
        DataFrame with last ~30 days of data
    """
```

### Market Statistics

```python
def get_market_stats(self) -> Optional[Dict]:
    """Get A-share market statistics
    Returns:
        {
            "up_count": int,
            "down_count": int,
            "unchanged_count": int,
            "limit_up_count": int,
            "limit_down_count": int,
            "total_amount": float
        }
    """
```

### Convertible Bond Extended Data

```python
def get_convertible_detail(self, cb_code: str) -> Optional[Dict]:
    """Get convertible bond detail information
    Returns:
        {
            "cb_code": str,
            "cb_name": str,
            "stock_code": str,
            "stock_name": str,
            "conversion_price": float,
            "conversion_value": float,
            "premium_rate": float,
            "stock_price": float,
            ...
        }
    """

def get_convertible_realtime(self, cb_code: str) -> Optional[Dict]:
    """Get convertible bond real-time quote
    Returns:
        {
            "price": float,
            "volume": float,
            "amount": float,
            ...
        }
    """

def get_convertible_name_by_code(self, cb_code: str) -> Optional[str]:
    """Get convertible bond name by code"""

def get_convertible_by_name(self, cb_name: str) -> Optional[str]:
    """Get convertible bond code by name"""
```

### LOF/ETF Data

```python
def get_lof_etf_history(self, symbol: str, period: int = 100) -> Optional[pd.DataFrame]:
    """Get LOF/ETF historical data
    Args:
        symbol: Fund code (e.g., "163415")
        period: Number of trading days (default: 100)
    Returns:
        DataFrame with normalized columns (date, open, high, low, close, volume)
    """

def get_commodity_lof_list(self) -> List[Dict]:
    """Get commodity LOF list
    Returns:
        [
            {"code": "163415", "name": "白银LOF", "type": "LOF"},
            ...
        ]
    """

def get_overseas_etf_list(self) -> List[Dict]:
    """Get overseas ETF list
    Returns:
        [
            {"code": "513100", "name": "纳指ETF", "type": "ETF"},
            ...
        ]
    """
```

## Adding New Data Sources

To add a new data source (e.g., Tushare, EastMoney):

1. Create a new fetcher class following the same pattern
2. Implement consistent method signatures
3. Use the same column normalization
4. Handle errors gracefully

```python
# data/fetchers/new_source_fetcher.py
import pandas as pd
from typing import List, Dict, Optional

class NewSourceFetcher:
    COLUMN_MAPPING = {
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        # ... same mapping as AKShareFetcher
    }

    def _process_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and date format"""
        existing_columns = {k: v for k, v in self.COLUMN_MAPPING.items() if k in df.columns}
        df = df.rename(columns=existing_columns)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch from new source"""
        # Your API call here
        df = new_source_api.stock_daily(symbol, start_date, end_date)
        return self._process_daily_data(df)

    # Implement other methods similarly
```

Then update analyzers to use the new fetcher:

```python
from data.fetchers.new_source_fetcher import NewSourceFetcher

fetcher = NewSourceFetcher()
```

## Error Handling

Methods that may fail should return `None` or empty collections:

```python
def get_market_stats(self) -> Optional[Dict]:
    try:
        df = ak.stock_zh_a_spot_em()
        if df.empty:
            return None
        # Process and return
    except Exception:
        return None
```

## Index Code Prefixes

For `get_index_daily()`, prefix is determined by index code:

| Code Prefix | Prefix | Example |
|-------------|--------|---------|
| 00xxxx | sh | 000001 → sh000001 (Shanghai) |
| 30xxxx, 39xxxx | sz | 399001 → sz399001 (Shenzhen) |
| other | sh | default to Shanghai |

## Testing

Mock AKShare calls in tests:

```python
from unittest.mock import patch, Mock
import pandas as pd

@patch('akshare.stock_zh_a_hist')
def test_get_stock_daily(mock_ak):
    mock_ak.return_value = pd.DataFrame({
        '日期': ['2026-01-28'],
        '开盘': [100.0],
        '收盘': [105.0]
    })

    fetcher = AKShareFetcher()
    df = fetcher.get_stock_daily("600519", "2026-01-01", "2026-01-28")

    assert 'date' in df.columns
    assert df['close'].iloc[0] == 105.0
```
