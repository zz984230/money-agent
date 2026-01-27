# Money-Agent 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 构建一个面向中国 A 股市场的 AI 投研辅助平台，支持股票、ETF、可转债的多 AI 模型竞技分析

**架构：** 基于 AI-Trader 框架，使用 AKShare 作为数据源，通过 MCP 工具链连接多个 AI 模型（GLM-4.7 等），用户作为最终决策者

**技术栈：** Python 3.10+, FastAPI, LangChain, MCP, AKShare, GLM-4.7, Streamlit

---

## 前置准备

### Task 0: 环境设置

**文件：**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: 创建 requirements.txt**

```bash
cat > requirements.txt << 'EOF'
# 核心框架
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# AI 模型
langchain==0.1.0
langchain-openai==0.0.2
zhipuai==2.1.5  # GLM-4.7

# MCP 工具链
fastmcp==0.1.0
mcp==0.9.0

# 数据源
akshare==1.12.0
pandas==2.1.0
numpy==1.24.0

# Web 框架
fastapi==0.109.0
uvicorn==0.27.0
streamlit==1.31.0
plotly==5.18.0

# 数据存储
sqlite3  # Python 标准库

# 工具
requests==2.31.0
python-dateutil==2.8.2
EOF
```

**Step 2: 创建 .env.example**

```bash
cat > .env.example << 'EOF'
# GLM-4.7 API 配置
GLM_API_KEY=your_glm_api_key_here
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4

# 数据存储路径
DATA_PATH=./data
LOG_PATH=./logs
EOF
```

**Step 3: 创建 .gitignore**

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# 环境变量
.env

