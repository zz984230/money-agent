# Tushare Pro API Integration Design

**Date**: 2026-01-29
**Author**: Claude
**Status**: Approved

## Overview

This document describes the design for integrating Tushare Pro API to fetch the latest financial data for convertible bond analysis. The integration addresses the issue of outdated financial data in AI analysis reports.

### Problem Statement

The current convertible bond analysis has the following data limitations:

1. **AKShare Limitations**: `bond_cb_jsl()` only provides market data (prices, volumes) but not complete financial statements
2. **AI Knowledge Base Limitations**: AI models have time cutoffs, resulting in outdated financial data (e.g., 2023 reports instead of 2024)
3. **User Impact**: Analysis reports don't contain the latest quarterly/annual financial data

### Solution

Integrate Tushare Pro API as a supplementary data source to fetch:
- Latest income statements (利润表)
- Latest balance sheets (资产负债表)
- Latest cash flow statements (现金流量表)

### Key Design Decisions

1. **Required Data**: Tushare data is REQUIRED (not optional). If Tushare API fails, the system directly shows an error to the user.
2. **No Fallback**: No degradation to old data when Tushare fails.
3. **Real-time Fetching**: Data is fetched on-demand when users analyze convertible bonds.
4. **Independent Implementation**: `TushareFetcher` is independent from `AKShareFetcher`.

## Architecture

### Data Flow

```
User Input (cb_name)
    ↓
ConvertibleBondAnalyzer.analyze_convertible_by_name()
    ↓
ConvertibleBondAnalyzer.analyze_convertible()
    ↓
┌─────────────────────────────────────┐
│  Get Convertible List (AKShare)     │
│  - Market data (price, change)      │
│  - Stock code (6-digit format)      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Get Financial Data (Tushare)       │
│  - Convert: 688798 → 688798.SH      │
│  - Fetch: income, balance, cashflow │
│  - On failure: RETURN ERROR         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Format Combined Data               │
│  - Market data + Financial data     │
└─────────────────────────────────────┘
    ↓
AI Agent Analysis (with latest data)
```

### Module Structure

```
data/fetchers/
├── __init__.py
├── akshare_fetcher.py          # Existing: AKShare integration
└── tushare_fetcher.py          # New: Tushare Pro integration

analysis/
└── convertible_analysis.py     # Modified: Integrates TushareFetcher

tests/
├── test_tushare_fetcher.py           # New: TushareFetcher unit tests
└── test_convertible_analysis_tushare.py  # New: Integration tests
```

## Implementation Details

### 1. TushareFetcher Class

**File**: `data/fetchers/tushare_fetcher.py`

**Key Methods**:

```python
class TushareFetcher:
    def __init__(self, token: str = None)
        # Initialize with Tushare Pro token
        # Reads from settings.tushare_token if not provided

    def get_latest_financials(self, ts_code: str) -> Optional[Dict]
        # Fetch latest financial data from Tushare
        # Returns: income, balance, cashflow, report_date
        # Raises: RuntimeError on any API failure

    def get_basic_info(self, ts_code: str) -> Optional[Dict]
        # Fetch basic stock information

    @staticmethod
    def stock_code_to_ts_code(stock_code: str) -> str
        # Convert 6-digit code to Tushare format
        # Examples:
        #   688798 → 688798.SH (Shanghai)
        #   000001 → 000001.SZ (Shenzhen)
        #   832566 → 832566.BJ (Beijing)
```

**Error Handling**:

- `__init__`: Raises `ValueError` if token is not provided
- `get_latest_financials`: Raises `RuntimeError` if any API call fails
- All errors are propagated to the caller

### 2. ConvertibleBondAnalyzer Integration

**File**: `analysis/convertible_analysis.py`

**Modifications**:

```python
class ConvertibleBondAnalyzer:
    def __init__(self, agent: BaseAgent):
        # ...
        self.tushare_fetcher = None  # Lazy initialization

    def _ensure_tushare_fetcher(self) -> None:
        """Lazy initialization of TushareFetcher"""
        if self.tushare_fetcher is None:
            try:
                self.tushare_fetcher = TushareFetcher()
            except ValueError as e:
                raise RuntimeError(f"Tushare Token 未配置: {e}")

    def _get_stock_financial_data(self, stock_code: str) -> str:
        """Fetch and format stock financial data"""
        self._ensure_tushare_fetcher()
        ts_code = TushareFetcher.stock_code_to_ts_code(stock_code)
        financials = self.tushare_fetcher.get_latest_financials(ts_code)
        return self._format_financial_data(financials)

    def analyze_convertible(self, cb_code, cb_name, use_ai_only=False):
        # ...
        # 1. Get market data from AKShare
        # 2. Get financial data from Tushare
        #    - If Tushare fails: return error dict immediately
        # 3. Combine data and send to AI
```

**Error Handling**:

