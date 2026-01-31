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
│   ├── convertible_technical_analysis.py  # Convertible bond technical analysis
│   ├── factors/         # Factor analysis modules
│   │   ├── sentiment_analyzer.py      # Market sentiment factors (breadth, limit-up stats)
│   │   ├── money_flow_analyzer.py     # Capital flow factors (main force, northbound)
│   │   └── etf_lof_specific.py        # ETF/LOF specific factors (premium, arbitrage)
│   └── etf_lof_gamble.py  # ETF/LOF speculative analysis with enhanced factors
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

### Factor Analysis Modules

位于 `analysis/factors/`

**模块架构:**
```
analysis/factors/
├── __init__.py           # Module exports
├── sentiment_analyzer.py # Market sentiment factors
├── money_flow_analyzer.py    # Capital flow factors
└── etf_lof_specific.py   # ETF/LOF specific factors
```

#### SentimentAnalyzer - 市场情绪因子分析

位于 `analysis/factors/sentiment_analyzer.py`

**核心功能:**
- `get_market_breadth()` - 获取市场宽度统计数据（上涨/下跌家数，涨跌比）
- `get_limit_up_stats()` - 获取涨停统计数据（涨停/跌停家数和比例）
- `calculate_sentiment_score()` - 计算综合情绪得分（0-100分）
- `calculate_sentiment_factors()` - 计算情绪因子DataFrame

**数据来源:**
- `ak.stock_zh_a_spot_em()` - A股实时行情
- `ak.stock_market_activity_legu()` - 涨停统计

**使用示例:**
```python
from data.fetchers.akshare_fetcher import AKShareFetcher
from analysis.factors.sentiment_analyzer import SentimentAnalyzer

fetcher = AKShareFetcher()
sentiment = SentimentAnalyzer(fetcher)

# 获取市场宽度
breadth = sentiment.get_market_breadth()
# {'up_count': 2500, 'down_count': 1500, 'advance_decline_ratio': 0.625}

# 获取情绪得分
score = sentiment.calculate_sentiment_score()
# 65.5 (0-100, >70偏多, <30偏空)

# 计算情绪因子
factors = sentiment.calculate_sentiment_factors(df)
# DataFrame with 'market_breadth_ratio', 'market_sentiment_score'
```

**情绪得分算法:**
1. 市场宽度得分 (0-40分): 涨跌比 > 0.7 得40分，< 0.3 得0分
2. 涨停比例得分 (0-30分): 涨停比例 > 3% 得30分，< 1% 得0分
3. 涨跌停比率得分 (0-30分): 涨停家数/跌停家数比率

**特性:**
- 5分钟缓存（TTL）
- 数据失败时返回默认中性值
- 支持 graceful degradation

#### MoneyFlowAnalyzer - 资金流因子分析

位于 `analysis/factors/money_flow_analyzer.py`

**核心功能:**
- `get_individual_fund_flow()` - 获取个股资金流数据
- `calculate_capital_accumulation()` - 计算资金累积
- `calculate_order_momentum()` - 计算大单动能
- `calculate_money_flow_factors()` - 计算资金流因子DataFrame
- `get_northbound_flow()` - 获取北向资金流

**数据来源:**
- `ak.stock_individual_fund_flow()` - 个股资金流
- `ak.stock_hsgt_individual_em()` - 北向资金

**使用示例:**
```python
from analysis.factors.money_flow_analyzer import MoneyFlowAnalyzer

flow_analyzer = MoneyFlowAnalyzer(fetcher)

# 获取资金流数据
flow_data = flow_analyzer.get_individual_fund_flow('163415', 'sz')

# 计算资金累积
accumulation = flow_analyzer.calculate_capital_accumulation(flow_data)

# 计算大单动能
momentum = flow_analyzer.calculate_order_momentum(flow_data, period=5)

# 计算资金流因子
factors = flow_analyzer.calculate_money_flow_factors(df, '163415', 'sz')
# DataFrame with 'main_force_net_inflow_ratio', 'large_order_momentum', 'capital_accumulation'
```

**计算的因子:**
- `main_force_net_inflow_ratio`: 主力净流入占比
- `large_order_momentum`: 大单动能（5日变化率）
- `capital_accumulation`: 资金累积值
- `northbound_flow`: 北向资金流向

#### ETFLOFSpecificAnalyzer - ETF/LOF特有因子

位于 `analysis/factors/etf_lof_specific.py`