# 数据文件
data/*.jsonl
data/*.csv
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Jupyter
.ipynb_checkpoints/

# 测试
.pytest_cache/
.coverage
htmlcov/
EOF
```

**Step 4: 安装依赖**

```bash
pip install -r requirements.txt
```

**Step 5: 复制环境变量文件**

```bash
cp .env.example .env
# 编辑 .env 填入你的 GLM API Key
```

**Step 6: 提交**

```bash
git add requirements.txt .env.example .gitignore
git commit -m "chore: add project dependencies and config files"
```

---

## 阶段一：基础框架搭建

### Task 1: 项目目录结构初始化

**文件：**
- Create: `core/__init__.py`
- Create: `core/agent/__init__.py`
- Create: `data/__init__.py`
- Create: `data/fetchers/__init__.py`
- Create: `analysis/__init__.py`
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `utils/__init__.py`

**Step 1: 创建目录结构**

```bash
mkdir -p core/agent data/fetchers analysis config utils ui
mkdir -p data/storage logs tests
```

**Step 2: 创建各模块的 __init__.py**

```python
# touch core/__init__.py core/agent/__init__.py data/__init__.py
# touch data/fetchers/__init__.py analysis/__init__.py
# touch config/__init__.py utils/__init__.py
```

**Step 3: 创建配置管理模块**

```python
# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path

class Settings(BaseSettings):
    """应用配置"""

    # GLM API 配置
    glm_api_key: str = Field(default="", env="GLM_API_KEY")
    glm_api_base: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        env="GLM_API_BASE"
    )
    glm_model: str = "glm-4-plus"

    # 路径配置
    project_root: Path = Field(default=Path(__file__).parent.parent)
    data_path: Path = Field(default=Path("./data"))
    log_path: Path = Field(default=Path("./logs"))

    # 数据库配置
    db_path: Path = Field(default=Path("./data/money_agent.db"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

# 全局配置实例
settings = Settings()
```

**Step 4: 创建测试验证配置加载**

```python
# tests/test_config.py
import pytest
from config.settings import settings

def test_settings_load():
    """测试配置加载"""
    assert settings.glm_api_base == "https://open.bigmodel.cn/api/paas/v4"
    assert settings.glm_model == "glm-4-plus"

def test_paths_exist():
    """测试路径创建"""
    assert settings.data_path.exists()
    assert settings.log_path.exists()
```

**Step 5: 运行测试**

```bash
pytest tests/test_config.py -v
```

**Step 6: 提交**

```bash
git add core/ data/ analysis/ config/ utils/ tests/
git commit -m "feat: initialize project structure and config management"
```

---

### Task 2: AKShare 数据获取模块

**文件：**
- Create: `data/fetchers/akshare_fetcher.py`
- Test: `tests/test_akshare_fetcher.py`

**Step 1: 编写测试 - 获取股票列表**

```python
# tests/test_akshare_fetcher.py
import pytest
from data.fetchers.akshare_fetcher import AKShareFetcher

def test_get_stock_list():
    """测试获取 A 股列表"""
    fetcher = AKShareFetcher()
    stock_list = fetcher.get_stock_list()

    assert isinstance(stock_list, list)
    assert len(stock_list) > 0
    assert 'code' in stock_list[0]
    assert 'name' in stock_list[0]

def test_get_stock_daily():
    """测试获取日线数据"""
    fetcher = AKShareFetcher()
    df = fetcher.get_stock_daily("000001", "2024-01-01", "2024-01-31")

    assert df is not None
    assert len(df) > 0
    assert 'close' in df.columns
    assert 'volume' in df.columns

def test_get_etf_list():
    """测试获取 ETF 列表"""
    fetcher = AKShareFetcher()
    etf_list = fetcher.get_etf_list()

    assert isinstance(etf_list, list)
    assert len(etf_list) > 0

def test_get_convertible_list():
    """测试获取可转债列表"""
    fetcher = AKShareFetcher()
    cb_list = fetcher.get_convertible_list()

    assert isinstance(cb_list, list)
    assert len(cb_list) > 0
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_akshare_fetcher.py -v
```

**Step 3: 实现 AKShareFetcher**

```python
# data/fetchers/akshare_fetcher.py
import akshare as ak
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

class AKShareFetcher:
    """AKShare 数据获取器"""

    def __init__(self):
        self.cache = {}

    def get_stock_list(self) -> List[Dict]:
        """获取 A 股股票列表"""
        try:
            df = ak.stock_info_a_code_name()
            return df.to_dict('records')
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []

    def get_stock_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """获取股票日线数据

        Args:
            symbol: 股票代码，如 "000001"
            start_date: 开始日期，如 "2024-01-01"
            end_date: 结束日期，如 "2024-01-31"
        """
        try:
            # AKShare 的 stock_zh_a_hist 函数获取日线数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=""
            )
            # 标准化列名
            df.rename(columns={
                '收盘': 'close',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '日期': 'date'
            }, inplace=True)
            return df
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
            return None

    def get_etf_list(self) -> List[Dict]:
        """获取 ETF 列表"""
        try:
            df = ak.fund_etf_spot_em()
            return df.to_dict('records')
        except Exception as e:
            print(f"获取 ETF 列表失败: {e}")
            return []

    def get_etf_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """获取 ETF 日线数据"""
        try:
            df = ak.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=""
            )
            df.rename(columns={
                '收盘': 'close',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '日期': 'date'
            }, inplace=True)
            return df
        except Exception as e:
            print(f"获取 ETF {symbol} 数据失败: {e}")
            return None

    def get_convertible_list(self) -> List[Dict]:
        """获取可转债列表"""
        try:
            df = ak.bond_cb_jsl()
            return df.to_dict('records')
        except Exception as e:
            print(f"获取可转债列表失败: {e}")
            return []

    def get_convertible_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """获取可转债日线数据"""
        try:
            df = ak.bond_cb_hist_em(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", "")
            )
            df.rename(columns={
                '收盘': 'close',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '日期': 'date'
            }, inplace=True)
            return df
        except Exception as e:
            print(f"获取可转债 {symbol} 数据失败: {e}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            return df.to_dict()
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return None
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_akshare_fetcher.py -v
```

**Step 5: 提交**

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher.py
git commit -m "feat: add AKShare data fetcher"
```

---

### Task 3: GLM-4.7 AI Agent 基础框架

**文件：**
- Create: `core/agent/base_agent.py`
- Create: `core/agent/glm_agent.py`
- Test: `tests/test_glm_agent.py`

**Step 1: 编写测试 - AI Agent 对话**

```python
# tests/test_glm_agent.py
import pytest
from core.agent.glm_agent import GLMAgent
from config.settings import settings

def test_glm_agent_init():
    """测试 GLM Agent 初始化"""
    agent = GLMAgent()
    assert agent.model_name == settings.glm_model

def test_glm_agent_chat():
    """测试 AI 对话功能"""
    agent = GLMAgent()
    response = agent.chat("你好，请用一句话介绍你自己")

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_glm_agent_stock_analysis():
    """测试股票分析功能"""
    agent = GLMAgent()
    prompt = "请分析贵州茅台(600519)的投资价值，从行业地位、财务状况、估值水平三个方面进行简要分析"
    response = agent.chat(prompt)

    assert response is not None
    assert isinstance(response, str)
    # 检查是否包含关键词
    assert any(keyword in response for keyword in ['茅台', '贵州茅台', '白酒', '行业'])
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_glm_agent.py -v
```

**Step 3: 实现基础 Agent 类**

```python
# core/agent/base_agent.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseAgent(ABC):
    """AI Agent 基类"""

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> Optional[str]:
        """发送对话请求"""
        pass

    @abstractmethod
    def stream_chat(self, prompt: str, **kwargs):
        """流式对话"""
        pass
```

**Step 4: 实现 GLM Agent**

```python
# core/agent/glm_agent.py
from typing import Optional, Dict, Any
from zhipuai import ZhipuAI
from core.agent.base_agent import BaseAgent
from config.settings import settings

class GLMAgent(BaseAgent):
    """智谱 GLM AI Agent"""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        model_name = model_name or settings.glm_model
        super().__init__(model_name, temperature, max_tokens)

        # 初始化 GLM 客户端
        self.client = ZhipuAI(
            api_key=settings.glm_api_key,
            base_url=settings.glm_api_base
        )

    def chat(self, prompt: str, **kwargs) -> Optional[str]:
        """发送对话请求

        Args:
            prompt: 用户提示词

        Returns:
            AI 响应文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GLM API 调用失败: {e}")
            return None

    def stream_chat(self, prompt: str, **kwargs):
        """流式对话"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"GLM 流式调用失败: {e}")
            yield None
```

**Step 5: 运行测试验证通过**

```bash
pytest tests/test_glm_agent.py -v
```

**Step 6: 提交**

```bash
git add core/agent/base_agent.py core/agent/glm_agent.py tests/test_glm_agent.py
git commit -m "feat: add GLM-4.7 AI agent framework"
```

---

### Task 4: 提示词工程模块

**文件：**
- Create: `core/agent/prompts.py`
- Test: `tests/test_prompts.py`

**Step 1: 编写测试 - 提示词生成**

```python
# tests/test_prompts.py
from core.agent.prompts import PromptBuilder

def test_build_stock_screening_prompt():
    """测试生成选股提示词"""
    builder = PromptBuilder()
    prompt = builder.build_stock_screening_prompt(
        criteria={"pe": {"max": 30}, "roe": {"min": 15}},
        stock_count=10
    )

    assert "选股" in prompt or "筛选" in prompt
    assert "PE" in prompt or "市盈率" in prompt

def test_build_market_analysis_prompt():
    """测试生成市场分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_market_analysis_prompt(
        index_code="000001",
        date="2024-01-15"
    )

    assert "分析" in prompt
    assert "000001" in prompt

def test_build_stock_analysis_prompt():
    """测试生成个股分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_stock_analysis_prompt(
        symbol="600519",
        company_name="贵州茅台"
    )

    assert "600519" in prompt or "贵州茅台" in prompt
    assert "分析" in prompt
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_prompts.py -v
```

**Step 3: 实现提示词构建器**

```python
# core/agent/prompts.py
from typing import Dict, List, Any

class PromptBuilder:
    """AI 提示词构建器"""

    def build_stock_screening_prompt(
        self,
        criteria: Dict[str, Any],
        stock_count: int = 10
    ) -> str:
        """构建选股提示词

        Args:
            criteria: 筛选条件，如 {"pe": {"max": 30}, "roe": {"min": 15}}
            stock_count: 目标股票数量
        """
        criteria_desc = self._format_criteria(criteria)

        prompt = f"""你是一位专业的 A 股投资分析师。请根据以下筛选条件，从 A 股市场中选出 {stock_count} 只符合条件的优质股票。

**筛选条件：**
{criteria_desc}

**分析要求：**
1. 从基本面角度分析每个公司的投资价值
2. 结合行业景气度和公司竞争力
3. 给出明确的推荐理由
4. 输出格式：股票代码 | 股票名称 | 推荐理由

请开始分析："""
        return prompt

    def build_market_analysis_prompt(
        self,
        index_code: str,
        date: str
    ) -> str:
        """构建市场分析提示词

        Args:
            index_code: 指数代码
            date: 分析日期
        """
        prompt = f"""你是一位专业的 A 股市场分析师。请对指数 {index_code} 在 {date} 的市场表现进行深度分析。

**分析维度：**
1. 大盘走势：涨跌幅、成交量变化
2. 市场情绪：涨跌家数比、涨停跌停数量
3. 资金流向：北向资金、主力资金动向
4. 板块表现：领涨领跌板块分析
5. 后展望：短期和中期市场判断

请提供详细的分析报告："""
        return prompt

    def build_stock_analysis_prompt(
        self,
        symbol: str,
        company_name: str,
        analysis_type: str = "comprehensive"
    ) -> str:
        """构建个股分析提示词

        Args:
            symbol: 股票代码
            company_name: 公司名称
            analysis_type: 分析类型 (comprehensive/technical/fundamental)
        """
        if analysis_type == "comprehensive":
            scope = "综合分析（技术面 + 基本面）"
        elif analysis_type == "technical":
            scope = "技术面分析（K线形态、均线系统、技术指标）"
        else:
            scope = "基本面分析（财务数据、估值水平、行业地位）"

        prompt = f"""你是一位专业的 A 股投资分析师。请对 {company_name}（{symbol}）进行{scope}。

**分析要求：**
1. 公司基本面：行业地位、竞争优势
2. 财务状况：营收、利润、现金流
3. 估值水平：PE、PB、PS 等指标对比
4. 技术面：价格趋势、关键支撑阻力位
5. 投资建议：明确给出买入/持有/卖出建议及理由

请提供详细的分析报告："""
        return prompt

    def build_etf_analysis_prompt(
        self,
        etf_code: str,
        etf_name: str
    ) -> str:
        """构建 ETF 分析提示词"""
        prompt = f"""你是一位专业的 ETF 投资分析师。请对 {etf_name}（{etf_code}）进行投资价值分析。

**分析维度：**
1. 跟踪标的：该 ETF 跟踪的指数及其特点
2. 行业前景：所覆盖行业的发展前景和政策环境
3. 规模流动性：ETF 规模、日均成交额
4. 持仓分析：前十大重仓股及权重
5. 估值水平：当前估值处于历史分位
6. 配置建议：适合的投资场景和时机

请提供详细的分析报告："""
        return prompt

    def build_convertible_analysis_prompt(
        self,
        cb_code: str,
        cb_name: str
    ) -> str:
        """构建可转债分析提示词"""
        prompt = f"""你是一位专业的可转债投资分析师。请对 {cb_name}（{cb_code}）进行投资价值分析。

**分析维度：**
1. 债底保护：转债价格、纯债价值、到期收益率
2. 股性弹性：转股溢价率、正股走势
3. 条款分析：强赎条款、下修条款、回售条款
4. 估值水平：转股溢价率、纯债溢价率、双低值
5. 正股分析：正股基本面和走势
6. 投资建议：当前价格的投资价值及风险

请提供详细的分析报告："""
        return prompt

    def _format_criteria(self, criteria: Dict[str, Any]) -> str:
        """格式化筛选条件"""
        lines = []
        for key, value in criteria.items():
            if isinstance(value, dict):
                if "min" in value:
                    lines.append(f"- {key.upper()} ≥ {value['min']}")
                if "max" in value:
                    lines.append(f"- {key.upper()} ≤ {value['max']}")
        return "\n".join(lines)
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_prompts.py -v
```

**Step 5: 提交**

```bash
git add core/agent/prompts.py tests/test_prompts.py
git commit -m "feat: add prompt engineering module"
```

---

## 阶段二：核心分析功能

### Task 5: 选股筛选模块

**文件：**
- Create: `analysis/screening.py`
- Test: `tests/test_screening.py`

**Step 1: 编写测试 - 选股功能**

```python
# tests/test_screening.py
import pytest
from analysis.screening import StockScreener
from core.agent.glm_agent import GLMAgent

def test_stock_screening():
    """测试选股功能"""
    agent = GLMAgent()
    screener = StockScreener(agent)

    criteria = {
        "pe": {"max": 30},
        "roe": {"min": 15}
    }

    result = screener.screen_stocks(criteria, top_n=5)

    assert result is not None
    assert "stocks" in result
    assert "reasoning" in result
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_screening.py -v
```

**Step 3: 实现选股筛选器**

```python
# analysis/screening.py
from typing import Dict, List, Any, Optional
from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher
import json

class StockScreener:
    """股票筛选器"""

    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def screen_stocks(
        self,
        criteria: Dict[str, Any],
        top_n: int = 10
    ) -> Optional[Dict]:
        """执行股票筛选

        Args:
            criteria: 筛选条件
            top_n: 返回前 N 只股票

        Returns:
            {
                "stocks": [{"code": "600519", "name": "贵州茅台", "reason": "..."}],
                "reasoning": "AI 的分析思路"
            }
        """
        # 构建提示词
        prompt = self.prompt_builder.build_stock_screening_prompt(
            criteria=criteria,
            stock_count=top_n
        )

        # 调用 AI 分析
        response = self.agent.chat(prompt)

        if not response:
            return None

        # 解析 AI 返回结果
        stocks = self._parse_stocks_from_response(response)

        return {
            "stocks": stocks,
            "reasoning": response,
            "criteria": criteria
        }

    def _parse_stocks_from_response(self, response: str) -> List[Dict]:
        """从 AI 响应中解析股票列表"""
        stocks = []
        lines = response.split('\n')

        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    stocks.append({
                        "code": parts[0],
                        "name": parts[1],
                        "reason": parts[2] if len(parts) > 2 else ""
                    })

        return stocks
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_screening.py -v
```

**Step 5: 提交**

```bash
git add analysis/screening.py tests/test_screening.py
git commit -m "feat: add stock screening module"
```

---

### Task 6: 市场分析模块

**文件：**
- Create: `analysis/market_analysis.py`
- Test: `tests/test_market_analysis.py`

**Step 1: 编写测试**

```python
# tests/test_market_analysis.py
import pytest
from analysis.market_analysis import MarketAnalyzer
from core.agent.glm_agent import GLMAgent

def test_market_index_analysis():
    """测试大盘分析"""
    agent = GLMAgent()
    analyzer = MarketAnalyzer(agent)

    result = analyzer.analyze_index("000001", "2024-01-15")

    assert result is not None
    assert "analysis" in result

def test_market_sentiment_analysis():
    """测试市场情绪分析"""
    agent = GLMAgent()
    analyzer = MarketAnalyzer(agent)

    result = analyzer.analyze_sentiment()

    assert result is not None
    assert "sentiment" in result
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_market_analysis.py -v
```

**Step 3: 实现市场分析器**

```python
# analysis/market_analysis.py
from typing import Dict, Optional
from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher

class MarketAnalyzer:
    """市场分析器"""

    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_index(
        self,
        index_code: str,
        date: str
    ) -> Optional[Dict]:
        """分析大盘指数

        Args:
            index_code: 指数代码（如 000001 上证指数）
            date: 分析日期

        Returns:
            {"analysis": "分析报告内容", "summary": "要点总结"}
        """
        # 获取指数数据
        index_data = self.fetcher.get_stock_daily(index_code, date, date)

        # 构建提示词
        prompt = self.prompt_builder.build_market_analysis_prompt(
            index_code=index_code,
            date=date
        )

        # AI 分析
        response = self.agent.chat(prompt)

        if not response:
            return None

        return {
            "index_code": index_code,
            "date": date,
            "data": index_data,
            "analysis": response,
            "summary": self._extract_summary(response)
        }

    def analyze_sentiment(self) -> Optional[Dict]:
        """分析市场情绪"""
        # 获取市场涨跌数据
        # 这里简化处理，实际应调用 AKShare 获取涨跌统计

        prompt = """请分析当前 A 股市场的整体情绪状态，包括：
1. 市场热度
2. 投资者情绪（恐慌/贪婪）
3. 资金流向
4. 短期走势判断

请给出简要分析："""

        response = self.agent.chat(prompt)

        return {
            "sentiment": response,
            "timestamp": None
        }

    def _extract_summary(self, analysis: str) -> str:
        """提取分析摘要"""
        # 简化处理：返回前 200 字
        return analysis[:200] + "..."
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_market_analysis.py -v
```

**Step 5: 提交**

```bash
git add analysis/market_analysis.py tests/test_market_analysis.py
git commit -m "feat: add market analysis module"
```

---

### Task 7: ETF 分析模块

**文件：**
- Create: `analysis/etf_analysis.py`
- Test: `tests/test_etf_analysis.py`

**Step 1: 编写测试**

```python
# tests/test_etf_analysis.py
import pytest
from analysis.etf_analysis import ETFAnalyzer
from core.agent.glm_agent import GLMAgent

def test_etf_analysis():
    """测试 ETF 分析"""
    agent = GLMAgent()
    analyzer = ETFAnalyzer(agent)

    result = analyzer.analyze_etf("510300", "沪深300ETF")

    assert result is not None
    assert "analysis" in result
    assert "510300" in result.get("etf_code", "")
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_etf_analysis.py -v
```

**Step 3: 实现 ETF 分析器**

```python
# analysis/etf_analysis.py
from typing import Dict, Optional
from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher

class ETFAnalyzer:
    """ETF 分析器"""

    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_etf(
        self,
        etf_code: str,
        etf_name: str = None
    ) -> Optional[Dict]:
        """分析 ETF

        Args:
            etf_code: ETF 代码
            etf_name: ETF 名称（可选）

        Returns:
            {"etf_code": "...", "analysis": "...", "recommendation": "..."}
        """
        # 获取 ETF 数据
        etf_list = self.fetcher.get_etf_list()
        etf_info = next(
            (e for e in etf_list if e.get('代码') == etf_code),
            None
        )

        if not etf_info and not etf_name:
            return None

        name = etf_name or etf_info.get('名称', etf_code)

        # 构建提示词
        prompt = self.prompt_builder.build_etf_analysis_prompt(
            etf_code=etf_code,
            etf_name=name
        )

        # AI 分析
        response = self.agent.chat(prompt)

        if not response:
            return None

        return {
            "etf_code": etf_code,
            "etf_name": name,
            "info": etf_info,
            "analysis": response
        }

    def get_etf_list(self) -> list:
        """获取 ETF 列表"""
        return self.fetcher.get_etf_list()

    def recommend_etfs(
        self,
        category: str = "industry",
        top_n: int = 5
    ) -> Optional[Dict]:
        """推荐 ETF

        Args:
            category: 类别 (industry/theme/broad)
            top_n: 推荐数量
        """
        etf_list = self.get_etf_list()

        prompt = f"""请从以下 ETF 列表中，选出最值得投资的 {top_n} 只 {category} 类 ETF。

**筛选标准：**
1. 规模大（日均成交额高）
2. 跟踪误差小
3. 所跟踪指数前景好
4. 当前估值合理

请给出推荐理由和配置建议："""

        response = self.agent.chat(prompt)

        return {
            "category": category,
            "recommendations": response
        }
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_etf_analysis.py -v
```

**Step 5: 提交**

```bash
git add analysis/etf_analysis.py tests/test_etf_analysis.py
git commit -m "feat: add ETF analysis module"
```

---

### Task 8: 可转债分析模块

**文件：**
- Create: `analysis/convertible_analysis.py`
- Test: `tests/test_convertible_analysis.py`

**Step 1: 编写测试**

```python
# tests/test_convertible_analysis.py
import pytest
from analysis.convertible_analysis import ConvertibleBondAnalyzer
from core.agent.glm_agent import GLMAgent

def test_convertible_analysis():
    """测试可转债分析"""
    agent = GLMAgent()
    analyzer = ConvertibleBondAnalyzer(agent)

    result = analyzer.analyze_convertible("113050", "南银转债")

    assert result is not None
    assert "analysis" in result
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_convertible_analysis.py -v
```

**Step 3: 实现可转债分析器**

```python
# analysis/convertible_analysis.py
from typing import Dict, Optional, List
from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher

class ConvertibleBondAnalyzer:
    """可转债分析器"""

    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_convertible(
        self,
        cb_code: str,
        cb_name: str = None
    ) -> Optional[Dict]:
        """分析可转债

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称（可选）
        """
        cb_list = self.fetcher.get_convertible_list()
        cb_info = next(
            (c for c in cb_list if c.get('bond_code') == cb_code),
            None
        )

        name = cb_name or cb_info.get('bond_nm', cb_code)

        # 构建提示词
        prompt = self.prompt_builder.build_convertible_analysis_prompt(
            cb_code=cb_code,
            cb_name=name
        )

        response = self.agent.chat(prompt)

        if not response:
            return None

        return {
            "cb_code": cb_code,
            "cb_name": name,
            "info": cb_info,
            "analysis": response
        }

    def get_convertible_list(self) -> List[Dict]:
        """获取可转债列表"""
        return self.fetcher.get_convertible_list()

    def screen_double_low(
        self,
        max_price: float = 130,
        max_premium: float = 30,
        top_n: int = 10
    ) -> Optional[Dict]:
        """双低策略筛选

        Args:
            max_price: 最高转债价格
            max_premium: 最高转股溢价率（%）
            top_n: 返回数量
        """
        cb_list = self.get_convertible_list()

        prompt = f"""请从可转债市场中筛选出符合以下条件的 {top_n} 只可转债：

**双低策略条件：**
- 转债价格 ≤ {max_price} 元
- 转股溢价率 ≤ {max_premium}%

请分析每只转债的投资价值和风险，给出推荐顺序。"""

        response = self.agent.chat(prompt)

        return {
            "strategy": "double_low",
            "criteria": {"max_price": max_price, "max_premium": max_premium},
            "recommendations": response
        }
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_convertible_analysis.py -v
```

**Step 5: 提交**

```bash
git add analysis/convertible_analysis.py tests/test_convertible_analysis.py
git commit -m "feat: add convertible bond analysis module"
```

---

## 阶段三：Web 界面

### Task 9: Streamlit 仪表板

**文件：**
- Create: `ui/dashboard.py`
- Create: `ui/pages/stock_analysis.py`
- Create: `ui/pages/etf_analysis.py`
- Create: `ui/pages/convertible_analysis.py`

**Step 1: 创建主仪表板**

```python
# ui/dashboard.py
import streamlit as st
from core.agent.glm_agent import GLMAgent
from analysis.screening import StockScreener
from analysis.market_analysis import MarketAnalyzer
from analysis.etf_analysis import ETFAnalyzer
from analysis.convertible_analysis import ConvertibleBondAnalyzer

st.set_page_config(
    page_title="Money-Agent - A 股 AI 投研助手",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Money-Agent - A 股 AI 投研竞技场")

# 初始化 AI Agent
if "agent" not in st.session_state:
    st.session_state.agent = GLMAgent()

# 侧边栏导航
with st.sidebar:
    st.header("功能导航")
    page = st.radio(
        "选择功能",
        ["选股筛选", "市场分析", "ETF 分析", "可转债分析"]
    )

    st.divider()
    st.caption("基于 GLM-4.7 驱动")

# 根据选择显示不同页面
if page == "选股筛选":
    st.header("📊 AI 选股助手")

    with st.form("screening_form"):
        st.subheader("设置筛选条件")

        col1, col2 = st.columns(2)
        with col1:
            pe_max = st.number_input("PE 最高值", value=30, min_value=0)
            pb_max = st.number_input("PB 最高值", value=5, min_value=0)
        with col2:
            roe_min = st.number_input("ROE 最低值(%)", value=15, min_value=0)
            top_n = st.slider("推荐数量", 5, 20, 10)

        submitted = st.form_submit_button("开始筛选")

        if submitted:
            with st.spinner("AI 正在分析中..."):
                screener = StockScreener(st.session_state.agent)
                criteria = {
                    "pe": {"max": pe_max},
                    "pb": {"max": pb_max},
                    "roe": {"min": roe_min}
                }
                result = screener.screen_stocks(criteria, top_n=top_n)

                if result:
                    st.success("筛选完成！")

                    st.subheader("AI 分析思路")
                    st.write(result["reasoning"])

                    st.subheader(f"推荐股票（前 {len(result['stocks'])} 只）")
                    for stock in result["stocks"]:
                        st.info(f"**{stock['name']} ({stock['code']})** - {stock['reason']}")
                else:
                    st.error("筛选失败，请重试")

elif page == "市场分析":
    st.header("📈 市场分析")

    col1, col2 = st.columns(2)
    with col1:
        index_code = st.text_input("指数代码", value="000001")
    with col2:
        date = st.date_input("分析日期")

    if st.button("开始分析"):
        with st.spinner("AI 正在分析中..."):
            analyzer = MarketAnalyzer(st.session_state.agent)
            result = analyzer.analyze_index(index_code, str(date))

            if result:
                st.subheader("市场分析报告")
                st.write(result["analysis"])

elif page == "ETF 分析":
    st.header("🔆 ETF 分析")

    etf_code = st.text_input("ETF 代码", value="510300")

    if st.button("分析 ETF"):
        with st.spinner("AI 正在分析中..."):
            analyzer = ETFAnalyzer(st.session_state.agent)
            result = analyzer.analyze_etf(etf_code)

            if result:
                st.subheader(f"{result['etf_name']} 分析报告")
                st.write(result["analysis"])

elif page == "可转债分析":
    st.header("💰 可转债分析")

    cb_code = st.text_input("可转债代码", value="113050")

    if st.button("分析可转债"):
        with st.spinner("AI 正在分析中..."):
            analyzer = ConvertibleBondAnalyzer(st.session_state.agent)
            result = analyzer.analyze_convertible(cb_code)

            if result:
                st.subheader(f"{result['cb_name']} 分析报告")
                st.write(result["analysis"])
```

**Step 2: 创建启动脚本**

```bash
cat > run_ui.sh << 'EOF'
#!/bin/bash
streamlit run ui/dashboard.py
EOF
chmod +x run_ui.sh
```

**Step 3: 提交**

```bash
git add ui/ run_ui.sh
git commit -m "feat: add Streamlit dashboard"
```

---

## 最终检查

### Task 10: 集成测试与文档

**文件：**
- Create: `README.md`
- Update: `docs/plans/2026-01-27-money-agent-implementation.md`

**Step 1: 更新 README**

```markdown
# Money-Agent - A 股 AI 投研竞技场

基于 AI-Trader 框架，使用多 AI 模型进行 A 股（股票、ETF、可转债）投研分析的辅助平台。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 GLM API Key
```

### 3. 启动界面

```bash
bash run_ui.sh
```

### 4. 访问

打开浏览器访问 http://localhost:8501

## 功能

- 📊 **选股筛选**：AI 根据多维度条件筛选优质股票
- 📈 **市场分析**：深度分析大盘走势和市场情绪
- 🔆 **ETF 分析**：行业/主题/宽基 ETF 投资价值分析
- 💰 **可转债分析**：双低策略、条款博弈、债底股性分析

## 技术栈

- Python 3.10+
- GLM-4.7 (智谱 AI)
- AKShare (数据源)
- Streamlit (界面)
- LangChain (Agent 框架)
```

**Step 2: 运行所有测试**

```bash
pytest tests/ -v
```

**Step 3: 启动应用验证**

```bash
streamlit run ui/dashboard.py
```

**Step 4: 最终提交**

```bash
git add README.md
git commit -m "docs: update README with usage instructions"
```

---

## 总结

本实施计划包含 10 个主要任务，覆盖：

1. 环境搭建和配置管理
2. AKShare 数据获取
3. GLM-4.7 AI Agent 框架
4. 提示词工程模块
5. 选股筛选功能
6. 市场分析功能
7. ETF 分析功能
8. 可转债分析功能
9. Streamlit Web 界面
10. 集成测试和文档

每个任务都遵循 TDD 原则，先写测试再实现功能，确保代码质量。
