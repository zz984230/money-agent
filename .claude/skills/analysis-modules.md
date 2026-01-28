---
name: money-agent-analysis
description: Analysis modules for Money-Agent. Use when working with stock screening, market analysis, ETF analysis, convertible bond analysis, or understanding the common analyzer pattern. Covers StockScreener, MarketAnalyzer, ETFAnalyzer, ConvertibleBondAnalyzer classes and their AI-driven analysis workflows.
---

# Analysis Modules

## Overview

The analysis modules contain business logic for AI-driven financial analysis. Each analyzer follows a consistent pattern: take an AI Agent, fetch data via AKShareFetcher, build prompts via PromptBuilder, and return structured results.

## Architecture

```
analysis/
├── screening.py              # Stock screening by financial metrics
├── market_analysis.py        # Market index and sentiment analysis
├── etf_analysis.py           # ETF analysis and recommendations
└── convertible_analysis.py   # Convertible bond analysis (double-low strategy)
```

## Common Analyzer Pattern

All analyzers follow this pattern:

```python
from core.agent.glm_agent import GLMAgent
from core.agent.prompts import PromptBuilder

class SomeAnalyzer:
    def __init__(self, agent: GLMAgent):
        self.agent = agent
        self.prompt_builder = PromptBuilder()

    def analyze(self, ...inputs...) -> Dict:
        # 1. Build prompt
        prompt = self.prompt_builder.build_xxx_prompt(...)

        # 2. Call AI
        response = self.agent.chat(prompt)

        # 3. Process and return
        if not response:
            return {"error": "AI analysis failed"}
        return self._parse_response(response)
```

## StockScreener

Location: `analysis/screening.py`

Screens stocks based on financial metrics (PE, PB, ROE, PS, dividend yield).

### Usage

```python
from core.agent.glm_agent import GLMAgent
from analysis.screening import StockScreener

agent = GLMAgent()
screener = StockScreener(agent)

# Define criteria
criteria = {
    "pe": {"max": 30},        # PE ≤ 30
    "roe": {"min": 15},       # ROE ≥ 15%
    "pb": {"max": 3.0}        # PB ≤ 3.0
}

# Screen stocks
result = screener.screen_stocks(criteria, top_n=10)

print(result["stocks"])      # List of stock dicts
print(result["reasoning"])   # Full AI analysis
print(result["count"])       # Number of results
```

### Supported Criteria

| Key | Operations | Description |
|-----|------------|-------------|
| pe | max, min, eq | Price-to-earnings ratio |
| pb | max, min, eq | Price-to-book ratio |
| roe | max, min, eq | Return on equity (%) |
| ps | max, min, eq | Price-to-sales ratio |
| dividend_yield | max, min, eq | Dividend yield (%) |

### Response Format

```python
{
    "stocks": [
        {
            "symbol": "600519",
            "name": "贵州茅台",
            "pe": 28.5,
            "roe": 25.3,
            "reasoning": "Quality stock..."
        }
    ],
    "reasoning": "Full AI analysis text...",
    "criteria": {...},
    "count": 10
}
```

## MarketAnalyzer

Location: `analysis/market_analysis.py`

Analyzes market indices and overall market sentiment.

### Usage

```python
from analysis.market_analysis import MarketAnalyzer

analyzer = MarketAnalyzer(agent)

# Analyze specific index
result = analyzer.analyze_index(
    index_code="000001",  # Shanghai Composite
    date="2026-01-28"
)

# Analyze market sentiment
result = analyzer.analyze_sentiment()
```

### Supported Indices

| Code | Name |
|------|------|
| 000001 | 上证指数 |
| 000300 | 沪深300 |
| 000905 | 中证500 |
| 399001 | 深证成指 |
| 399006 | 创业板指 |

### Response Format

```python
{
    "index_code": "000001",
    "date": "2026-01-28",
    "data": {...},           # Index data if available
    "summary": "Brief summary",
    "analysis": "Full AI analysis..."
}
```

## ETFAnalyzer

Location: `analysis/etf_analysis.py`

Analyzes individual ETFs and provides category-based recommendations.

### Usage