```python
try:
    financial_summary = self._get_stock_financial_data(stock_code)
except RuntimeError as e:
    # Tushare failed - return error without calling AI
    return {
        "cb_code": cb_code,
        "cb_name": cb_name,
        "data": cb_data_dict,
        "analysis": "",
        "summary": f"获取正股财务数据失败: {e}",
        "error": str(e)
    }
```

### 3. UI Error Handling

**File**: `ui/dashboard.py`

**Added specific error handling for Tushare failures**:

```python
if result.get("error"):
    st.markdown(f"""
    <div class="error-box">
        <h4>获取财务数据失败</h4>
        <p><strong>错误信息：</strong>{result.get('summary', '')}</p>
        <p><strong>解决方案：</strong></p>
        <ul>
            <li>确保已在 .env 文件中配置 TUSHARE_TOKEN</li>
            <li>确认 Tushare Pro Token 有效且有积分余额</li>
            <li>检查网络连接是否正常</li>
            <li>访问 <a href="https://tushare.pro" target="_blank">Tushare Pro</a> 获取 Token</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    return
```

## Configuration

### Environment Variables

**File**: `.env`

```bash
# Tushare Pro API 配置
TUSHARE_TOKEN=your_tushare_token_here
```

### Pydantic Settings

**File**: `config/settings.py`

```python
class Settings(BaseSettings):
    # ...
    # Tushare Pro API 配置
    tushare_token: str = Field(default="", env="TUSHARE_TOKEN")
```

### Dependencies

**File**: `pyproject.toml`

```toml
dependencies = [
    # ...
    "tushare>=1.2.89",
]
```

## Error Handling

### Error Categories

1. **Configuration Error**: Token not provided
   - Error: `ValueError: Tushare Token 未提供`
   - Solution: Configure `TUSHARE_TOKEN` in `.env`

2. **API Error**: Network/timeout/authentication failure
   - Error: `RuntimeError: 获取 Tushare 财务数据失败: ...`
   - Solution: Show user-friendly error with troubleshooting steps

3. **Data Error**: Stock code not found
   - Error: `RuntimeError: 未能获取 [code] 的利润表数据`
   - Solution: Show specific data missing error

### Error Flow

```
User analyzes convertible bond with stock_code
    ↓
TushareFetcher.get_latest_financials()
    ↓
Any API call fails?
    YES → Raise RuntimeError
         ↓
    analyze_convertible() catches RuntimeError
         ↓
    Return dict with "error" field
         ↓
    UI shows error message (NO AI call)
```

## Testing

### Unit Tests

**File**: `tests/test_tushare_fetcher.py`

- Test initialization (with token, from settings, no token)
- Test `get_latest_financials()` success and failures
- Test `get_basic_info()` success and failures
- Test `stock_code_to_ts_code()` conversion (SH, SZ, BJ)

**Total**: 14 tests

### Integration Tests

**File**: `tests/test_convertible_analysis_tushare.py`

- Test successful Tushare integration with AI analysis
- Test Tushare failure → error return (no AI call)
- Test no stock code → skip Tushare
- Test lazy initialization of TushareFetcher
- Test AI-only mode (no Tushare call)

**Total**: 7 tests

### Test Results

```
tests/test_tushare_fetcher.py .............. [14 passed]
tests/test_convertible_analysis_tushare.py ....... [7 passed]
```

## Implementation Checklist

- [x] Install tushare dependency (`uv add tushare>=1.2.89`)
- [x] Create `data/fetchers/tushare_fetcher.py`
- [x] Update `data/fetchers/__init__.py` to export TushareFetcher
- [x] Update `config/settings.py` to add `tushare_token` field
- [x] Update `.env.example` to include `TUSHARE_TOKEN` template
- [x] Modify `analysis/convertible_analysis.py`:
  - [x] Import TushareFetcher
  - [x] Add lazy initialization of TushareFetcher
  - [x] Add `_get_stock_financial_data()` method
  - [x] Modify `analyze_convertible()` to integrate Tushare data
  - [x] Update `_format_convertible_dict()` to include financial reports
- [x] Update `ui/dashboard.py` with Tushare error handling
- [x] Write unit tests in `tests/test_tushare_fetcher.py`
- [x] Write integration tests in `tests/test_convertible_analysis_tushare.py`
- [x] Update existing tests in `tests/test_convertible_analysis.py`
- [x] Verify all tests pass
- [x] Create design document

## Future Enhancements

1. **Caching**: Add caching for frequently accessed financial data
2. **Batch Fetching**: Support fetching multiple stocks in one call
3. **Data Validation**: Add more robust validation of Tushare response data
4. **Backup Data Source**: Consider adding additional data sources as backup

## References

- [Tushare Pro Documentation](https://tushare.pro/document/2)
- [Tushare Pro API](https://tushare.pro/document/1)
- Project: `D:\code\money-agent`
