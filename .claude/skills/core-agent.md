---
name: money-agent-core
description: Core AI Agent module for Money-Agent. Use when working with AI model integrations, extending BaseAgent for new AI providers, implementing GLMAgent, or using PromptBuilder for financial analysis prompts. Covers the agent abstraction layer, GLM-4.7 integration, and prompt engineering patterns for stock/market/ETF/convertible bond analysis.
---

# Core Agent Module

## Overview

The core agent module provides the AI abstraction layer for Money-Agent. It defines the `BaseAgent` abstract class that all AI model implementations must extend, and includes the `GLMAgent` implementation for Zhipu AI's GLM-4.7 model.

## Architecture

```
core/agent/
├── base_agent.py      # Abstract base class
├── glm_agent.py       # GLM-4.7 implementation
└── prompts.py         # Prompt builder for all analysis types
```

## BaseAgent Abstract Class

Location: `core/agent/base_agent.py`

All AI agent implementations must extend `BaseAgent`:

```python
from abc import ABC, abstractmethod
from typing import Optional

class BaseAgent(ABC):
    def __init__(self, model_name: str, temperature: float = 0.7, max_tokens: int = 2000):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> Optional[str]:
        """Send chat request and return response"""
        pass

    @abstractmethod
    def stream_chat(self, prompt: str, **kwargs):
        """Stream chat response as generator"""
        pass
```

### Adding New AI Model Integrations

To add support for a new AI model (e.g., Claude, GPT):

1. Create a new class extending `BaseAgent`
2. Implement `chat()` and `stream_chat()` methods
3. Use `config/settings.py` for API credentials

Example template:

```python
from core.agent.base_agent import BaseAgent
from config.settings import settings
from typing import Optional, Generator

class NewModelAgent(BaseAgent):
    def __init__(self, model_name: str = None, temperature: float = 0.7, max_tokens: int = 2000):
        model_name = model_name or settings.new_model_default
        super().__init__(model_name, temperature, max_tokens)
        # Initialize your API client here
        self.client = ...

    def chat(self, prompt: str, **kwargs) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None

    def stream_chat(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Stream API call failed: {e}")
            yield f"Error: {e}"
```

## GLMAgent Implementation

Location: `core/agent/glm_agent.py`

The `GLMAgent` class provides integration with Zhipu AI's GLM-4.7 model.

### Usage

```python
from core.agent.glm_agent import GLMAgent

# Initialize with defaults (reads from settings)
agent = GLMAgent()

# Initialize with custom parameters
agent = GLMAgent(
    model_name="glm-4-plus",
    temperature=0.5,
    max_tokens=4000
)

# Simple chat
response = agent.chat("Analyze this stock...")
print(response)

# Stream chat
for chunk in agent.stream_chat("Analyze this stock..."):
    print(chunk, end="")
```

### Configuration

GLMAgent reads from `config/settings.py`:

- `GLM_API_KEY`: API key (required)
- `GLM_API_BASE`: API endpoint (default: https://open.bigmodel.cn/api/paas/v4)
- `GLM_MODEL`: Default model (default: glm-4-plus)

## PromptBuilder

Location: `core/agent/prompts.py`

`PromptBuilder` centralizes all prompt construction for financial analysis tasks.

### Usage

```python
from core.agent.prompts import PromptBuilder

builder = PromptBuilder()

# Stock screening prompt
prompt = builder.build_stock_screening_prompt(
    criteria={"pe": {"max": 30}, "roe": {"min": 15}},
    stock_count=10
)

# Market analysis prompt
prompt = builder.build_market_analysis_prompt(
    index_code="000001",
    date="2026-01-28"
)

# Stock analysis prompt
prompt = builder.build_stock_analysis_prompt(
    symbol="600519",
    company_name="贵州茅台",
    analysis_type="comprehensive"  # or "technical", "fundamental"
)

# ETF analysis prompt
prompt = builder.build_etf_analysis_prompt(
    etf_code="510300",
    etf_name="沪深300ETF"
)

# Convertible bond analysis prompt
prompt = builder.build_convertible_analysis_prompt(
    cb_code="113527",
    cb_name="广电转债"
)
```

### Adding New Prompt Types

To add a new prompt type:

1. Add a method to `PromptBuilder` class
2. Follow naming convention: `build_<analysis_type>_prompt()`
3. Include detailed task description in prompt
4. Return formatted prompt string

Example:

```python
def build_portfolio_analysis_prompt(self, holdings: List[Dict]) -> str:
    prompt = f"""请对以下投资组合进行分析：

持仓信息：
{json.dumps(holdings, ensure_ascii=False, indent=2)}

请重点分析：
1. 组合配置分析
2. 风险评估
3. 收益预期
4. 优化建议

请提供详细的投资组合分析报告。"""
    return prompt
```

## Common Patterns

### Error Handling

Always wrap API calls in try-except and return `None` on error:

```python
def chat(self, prompt: str, **kwargs) -> Optional[str]:
    try:
        # API call
        return response
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None
```

### Response Processing

Analyzers should handle `None` responses from agents:

```python
response = self.agent.chat(prompt)
if not response:
    return {"error": "AI analysis failed"}
```

## Testing

Mock agent responses in tests using `unittest.mock`:

```python
from unittest.mock import Mock, patch

def test_screener_with_mock():
    mock_agent = Mock()
    mock_agent.chat.return_value = "Sample AI response..."
    screener = StockScreener(mock_agent)
    result = screener.screen_stocks({"pe": {"max": 30}})
    assert result["stocks"]
```