```python
from analysis.etf_analysis import ETFAnalyzer

analyzer = ETFAnalyzer(agent)

# Analyze single ETF
result = analyzer.analyze_etf(
    etf_code="510300",
    etf_name="沪深300ETF"
)

# Get ETF recommendations by category
result = analyzer.recommend_etfs(
    category="宽基",  # or "行业", "债券", "商品", "跨境"
    top_n=5
)
```

### Categories

| Category | Description |
|----------|-------------|
| 宽基 | Broad market ETFs |
| 行业 | Sector/Industry ETFs |
| 债券 | Bond ETFs |
| 商品 | Commodity ETFs |
| 跨境 | Cross-border ETFs |

### Response Format

Single ETF analysis:
```python
{
    "etf_code": "510300",
    "etf_name": "沪深300ETF",
    "data": {...},
    "summary": "Brief summary",
    "analysis": "Full AI analysis..."
}
```

Recommendations:
```python
[
    {
        "etf_code": "510300",
        "etf_name": "沪深300ETF",
        "category": "宽基"
    },
    ...
]
```

## ConvertibleBondAnalyzer

Location: `analysis/convertible_analysis.py`

Analyzes convertible bonds and implements the "double-low" strategy (low price + low premium).

### Usage

```python
from analysis.convertible_analysis import ConvertibleBondAnalyzer

analyzer = ConvertibleBondAnalyzer(agent)

# Analyze single convertible bond
result = analyzer.analyze_convertible(
    cb_code="113527",
    cb_name="广电转债"
)

# Double-low strategy screening
result = analyzer.screen_double_low(
    max_price=110.0,      # Max bond price
    max_premium=30.0,     # Max premium rate (%)
    top_n=10
)
```

### Double-Low Strategy

Double-low value = bond price + premium rate. Lower is better.

```python
{
    "cb_code": "113527",
    "cb_name": "广电转债",
    "price": 105.5,
    "premium": 12.3,
    "double_low": 117.8   # price + premium
}
```

### Response Format

Single bond analysis:
```python
{
    "cb_code": "113527",
    "cb_name": "广电转债",
    "data": {...},
    "summary": "Brief summary",
    "analysis": "Full AI analysis..."
}
```

Screening results:
```python
[
    {
        "cb_code": "113527",
        "cb_name": "广电转债",
        "price": 105.5,
        "premium": 12.3,
        "double_low": 117.8
    },
    ...
]
```

## Adding New Analyzers

To add a new analyzer:

1. Create class following the pattern
2. Take agent in `__init__`
3. Use PromptBuilder for prompts
4. Return structured results

```python
from core.agent.glm_agent import GLMAgent
from core.agent.prompts import PromptBuilder

class NewAnalyzer:
    def __init__(self, agent: GLMAgent):
        self.agent = agent
        self.prompt_builder = PromptBuilder()

    def analyze_new_thing(self, input_data) -> Dict:
        prompt = self.prompt_builder.build_new_prompt(input_data)
        response = self.agent.chat(prompt)

        if not response:
            return {"error": "AI analysis failed"}

        return {
            "data": input_data,
            "analysis": response
        }
```

Then add the corresponding prompt builder method in `core/agent/prompts.py`:

```python
def build_new_prompt(self, input_data) -> str:
    prompt = f"""请对以下数据进行分析：
{input_data}
请提供详细的分析报告。"""
    return prompt
```

## Error Handling Pattern

All analyzers should handle AI failures gracefully:

```python
def some_method(self, ...) -> Dict:
    # Build prompt
    prompt = ...

    # Call AI
    response = self.agent.chat(prompt)

    # Handle failure
    if not response:
        return {
            "error": "AI分析失败，请稍后重试",
            "data": None
        }

    # Parse and return
    return self._parse_response(response)
```

## Testing with Mocked Agents

```python
from unittest.mock import Mock

def test_analyzer():
    mock_agent = Mock()
    mock_agent.chat.return_value = "Sample AI response..."

    analyzer = StockScreener(mock_agent)
    result = analyzer.screen_stocks({"pe": {"max": 30}})

    assert result["stocks"]
    mock_agent.chat.assert_called_once()
```