**核心功能:**
- `get_premium_discount_rate()` - 获取溢价率/折价率
- `calculate_arbitrage_space()` - 计算套利空间
- `calculate_liquidity_rank()` - 计算流动性排名
- `calculate_turnover_percentile()` - 计算换手率百分位
- `calculate_etf_lof_specific_factors()` - 计算特有因子DataFrame

**数据来源:**
- `ak.fund_open_fund_info_em()` - 基金净值
- `ak.fund_etf_spot_em()` - ETF实时行情

**使用示例:**
```python
from analysis.factors.etf_lof_specific import ETFLOFSpecificAnalyzer

specific_analyzer = ETFLOFSpecificAnalyzer(fetcher)

# 获取溢价率
premium_rate = specific_analyzer.get_premium_discount_rate('163415', 'LOF')
# 0.0476 (正数=溢价, 负数=折价)

# 计算套利空间
arbitrage = specific_analyzer.calculate_arbitrage_space(premium_rate, arbitrage_cost=0.015)
# >0 表示有套利机会

# 计算ETF/LOF特有因子
factors = specific_analyzer.calculate_etf_lof_specific_factors(df, '163415', 'LOF')
# DataFrame with 'premium_discount_rate', 'arbitrage_space', 'liquidity_rank'
```

**计算的因子:**
- `premium_discount_rate`: 溢价率/折价率 (price - nav) / nav
- `arbitrage_space`: 套利空间（扣除交易成本后）
- `liquidity_rank`: 流动性排名（在同类基金中）
- `turnover_percentile`: 换手率百分位

#### PredictiveFactorAnalyzer - 增强预测因子分析

位于 `analysis/etf_lof_gamble.py`

**增强功能:**
- 新增25+因子，从原有~18个扩展到43个因子
- 集成SentimentAnalyzer、MoneyFlowAnalyzer、ETFLOFSpecificAnalyzer
- 优化AI提示词结构，包含信号阈值和因子表格

**新增因子类别:**

| 类别 | 原有因子 | 新增因子 | 总数 |
|------|----------|----------|------|
| 技术指标 | 14 | 9 | 23 |
| 情绪指标 | 0 | 6 | 6 |
| 资金流 | 0 | 5 | 5 |
| ETF/LOF特有 | 0 | 5 | 5 |
| 流动性 | 4 | 0 | 4 |

**新增技术指标:**
- OBV (能量潮) 及其移动平均和背离
- KDJ (随机指标): K值、D值、J值
- CCI (顺势指标)
- Williams %R (威廉指标)
- 价格趋势强度
- PV背离
- 价格加速度

**AI提示词增强:**
```python
from core.agent.prompts import PromptBuilder

# 信号阈值配置
SIGNAL_THRESHOLDS = {
    'rsi_14': {'overbought': 70, 'oversold': 30},
    'kdj_k': {'overbought': 80, 'oversold': 20},
    'williams_r': {'overbought': -20, 'oversold': -80},
    'bollinger_position': {'upper': 0.8, 'lower': 0.2},
    # ... 更多阈值
}

# 构建结构化提示词
prompt = PromptBuilder().build_etf_lof_gamble_prompt(
    symbol='163415',
    name='白银LOF',
    fund_type='LOF',
    abnormal_events=[],
    current_factors=factors_dict,
    feature_importance=feature_df,
    current_data=data_dict
)
```

**提示词结构:**
1. 标题和基本信息
2. 异常事件摘要（最近5个）
3. 技术面因子表格（趋势、动量、波动率）
4. 资金流因子表格
5. 情绪指标表格
6. ETF/LOF特有因子表格
7. 信号汇总统计
8. 6部分分析要求

**使用示例:**
```python
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer, PredictiveFactorAnalyzer
from analysis.factors.sentiment_analyzer import SentimentAnalyzer
from analysis.factors.money_flow_analyzer import MoneyFlowAnalyzer
from analysis.factors.etf_lof_specific import ETFLOFSpecificAnalyzer

# 初始化分析器
sentiment_analyzer = SentimentAnalyzer(fetcher)
money_flow_analyzer = MoneyFlowAnalyzer(fetcher)
specific_analyzer = ETFLOFSpecificAnalyzer(fetcher)

factor_analyzer = PredictiveFactorAnalyzer(
    sentiment_analyzer=sentiment_analyzer,
    money_flow_analyzer=money_flow_analyzer,
    specific_analyzer=specific_analyzer
)

# 计算所有43个因子
factors = factor_analyzer.calculate_all_factors(df, symbol='163415', fund_type='LOF')

# 因子列包括:
# - 技术指标: rsi_14, macd, macd_signal, macd_hist, kdj_k, kdj_d, kdj_j, cci, williams_r, ...
# - 情绪指标: market_breadth_ratio, market_sentiment_score, ...
# - 资金流: main_force_net_inflow_ratio, large_order_momentum, capital_accumulation, ...
# - ETF/LOF: premium_discount_rate, arbitrage_space, liquidity_rank, ...
```

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

