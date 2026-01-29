# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Money-Agent is an AI-powered investment research platform for China's A-share market. It uses GLM-4.7 (Zhipu AI) to analyze stocks, ETFs, and convertible bonds, with data sourced via AKShare and a Streamlit-based web UI.

## Development Commands

### Package Management (UV)
```bash
# Install dependencies
uv sync

# Run Python scripts via UV
uv run python script.py

# Run Streamlit dashboard
uv run streamlit run ui/dashboard.py
```

### Starting the Web UI
```bash
# Linux/macOS
./run_ui.sh

# Windows
run_ui.bat

# Or directly
uv run streamlit run ui/dashboard.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_screening.py

# Run specific test case
uv run pytest tests/test_screening.py::test_stock_screening_with_mock

# Coverage report
uv run pytest --cov=. --cov-report=html
```

## Architecture

### Core Module Structure

```
money-agent/
├── core/agent/          # AI Agent layer
│   ├── base_agent.py    # Abstract base class for AI agents
│   ├── glm_agent.py     # GLM-4.7 implementation
│   └── prompts.py       # Prompt engineering for all analysis types
├── data/fetchers/       # Data layer
│   └── akshare_fetcher.py  # AKShare integration for A-share data
├── analysis/            # Business logic layer
│   ├── screening.py     # Stock screening by financial metrics
│   ├── market_analysis.py  # Market index analysis
│   ├── etf_analysis.py  # ETF analysis and recommendations
│   ├── convertible_analysis.py  # Convertible bond analysis (double-low strategy)
│   └── convertible_technical_analysis.py  # Convertible bond technical analysis
├── config/              # Configuration
│   └── settings.py      # Pydantic settings (reads from .env)
└── ui/                  # Presentation layer
    └── dashboard.py     # Streamlit web interface
```

### Key Design Patterns

1. **Agent Pattern**: `BaseAgent` abstract class with `GLMAgent` implementation. To add new AI models, extend `BaseAgent` and implement `chat()` and `stream_chat()` methods.

2. **Prompt Builder Pattern**: `PromptBuilder` in `core/agent/prompts.py` centralizes all prompt construction. Each analysis type has a dedicated `build_*_prompt()` method.

3. **Analyzer Pattern**: Each module in `analysis/` takes an Agent instance and orchestrates data fetching + AI analysis. Example:
   - `StockScreener(agent)` screens stocks by financial criteria
   - `MarketAnalyzer(agent)` analyzes market indices
   - `ETFAnalyzer(agent)` provides ETF analysis/recommendations
   - `ConvertibleBondAnalyzer(agent)` analyzes convertible bonds
   - `ConvertibleBondTechnicalAnalyzer(agent)` analyzes convertible bond technical indicators

4. **Data Fetcher Pattern**: `AKShareFetcher` provides methods for all data types. It normalizes column names from Chinese to English via `COLUMN_MAPPING`.

### AI Agent Usage

All analyzers depend on an AI agent instance:
```python
from core.agent.glm_agent import GLMAgent
from analysis.screening import StockScreener

agent = GLMAgent()  # Uses GLM_API_KEY from .env
screener = StockScreener(agent)
result = screener.screen_stocks({"pe": {"max": 30}, "roe": {"min": 15}}, top_n=10)
```

### Configuration

Settings are managed via `config/settings.py` using Pydantic. Required environment variable:
- `GLM_API_KEY`: Zhipu AI API key (required)

Optional settings in `.env`:
- `GLM_API_BASE`: API endpoint (default: https://open.bigmodel.cn/api/paas/v4)
- `GLM_MODEL`: Model version (default: glm-4-plus)

### Analysis Modules

- **Stock Screening**: Filters stocks by PE, PB, ROE, PS, dividend yield. Returns structured stock data with AI reasoning.
- **Market Analysis**: Analyzes indices (Shanghai, CSI 300, CSI 500, Shenzhen, ChiNext). Provides sentiment analysis.
- **ETF Analysis**: Single ETF analysis + category-based recommendations (宽基/行业/债券/商品/跨境)
- **Convertible Bonds**: Single bond analysis + "double-low" strategy (low price + low premium rate screening)

### 可转债技术面分析模块

位于 `analysis/convertible_technical_analysis.py`

**核心功能:**
- `analyze_technical()` - 单券技术面深度分析
- `analyze_terms()` - 条款博弈分析
- `screen_by_technical()` - 批量筛选

**使用示例:**
```python
from core.agent.glm_agent import GLMAgent
from analysis.convertible_technical_analysis import ConvertibleBondTechnicalAnalyzer

agent = GLMAgent()
analyzer = ConvertibleBondTechnicalAnalyzer(agent)

# 技术面分析
result = analyzer.analyze_technical('113527')

# 条款博弈分析
terms = analyzer.analyze_terms('113527', stock_price=125.0)

# 批量筛选
results = analyzer.screen_by_technical({"price_range": (100, 110)})
```

**数据获取扩展:**
- `get_convertible_detail()` - 获取单个转债详细信息
- `get_convertible_realtime()` - 获取实时行情
- `get_convertible_history()` - 获取历史价格数据
- `calculate_indicators()` - 计算技术指标（MA5, MA20, 波动率）

**分析维度:**
1. 定位判断：偏股型/平衡型/偏债型
2. 估值分析：价格、溢价率、YTM评估
3. 动能分析：价格趋势、成交量、波动率
4. 条款博弈：强赎、回售、下修触发分析
5. 流动性分析：成交额评估
6. 投资建议：买入/持有/卖出

### Streamlit Dashboard

Located in `ui/dashboard.py`. Uses `@st.cache_resource` for agent initialization and `@st.cache_data` for analyzer instances. Pages: Home, Stock Screening, Market Analysis, ETF Analysis, Convertible Bonds.

## Module Import Paths

When adding code, use these import patterns:
```python
from core.agent.glm_agent import GLMAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher
from analysis.screening import StockScreener
from config.settings import settings
```

## Testing Strategy

- Mock AI responses in tests (don't call real APIs)
- Use `pytest` fixtures for test data
- Integration tests (marked with `@pytest.mark.integration`) require real API keys and are skipped by default
- Current coverage: 62 tests (58 passing, 4 skipped integration tests)