### ETF/LOF投机分析

位于 `analysis/etf_lof_gamble.py`

**核心功能:**
- `detect_sudden_moves()` - 检测2-3天内的异常波动（突增突降）
- `calculate_all_factors()` - 计算技术、流动性、大宗商品特有因子
- `build_prediction_model()` - 构建预测模型识别预警信号
- `analyze_single()` - 单个标的AI深度分析
- `screen_and_analyze()` - 批量筛选和AI分析
- `get_top_factors_across_funds()` - 跨标的因子汇总

**使用示例:**
```python
from core.agent.modelscope_agent import ModelScopeAgent
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer

agent = ModelScopeAgent()
analyzer = LOFETFGambleAnalyzer(agent)

# 单个分析
result = analyzer.analyze_single('163415', '白银LOF', 'LOF')
print(result.ai_summary)  # AI分析报告

# 批量筛选
results = analyzer.screen_and_analyze(
    criteria={'window': 3, 'threshold': 0.15, 'fund_types': ['commodity']},
    top_n=20
)

# 因子汇总
factor_ranking = analyzer.get_top_factors_across_funds(results)
```

**UI页面:**
- 异常波动筛选：按时间窗口、波动阈值筛选标的
- AI深度分析：单个标的详细分析和操作建议
- 因子分析汇总：跨标的因子重要性排名

### ETF/LOF投机分析配置管理

位于 `storage/fund_selection.py`

**核心功能:**
- 保存/加载/删除命名配置
- 配置追加（自动去重）
- 支持批量分析选中标的

**使用示例:**
```python
from storage.fund_selection import FundSelectionManager
from pathlib import Path

manager = FundSelectionManager(Path(".cache/streamlit"))

# 保存配置
funds = [
    {"code": "163415", "name": "白银LOF", "type": "commodity"},
    {"code": "161226", "name": "白银基金", "type": "commodity"}
]
manager.save_config("白银LOF组合", funds)

# 加载配置
loaded = manager.load_config("白银LOF组合")

# 追加标的（自动去重）
new_funds = [{"code": "518880", "name": "黄金ETF", "type": "commodity"}]
manager.append_to_config("白银LOF组合", new_funds)

# 列出所有配置
configs = manager.list_configs()
```

**UI集成:**
- 在【ETF/LOF 投机分析】页面的"使用缓存重新计算"模式下
- 提供双栏穿梭框选择标的
- 支持保存/加载命名配置
- 支持批量分析选中标的

### Streamlit Dashboard

Located in `ui/dashboard.py`. Uses `@st.cache_resource` for agent initialization and `@st.cache_data` for analyzer instances. Pages: Home, Stock Screening, Market Analysis, ETF Analysis, Convertible Bonds.

## Module Import Paths

When adding code, use these import patterns:
```python
from core.agent.glm_agent import GLMAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher
from analysis.screening import StockScreener
from analysis.factors import SentimentAnalyzer, MoneyFlowAnalyzer, ETFLOFSpecificAnalyzer
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer, PredictiveFactorAnalyzer
from config.settings import settings
```

## Testing Strategy

- Mock AI responses in tests (don't call real APIs)
- Use `pytest` fixtures for test data
- Integration tests (marked with `@pytest.mark.integration`) require real API keys and are skipped by default
- Unit tests for individual factor analyzers: `tests/test_factors/`
- Integration tests for full analysis flow: `tests/integration/`
- Current coverage: 62+ tests (50+ passing, 12+ skipped integration tests)

**Test structure:**
```
tests/
├── test_factors/
│   ├── test_sentiment_analyzer.py      # 7 tests for SentimentAnalyzer
│   ├── test_money_flow_analyzer.py     # 6 tests for MoneyFlowAnalyzer
│   └── test_etf_lof_specific.py        # 10 tests for ETFLOFSpecificAnalyzer
├── test_etf_lof_gamble.py              # 18 tests for gamble analysis
└── integration/
    └── test_etf_lof_gamble_integration.py  # 11 integration tests
```
