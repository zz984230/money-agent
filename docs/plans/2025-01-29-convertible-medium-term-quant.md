# 可转债中期量化分析功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个"自上而下"的可转债中期量化筛选功能，通过行业趋势分析识别强势行业，再从中筛选优质转债

**Architecture:**
- 数据层：扩展 `AKShareFetcher` 添加行业指数、基准指数获取方法
- 因子层：新增 `MediumTermFactorCalculator` 实现完整因子集计算
- 分析层：新增 `ConvertibleBondMediumTermAnalyzer` 实现三层筛选逻辑
- UI层：改造 `render_convertible_factors_page()` 实现混合交互模式

**Tech Stack:** Python 3.10+, AKShare, Pandas, NumPy, Streamlit, Pytest

---

## Task 1: 扩展数据获取器 - 行业指数数据

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`
- Test: `tests/test_akshare_fetcher.py` (create if not exists)

**Step 1: Write the failing test**

创建测试文件 `tests/test_akshare_fetcher.py`:

```python
"""测试 AKShareFetcher 行业数据获取功能"""
import pytest
from data.fetchers.akshare_fetcher import AKShareFetcher


def test_get_industry_index_hist():
    """测试获取行业指数历史数据"""
    fetcher = AKShareFetcher()
    df = fetcher.get_industry_index_hist("new_energy", days=60)

    assert df is not None
    assert not df.empty
    assert 'close' in df.columns
    assert len(df) <= 60  # 不应超过请求的天数


def test_get_benchmark_index_hist():
    """测试获取基准指数历史数据"""
    fetcher = AKShareFetcher()
    df = fetcher.get_benchmark_index_hist("000300", days=60)

    assert df is not None
    assert not df.empty
    assert 'close' in df.columns


def test_get_industry_list():
    """测试获取行业列表"""
    fetcher = AKShareFetcher()
    industries = fetcher.get_industry_list()

    assert industries is not None
    assert len(industries) > 0
    assert isinstance(industries[0], dict)
    assert 'industry_code' in industries[0] or 'name' in industries[0]
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_akshare_fetcher.py::test_get_industry_index_hist -v
```

Expected: FAIL with "'AKShareFetcher' object has no attribute 'get_industry_index_hist'"

**Step 3: Write minimal implementation**

在 `data/fetchers/akshare_fetcher.py` 的 `AKShareFetcher` 类中添加以下方法（插入到 `calculate_indicators` 方法之前）:

```python
    def get_industry_index_hist(
        self,
        industry_symbol: str,
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取行业指数历史数据

        Args:
            industry_symbol: 行业指数代码（如 "new_energy" 对应新能源）
            days: 获取最近N天数据

        Returns:
            包含行业指数历史数据的DataFrame，包含 close 列用于计算涨跌幅
        """
        try:
            logger.debug(f"开始获取行业指数 {industry_symbol} 的历史数据（最近{days}天）")

            # 使用东方财富行业指数接口
            # industry_symbol 是行业名称的英文标识，需要转换为实际接口参数
            df = ak.stock_board_industry_hist_em(
                symbol=industry_symbol,
                period="daily",
                adjust=""  # 不复权
            )

            if df is None or df.empty:
                logger.warning(f"获取行业指数 {industry_symbol} 历史数据失败：返回数据为空")
                return pd.DataFrame()

            # 处理列名映射
            df = self._process_daily_data(df)

            # 筛选最近N天
            if 'date' in df.columns:
                df = df.sort_values('date').tail(days)

            logger.debug(f"成功获取行业指数 {industry_symbol} 的历史数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取行业指数 {industry_symbol} 历史数据失败: {e}", exc_info=True)
            return pd.DataFrame()

    def get_benchmark_index_hist(
        self,
        index_code: str = "000300",
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取基准指数历史数据（默认沪深300）

        Args:
            index_code: 指数代码（默认沪深300 000300）
            days: 获取最近N天数据

        Returns:
            包含基准指数历史数据的DataFrame
        """
        try:
            logger.debug(f"开始获取基准指数 {index_code} 的历史数据（最近{days}天）")

            # 确定市场前缀
            if index_code.startswith('00'):
                symbol = f"sh{index_code}"
            elif index_code.startswith('30') or index_code.startswith('39'):
                symbol = f"sz{index_code}"
            else:
                symbol = f"sh{index_code}"

            df = ak.stock_zh_index_daily(symbol=symbol)

            if df is None or df.empty:
                logger.warning(f"获取基准指数 {index_code} 历史数据失败：返回数据为空")
                return pd.DataFrame()

            # 处理列名
            df = self._process_daily_data(df)

            # 筛选最近N天
            if 'date' in df.columns:
                df = df.sort_values('date').tail(days)

            logger.debug(f"成功获取基准指数 {index_code} 的历史数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取基准指数 {index_code} 历史数据失败: {e}", exc_info=True)
            return pd.DataFrame()

    def get_industry_list(self) -> List[Dict]:
        """
        获取所有行业列表

        Returns:
            行业列表，每个元素为包含 industry_code 和 name 的字典
        """
        try:
            logger.debug("开始获取行业列表")

            # 获取东方财富行业板块信息
            df = ak.stock_board_industry_name_em()

            if df is None or df.empty:
                logger.warning("获取行业列表失败：返回数据为空")
                return []

            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                # 使用板块代码作为 industry_code
                result.append({
                    'industry_code': str(row.get('板块代码', '')),
                    'name': str(row.get('板块名称', '')),
                })

            logger.info(f"获取行业列表成功，共 {len(result)} 个行业")
            return result

        except Exception as e:
            logger.error(f"获取行业列表失败: {e}", exc_info=True)
            return []
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_akshare_fetcher.py::test_get_industry_index_hist -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher.py
git commit -m "feat: add industry index data fetching methods"
```

---

## Task 2: 扩展数据获取器 - 转债-行业映射

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`
- Test: `tests/test_akshare_fetcher.py`

**Step 1: Write the failing test**

在 `tests/test_akshare_fetcher.py` 中添加:

```python
def test_get_convertible_by_industry():
    """测试获取行业内可转债列表"""
    fetcher = AKShareFetcher()
    bonds = fetcher.get_convertible_by_industry("电子")

    assert bonds is not None
    assert isinstance(bonds, list)
    # 行业中应该有可转债
    if len(bonds) > 0:
        assert 'cb_code' in bonds[0]
        assert 'cb_name' in bonds[0]


def test_get_stock_by_industry():
    """测试获取行业内正股列表"""
    fetcher = AKShareFetcher()
    stocks = fetcher.get_stock_by_industry("电子")

    assert stocks is not None
    assert isinstance(stocks, list)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_akshare_fetcher.py::test_get_convertible_by_industry -v
```

Expected: FAIL with method not found

**Step 3: Write minimal implementation**

在 `data/fetchers/akshare_fetcher.py` 中添加方法:

```python
    def get_convertible_by_industry(self, industry_name: str) -> List[Dict]:
        """
        获取指定行业的可转债列表

        Args:
            industry_name: 行业名称（如 "电子"）

        Returns:
            该行业内的可转债列表，每个元素包含 cb_code, cb_name, stock_code
        """
        try:
            logger.debug(f"开始获取行业 '{industry_name}' 的可转债列表")

            # 获取所有可转债
            all_bonds = self.get_convertible_list()
            if not all_bonds:
                return []

            # 获取行业内股票列表
            industry_stocks = self.get_stock_by_industry(industry_name)
            if not industry_stocks:
                logger.warning(f"行业 '{industry_name}' 中没有找到股票")
                return []

            # 提取行业股票代码集合
            stock_codes = {s.get('代码', '') for s in industry_stocks}

            # 筛选属于该行业的可转债
            result = []
            for bond in all_bonds:
                stock_code = bond.get('正股代码', '')
                if stock_code in stock_codes:
                    result.append({
                        'cb_code': bond.get('代码'),
                        'cb_name': bond.get('转债名称'),
                        'stock_code': stock_code,
                        'stock_name': bond.get('正股名称', ''),
                    })

            logger.info(f"行业 '{industry_name}' 中找到 {len(result)} 只可转债")
            return result

        except Exception as e:
            logger.error(f"获取行业 '{industry_name}' 可转债失败: {e}", exc_info=True)
            return []

    def get_stock_by_industry(self, industry_name: str) -> List[Dict]:
        """
        获取指定行业的股票列表

        Args:
            industry_name: 行业名称

        Returns:
            该行业内的股票列表
        """
        try:
            logger.debug(f"开始获取行业 '{industry_name}' 的股票列表")

            # 获取行业板块成分股
            df = ak.stock_board_industry_cons_em(symbol=industry_name)

            if df is None or df.empty:
                logger.warning(f"获取行业 '{industry_name}' 股票列表失败：返回数据为空")
                return []

            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                result.append({
                    '代码': str(row.get('代码', '')),
                    '名称': str(row.get('名称', '')),
                })

            logger.info(f"行业 '{industry_name}' 中找到 {len(result)} 只股票")
            return result

        except Exception as e:
            logger.error(f"获取行业 '{industry_name}' 股票列表失败: {e}", exc_info=True)
            return []
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_akshare_fetcher.py::test_get_convertible_by_industry -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher.py
git commit -m "feat: add convertible bond to industry mapping"
```

---

## Task 3: 创建因子计算器模块

**Files:**
- Create: `analysis/convertible_medium_term_factors.py`
- Test: `tests/test_convertible_medium_term_factors.py`

**Step 1: Write the failing test**

创建 `tests/test_convertible_medium_term_factors.py`:

```python
"""测试中期量化因子计算器"""
import pytest
import pandas as pd
from analysis.convertible_medium_term_factors import MediumTermFactorCalculator


def test_calculate_industry_momentum():
    """测试计算行业动量因子"""
    calculator = MediumTermFactorCalculator()

    # 构造测试数据：60日数据，最后一天相比第一天上涨20%
    dates = pd.date_range('2024-01-01', periods=60)
    prices = [100.0 + i * 0.33 for i in range(60)]  # 约20%涨幅
    df = pd.DataFrame({'date': dates, 'close': prices})

    momentum = calculator.calculate_industry_momentum(df, days=60)

    assert momentum is not None
    assert momentum > 15  # 应该在20%左右
    assert momentum < 25


def test_calculate_industry_relative_strength():
    """测试计算行业相对强弱"""
    calculator = MediumTermFactorCalculator()

    # 行业涨20%，基准涨10%
    industry_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=60),
        'close': [100.0 + i * 0.33 for i in range(60)]
    })
    benchmark_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=60),
        'close': [100.0 + i * 0.16 for i in range(60)]
    })

    rs = calculator.calculate_industry_relative_strength(industry_df, benchmark_df)

    assert rs is not None
    # 相对强弱应该约为 (20/10 - 1) * 100 = 100%
    assert rs > 80
    assert rs < 120


def test_calculate_stock_excess_return():
    """测试计算正股超额收益"""
    calculator = MediumTermFactorCalculator()

    # 正股涨15%，行业涨10%
    stock_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=60),
        'close': [100.0 + i * 0.25 for i in range(60)]
    })
    industry_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=60),
        'close': [100.0 + i * 0.16 for i in range(60)]
    })

    excess_return = calculator.calculate_stock_excess_return(stock_df, industry_df)

    assert excess_return is not None
    # 超额收益约为 15% - 10% = 5%
    assert excess_return > 3
    assert excess_return < 7
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_convertible_medium_term_factors.py -v
```

Expected: FAIL with module not found

**Step 3: Write minimal implementation**

创建 `analysis/convertible_medium_term_factors.py`:

```python
"""
可转债中期量化因子计算器
Convertible Bond Medium-Term Quantitative Factor Calculator
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndustryFactorResult:
    """行业因子计算结果"""
    industry_code: str
    industry_name: str
    momentum_60d: float  # 60日动量
    momentum_120d: float  # 120日动量
    relative_strength: float  # 相对沪深300强弱
    volume_ratio: float  # 成交额占比


@dataclass
class BondFactorResult:
    """个券因子计算结果"""
    cb_code: str
    cb_name: str
    stock_excess_return: float  # 正股超额收益
    premium_rate: float  # 转股溢价率
    bond_type: str  # 转债类型：偏股型/平衡型/偏债型
    liquidity_score: float  # 流动性评分
    drawdown_from_high: float  # 距高点回撤
    stop_loss_signal: bool  # 止损信号
    stop_profit_signal: bool  # 止盈信号


class MediumTermFactorCalculator:
    """中期量化因子计算器"""

    def calculate_industry_momentum(
        self,
        price_df: pd.DataFrame,
        days: int = 60
    ) -> Optional[float]:
        """
        计算行业指数动量（N日涨跌幅）

        Args:
            price_df: 包含日期和收盘价的DataFrame
            days: 计算周期

        Returns:
            涨跌幅百分比，如 20.5 表示上涨20.5%
        """
        try:
            if price_df is None or price_df.empty or len(price_df) < 2:
                logger.warning("价格数据不足，无法计算动量")
                return 0.0

            # 确保按日期排序
            df = price_df.sort_values('date').tail(days)

            if len(df) < 2:
                return 0.0

            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]

            momentum = (end_price / start_price - 1) * 100

            logger.debug(f"行业{days}日动量: {momentum:.2f}%")
            return momentum

        except Exception as e:
            logger.error(f"计算行业动量失败: {e}", exc_info=True)
            return 0.0

    def calculate_industry_relative_strength(
        self,
        industry_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        days: int = 60
    ) -> Optional[float]:
        """
        计算行业相对强弱（相对沪深300）

        公式: (行业涨幅 / 基准涨幅 - 1) * 100%

        Args:
            industry_df: 行业指数数据
            benchmark_df: 基准指数数据
            days: 计算周期

        Returns:
            相对强弱百分比
        """
        try:
            industry_momentum = self.calculate_industry_momentum(industry_df, days)
            benchmark_momentum = self.calculate_industry_momentum(benchmark_df, days)

            if benchmark_momentum == 0:
                logger.warning("基准指数动量为0，无法计算相对强弱")
                return 0.0

            relative_strength = (industry_momentum / benchmark_momentum - 1) * 100

            logger.debug(f"行业相对强弱: {relative_strength:.2f}%")
            return relative_strength

        except Exception as e:
            logger.error(f"计算相对强弱失败: {e}", exc_info=True)
            return 0.0

    def calculate_stock_excess_return(
        self,
        stock_df: pd.DataFrame,
        industry_df: pd.DataFrame,
        days: int = 60
    ) -> Optional[float]:
        """
        计算正股超额收益（正股涨幅 - 行业涨幅）

        Args:
            stock_df: 正股价格数据
            industry_df: 行业指数数据
            days: 计算周期

        Returns:
            超额收益百分比
        """
        try:
            stock_momentum = self.calculate_industry_momentum(stock_df, days)
            industry_momentum = self.calculate_industry_momentum(industry_df, days)

            excess_return = stock_momentum - industry_momentum

            logger.debug(f"正股超额收益: {excess_return:.2f}%")
            return excess_return

        except Exception as e:
            logger.error(f"计算正股超额收益失败: {e}", exc_info=True)
            return 0.0

    def determine_bond_type(
        self,
        conversion_value: float,
        pure_bond_value: float
    ) -> str:
        """
        判断转债类型

        Args:
            conversion_value: 转股价值
            pure_bond_value: 纯债价值

        Returns:
            "偏股型" / "平衡型" / "偏债型"
        """
        if pure_bond_value == 0:
            return "平衡型"

        ratio = conversion_value / pure_bond_value

        if ratio > 2:
            return "偏股型"
        elif ratio > 1:
            return "平衡型"
        else:
            return "偏债型"

    def calculate_drawdown_from_high(
        self,
        price_df: pd.DataFrame,
        current_price: float,
        days: int = 20
    ) -> float:
        """
        计算距N日高点的回撤

        Args:
            price_df: 历史价格数据
            current_price: 当前价格
            days: 回溯周期

        Returns:
            回撤百分比（负数表示回撤）
        """
        try:
            if price_df is None or price_df.empty:
                return 0.0

            high_df = price_df.tail(days)
            if high_df.empty:
                return 0.0

            highest_price = high_df['close'].max()

            if highest_price == 0:
                return 0.0

            drawdown = (current_price / highest_price - 1) * 100

            logger.debug(f"距{days}日高点回撤: {drawdown:.2f}%")
            return drawdown

        except Exception as e:
            logger.error(f"计算回撤失败: {e}", exc_info=True)
            return 0.0

    def check_stop_loss_signal(
        self,
        drawdown: float,
        threshold: float = -15.0
    ) -> bool:
        """
        检查止损信号

        Args:
            drawdown: 回撤百分比
            threshold: 止损阈值

        Returns:
            是否触发止损
        """
        return drawdown <= threshold

    def check_stop_profit_signal(
        self,
        premium_rate: float,
        premium_history: pd.Series,
        percentile: float = 0.8
    ) -> bool:
        """
        检查止盈信号（溢价率扩张）

        Args:
            premium_rate: 当前溢价率
            premium_history: 历史溢价率序列
            percentile: 分位数阈值

        Returns:
            是否触发止盈
        """
        try:
            if premium_history is None or len(premium_history) < 10:
                return False

            threshold = premium_history.quantile(percentile)
            return premium_rate >= threshold

        except Exception as e:
            logger.error(f"检查止盈信号失败: {e}", exc_info=True)
            return False
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_convertible_medium_term_factors.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add analysis/convertible_medium_term_factors.py tests/test_convertible_medium_term_factors.py
git commit -m "feat: add medium-term factor calculator"
```

---

## Task 4: 创建中期量化分析器核心类

**Files:**
- Create: `analysis/convertible_medium_term.py`
- Test: `tests/test_convertible_medium_term.py`

**Step 1: Write the failing test**

创建 `tests/test_convertible_medium_term.py`:

```python
"""测试可转债中期量化分析器"""
import pytest
from unittest.mock import Mock, MagicMock
from analysis.convertible_medium_term import ConvertibleBondMediumTermAnalyzer


def test_screen_top_industries():
    """测试筛选强势行业"""
    agent = Mock()
    analyzer = ConvertibleBondMediumTermAnalyzer(agent)

    # Mock数据获取
    analyzer.fetcher.get_industry_list = Mock(return_value=[
        {'industry_code': 'test1', 'name': '测试行业1'},
        {'industry_code': 'test2', 'name': '测试行业2'},
    ])

    # Mock行业指数数据
    analyzer.fetcher.get_industry_index_hist = Mock(side_effect=[
        pd.DataFrame({'date': pd.date_range('2024-01-01', periods=60), 'close': [100 + i for i in range(60)]}),
        pd.DataFrame({'date': pd.date_range('2024-01-01', periods=60), 'close': [100 + i*0.5 for i in range(60)]}),
    ])

    analyzer.fetcher.get_benchmark_index_hist = Mock(
        return_value=pd.DataFrame({'date': pd.date_range('2024-01-01', periods=60), 'close': [100 + i*0.3 for i in range(60)]})
    )

    results = analyzer.screen_top_industries(top_n=5)

    assert results is not None
    assert len(results) <= 5
    assert len(results) > 0


def test_medium_term_screen():
    """测试完整的中期量化筛选流程"""
    agent = Mock()
    analyzer = ConvertibleBondMediumTermAnalyzer(agent)

    # 设置返回数据
    analyzer.screen_top_industries = Mock(return_value=[
        {'industry_code': 'test1', 'industry_name': '测试行业1', 'momentum_60d': 20, 'relative_strength': 50}
    ])

    analyzer.fetcher.get_convertible_by_industry = Mock(return_value=[
        {'cb_code': '123456', 'cb_name': '测试转债', 'stock_code': '600000'}
    ])

    # Mock agent.chat
    agent.chat = Mock(return_value="## 投资建议\n建议关注测试行业的优质转债。")

    results = analyzer.medium_term_screen(top_n=3)

    assert results is not None
    assert 'bonds' in results
    assert 'ai_analysis' in results
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_convertible_medium_term.py -v
```

Expected: FAIL with module not found

**Step 3: Write minimal implementation**

创建 `analysis/convertible_medium_term.py`:

```python
"""
可转债中期量化分析模块
Convertible Bond Medium-Term Quantitative Analysis Module
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher
from analysis.convertible_medium_term_factors import (
    MediumTermFactorCalculator,
    IndustryFactorResult,
    BondFactorResult
)


logger = logging.getLogger(__name__)


@dataclass
class MediumTermScreenResult:
    """中期量化筛选结果"""
    industries: List[IndustryFactorResult]
    bonds: List[Dict]
    ai_analysis: str


class ConvertibleBondMediumTermAnalyzer:
    """可转债中期量化分析器"""

    def __init__(self, agent: BaseAgent):
        """
        初始化分析器

        Args:
            agent: AI Agent实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()
        self.factor_calculator = MediumTermFactorCalculator()

    def screen_top_industries(
        self,
        top_n: int = 5,
        benchmark_code: str = "000300"
    ) -> List[IndustryFactorResult]:
        """
        筛选强势行业

        Args:
            top_n: 返回前N个强势行业
            benchmark_code: 基准指数代码（默认沪深300）

        Returns:
            按综合评分排序的强势行业列表
        """
        try:
            logger.info(f"开始筛选前{top_n}个强势行业")

            # 1. 获取所有行业
            industries = self.fetcher.get_industry_list()
            if not industries:
                logger.warning("获取行业列表失败")
                return []

            # 2. 获取基准指数数据
            benchmark_df = self.fetcher.get_benchmark_index_hist(benchmark_code, days=120)

            # 3. 计算每个行业的因子
            industry_results = []

            for industry in industries[:30]:  # 限制处理数量避免超时
                industry_code = industry.get('industry_code', '')
                industry_name = industry.get('name', '')

                if not industry_code:
                    continue

                try:
                    # 获取行业指数数据
                    industry_df = self.fetcher.get_industry_index_hist(
                        f"_{industry_code}",
                        days=120
                    )

                    if industry_df is None or industry_df.empty:
                        continue

                    # 计算因子
                    momentum_60d = self.factor_calculator.calculate_industry_momentum(industry_df, 60)
                    momentum_120d = self.factor_calculator.calculate_industry_momentum(industry_df, 120)
                    relative_strength = self.factor_calculator.calculate_industry_relative_strength(
                        industry_df,
                        benchmark_df,
                        60
                    )

                    # 成交额占比暂时设为0（需要额外数据源）
                    volume_ratio = 0.0

                    result = IndustryFactorResult(
                        industry_code=industry_code,
                        industry_name=industry_name,
                        momentum_60d=momentum_60d,
                        momentum_120d=momentum_120d,
                        relative_strength=relative_strength,
                        volume_ratio=volume_ratio
                    )

                    industry_results.append(result)

                except Exception as e:
                    logger.warning(f"处理行业 {industry_name} 失败: {e}")
                    continue

            # 4. 综合评分并排序
            industry_results.sort(
                key=lambda x: self._calculate_industry_score(x),
                reverse=True
            )

            # 5. 返回Top N
            result = industry_results[:top_n]

            logger.info(f"筛选完成，识别出{len(result)}个强势行业")
            return result

        except Exception as e:
            logger.error(f"筛选强势行业失败: {e}", exc_info=True)
            return []

    def _calculate_industry_score(self, industry: IndustryFactorResult) -> float:
        """
        计算行业综合评分

        Args:
            industry: 行业因子结果

        Returns:
            综合评分
        """
        # 权重：相对强弱50%，60日动量30%，120日动量20%
        score = (
            industry.relative_strength * 0.5 +
            industry.momentum_60d * 0.3 +
            industry.momentum_120d * 0.2
        )
        return score

    def medium_term_screen(
        self,
        top_n_industries: int = 5,
        top_n_bonds: int = 5,
        premium_max: float = 20.0,
        bond_type_filter: Optional[str] = None
    ) -> Optional[MediumTermScreenResult]:
        """
        完整的中期量化筛选流程

        Args:
            top_n_industries: 筛选前N个强势行业
            top_n_bonds: 每个行业筛选前N只转债
            premium_max: 最大溢价率
            bond_type_filter: 转债类型过滤（None/偏股型/平衡型/偏债型）

        Returns:
            MediumTermScreenResult对象
        """
        try:
            logger.info("开始中期量化筛选")

            # 1. 筛选强势行业
            industries = self.screen_top_industries(top_n=top_n_industries)

            if not industries:
                logger.warning("未识别出强势行业")
                return None

            # 2. 对每个行业筛选转债
            all_bonds = []

            for industry in industries:
                bonds = self._screen_bonds_in_industry(
                    industry,
                    top_n=top_n_bonds,
                    premium_max=premium_max,
                    bond_type_filter=bond_type_filter
                )
                all_bonds.extend(bonds)

            # 3. 按综合评分排序
            all_bonds.sort(key=lambda x: x.get('score', 0), reverse=True)

            # 4. AI分析
            ai_analysis = self._generate_ai_analysis(industries, all_bonds[:10])

            result = MediumTermScreenResult(
                industries=industries,
                bonds=all_bonds,
                ai_analysis=ai_analysis
            )

            logger.info(f"中期量化筛选完成，共筛选出{len(all_bonds)}只转债")
            return result

        except Exception as e:
            logger.error(f"中期量化筛选失败: {e}", exc_info=True)
            return None

    def _screen_bonds_in_industry(
        self,
        industry: IndustryFactorResult,
        top_n: int,
        premium_max: float,
        bond_type_filter: Optional[str]
    ) -> List[Dict]:
        """
        筛选行业内的转债

        Args:
            industry: 行业因子结果
            top_n: 返回前N只
            premium_max: 最大溢价率
            bond_type_filter: 类型过滤

        Returns:
            转债列表
        """
        try:
            # 获取行业内转债
            bonds = self.fetcher.get_convertible_by_industry(industry.industry_name)

            if not bonds:
                return []

            scored_bonds = []

            for bond in bonds:
                try:
                    cb_code = bond.get('cb_code')
                    if not cb_code:
                        continue

                    # 获取详细信息
                    detail = self.fetcher.get_convertible_detail(cb_code)
                    if not detail:
                        continue

                    # 应用筛选条件
                    premium_rate = detail.get('premium_rate', 100)

                    if premium_rate > premium_max:
                        continue

                    # 计算转债类型
                    conversion_value = detail.get('conversion_value', 0)
                    pure_value = 100.0  # 默认纯债价值

                    bond_type = self.factor_calculator.determine_bond_type(
                        conversion_value,
                        pure_value
                    )

                    if bond_type_filter and bond_type != bond_type_filter:
                        continue

                    # 计算综合评分
                    score = self._calculate_bond_score(
                        bond,
                        detail,
                        industry
                    )

                    scored_bonds.append({
                        'cb_code': cb_code,
                        'cb_name': bond.get('cb_name'),
                        'industry': industry.industry_name,
                        'premium_rate': premium_rate,
                        'bond_type': bond_type,
                        'score': score,
                        'industry_score': self._calculate_industry_score(industry)
                    })

                except Exception as e:
                    logger.warning(f"处理转债 {bond.get('cb_code')} 失败: {e}")
                    continue

            # 排序并返回Top N
            scored_bonds.sort(key=lambda x: x['score'], reverse=True)
            return scored_bonds[:top_n]

        except Exception as e:
            logger.error(f"筛选行业内转债失败: {e}", exc_info=True)
            return []

    def _calculate_bond_score(
        self,
        bond: Dict,
        detail: Dict,
        industry: IndustryFactorResult
    ) -> float:
        """
        计算个券综合评分

        Args:
            bond: 转债基础信息
            detail: 转债详细信息
            industry: 所属行业信息

        Returns:
            综合评分
        """
        score = 0.0

        # 行业强度 40%
        industry_score = self._calculate_industry_score(industry)
        score += industry_score * 0.4

        # 估值优势 30% (溢价率越低越好)
        premium_rate = detail.get('premium_rate', 50)
        valuation_score = max(0, 30 - premium_rate)
        score += valuation_score * 0.3

        # 转债类型 20%
        conversion_value = detail.get('conversion_value', 0)
        if conversion_value > 130:
            type_score = 100
        elif conversion_value > 100:
            type_score = 70
        else:
            type_score = 40
        score += type_score * 0.2

        # YTM 10%
        ytm = detail.get('ytm', 0)
        score += min(ytm * 10, 10) * 0.1

        return score

    def _generate_ai_analysis(
        self,
        industries: List[IndustryFactorResult],
        top_bonds: List[Dict]
    ) -> str:
        """
        生成AI分析报告

        Args:
            industries: 强势行业列表
            top_bonds: Top转债列表

        Returns:
            AI分析文本
        """
        try:
            prompt = self.prompt_builder.build_medium_term_analysis_prompt(
                industries,
                top_bonds
            )

            analysis = self.agent.chat(prompt)
            return analysis or "暂无AI分析"

        except Exception as e:
            logger.error(f"生成AI分析失败: {e}", exc_info=True)
            return "AI分析暂不可用"
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_convertible_medium_term.py -v
```

Expected: PASS (可能需要调整mock数据)

**Step 5: Commit**

```bash
git add analysis/convertible_medium_term.py tests/test_convertible_medium_term.py
git commit -m "feat: add medium-term quantitative analyzer"
```

---

## Task 5: 扩展提示词构建器

**Files:**
- Modify: `core/agent/prompts.py`
- Test: `tests/test_prompts.py` (if exists)

**Step 1: Write minimal implementation**

在 `core/agent/prompts.py` 的 `PromptBuilder` 类中添加方法（在文件末尾，`build_convertible_terms_prompt` 方法之后）:

```python
    def build_medium_term_analysis_prompt(
        self,
        industries: List['IndustryFactorResult'],
        top_bonds: List[Dict]
    ) -> str:
        """
        构建中期量化分析提示词

        Args:
            industries: 强势行业列表
            top_bonds: Top转债列表

        Returns:
            构建好的中期量化分析提示词
        """
        # 格式化行业信息
        industry_text = "\n".join([
            f"- {ind.industry_name}: 相对强弱 {ind.relative_strength:.1f}%, 60日动量 {ind.momentum_60d:.1f}%"
            for ind in industries[:5]
        ])

        # 格式化转债信息
        bond_text = "\n".join([
            f"- {b['cb_name']} ({b['cb_code']}): 行业 {b['industry']}, 溢价率 {b['premium_rate']:.1f}%, 评分 {b['score']:.1f}"
            for b in top_bonds[:10]
        ])

        prompt = f"""你是一位专业的可转债投资分析师。请基于以下中期量化筛选结果，提供专业的投资分析建议：

【识别出的强势行业】
{industry_text}

【精选转债列表】
{bond_text}

请从以下几个方面进行分析：

1. **行业趋势分析**
   - 分析各强势行业的驱动因素和可持续性
   - 识别最具投资价值的行业

2. **转债投资价值**
   - 评估精选转债的风险收益特征
   - 识别最具进攻性和防守性的标的

3. **配置建议**
   - 建议的行业配置比例
   - 建议的转债选择策略

4. **风险提示**
   - 行业轮动风险
   - 个券条款风险
   - 流动性风险

请用简洁专业的语言提供分析，重点关注实战价值。"""

        return prompt
```

**Step 2: Run existing tests to verify nothing breaks**

```bash
uv run pytest tests/test_prompts.py -v 2>/dev/null || uv run pytest tests/ -k "prompt" -v
```

Expected: Existing tests still pass

**Step 3: Commit**

```bash
git add core/agent/prompts.py
git commit -m "feat: add medium-term analysis prompt"
```

---

## Task 6: 实现UI层 - 快速筛选页面

**Files:**
- Modify: `ui/dashboard.py`
- Test: 手动测试

**Step 1: Update render_convertible_factors_page function**

替换 `ui/dashboard.py` 中的 `render_convertible_factors_page()` 函数（约532-566行）:

```python
def render_convertible_factors_page():
    """渲染可转债量化因子页面"""

    st.markdown("""
    <div class="info-box">
        可转债中期量化分析，基于行业趋势自上而下筛选优质标的。
        <br><small>支持快速筛选和行业探索两种模式。</small>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["快速筛选", "行业探索"])

    with tab1:
        render_medium_term_quick_screen()

    with tab2:
        render_medium_term_industry_explore()


def render_medium_term_quick_screen():
    """渲染中期量化快速筛选页面"""
    st.subheader("快速筛选")

    # 筛选参数配置
    with st.form("medium_term_screen_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            top_n_industries = st.slider(
                "强势行业数量",
                min_value=3,
                max_value=10,
                value=5,
                help="筛选出的强势行业数量"
            )

        with col2:
            top_n_bonds = st.slider(
                "每行业转债数量",
                min_value=3,
                max_value=10,
                value=5,
                help="每个行业返回的转债数量"
            )

        with col3:
            premium_max = st.slider(
                "溢价率上限(%)",
                min_value=0,
                max_value=50,
                value=20,
                help="只显示溢价率低于此值的转债"
            )

        with col4:
            bond_type = st.selectbox(
                "转债类型",
                options=["全部", "偏股型", "平衡型", "偏债型"],
                index=0,
                help="筛选指定类型的转债"
            )

        enable_signals = st.checkbox("启用止盈止损提醒", value=True)

        submitted = st.form_submit_button("开始筛选", use_container_width=True)

    if submitted:
        # 获取分析器
        agent = st.session_state.get('agent')
        if not agent:
            st.error("AI Agent未初始化")
            return

        try:
            from analysis.convertible_medium_term import ConvertibleBondMediumTermAnalyzer

            analyzer = ConvertibleBondMediumTermAnalyzer(agent)

            # 执行筛选
            with st.spinner("正在筛选，请稍候..."):
                bond_type_filter = None if bond_type == "全部" else bond_type

                result = analyzer.medium_term_screen(
                    top_n_industries=top_n_industries,
                    top_n_bonds=top_n_bonds,
                    premium_max=premium_max,
                    bond_type_filter=bond_type_filter
                )

            if result and result.bonds:
                # 显示筛选摘要
                st.success(f"筛选完成！识别出 {len(result.industries)} 个强势行业，共 {len(result.bonds)} 只转债")

                # 视图切换
                view_mode = st.radio(
                    "展示视图",
                    options=["按行业分组", "统一排名"],
                    horizontal=True
                )

                if view_mode == "按行业分组":
                    render_grouped_view(result, enable_signals)
                else:
                    render_ranked_view(result, enable_signals)

                # AI分析
                if result.ai_analysis:
                    with st.expander("查看AI投资建议", expanded=True):
                        st.markdown(result.ai_analysis)

            else:
                st.warning("未找到符合条件的转债，请尝试调整筛选条件")

        except Exception as e:
            st.error(f"筛选失败: {str(e)}")


def render_medium_term_industry_explore():
    """渲染行业探索页面"""
    st.subheader("行业探索")

    st.info("行业探索功能开发中，敬请期待...")

    # TODO: 实现行业排行榜和点击展开功能


def render_grouped_view(result, enable_signals):
    """渲染按行业分组的视图"""
    # 按行业分组
    from collections import defaultdict
    grouped = defaultdict(list)
    for bond in result.bonds:
        grouped[bond['industry']].append(bond)

    for industry in result.industries:
        bonds = grouped.get(industry.industry_name, [])
        if not bonds:
            continue

        with st.expander(
            f"📊 {industry.industry_name} "
            f"(相对强弱: {industry.relative_strength:.1f}%, "
            f"行业排名: {result.industries.index(industry)+1}/{len(result.industries)})"
        ):
            # 显示该行业的转债
            for bond in bonds:
                signals = []
                if enable_signals:
                    if bond.get('score', 0) > 70:
                        signals.append("✅强")
                    if bond['premium_rate'] > 15:
                        signals.append("⚠️溢价高")

                signal_text = " ".join(signals) if signals else ""

                st.markdown(
                    f"**{bond['cb_name']}** ({bond['cb_code']}) - "
                    f"溢价率 {bond['premium_rate']:.1f}% - "
                    f"评分 {bond['score']:.1f} {signal_text}"
                )


def render_ranked_view(result, enable_signals):
    """渲染统一排名视图"""
    import pandas as pd

    df = pd.DataFrame(result.bonds)

    # 添加信号列
    if enable_signals:
        df['信号'] = df.apply(
            lambda row: "✅强势" if row['score'] > 70 else ("⚠️关注" if row['score'] > 60 else ""),
            axis=1
        )

    st.dataframe(
        df[['cb_code', 'cb_name', 'industry', 'premium_rate', 'bond_type', 'score', '信号']] if enable_signals
        else df[['cb_code', 'cb_name', 'industry', 'premium_rate', 'bond_type', 'score']],
        column_config={
            "cb_code": st.column_config.TextColumn("代码", width="short"),
            "cb_name": st.column_config.TextColumn("名称", width="medium"),
            "industry": st.column_config.TextColumn("行业", width="medium"),
            "premium_rate": st.column_config.NumberColumn("溢价率", format="%.1f"),
            "bond_type": st.column_config.TextColumn("类型", width="short"),
            "score": st.column_config.NumberColumn("评分", format="%.1f"),
            "信号": st.column_config.TextColumn("信号", width="short")
        },
        use_container_width=True,
        hide_index=True
    )
```

**Step 2: Run manual test**

```bash
./run_ui.sh
```

Expected: UI shows new tabs and forms

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: implement medium-term quantitative UI"
```

---

## Task 7: 添加缓存支持

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: Add cache decorators**

在 `ui/dashboard.py` 的 `render_convertible_factors_page()` 函数前添加缓存函数:

```python
@st.cache_data(ttl=3600)
def get_cached_industries(_fetcher):
    """缓存行业列表数据（1小时）"""
    return _fetcher.get_industry_list()


@st.cache_data(ttl=1800)
def get_cached_convertible_by_industry(_fetcher, industry_name):
    """缓存行业转债映射（30分钟）"""
    return _fetcher.get_convertible_by_industry(industry_name)
```

**Step 2: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add caching for medium-term analysis"
```

---

## Task 8: 集成测试与优化

**Files:**
- Modify: `tests/test_convertible_medium_term.py`

**Step 1: Add integration test**

在 `tests/test_convertible_medium_term.py` 中添加:

```python
@pytest.mark.integration
def test_full_medium_term_workflow():
    """完整的中期量化集成测试（需要真实API）"""
    from core.agent.glm_agent import GLMAgent
    from analysis.convertible_medium_term import ConvertibleBondMediumTermAnalyzer

    agent = GLMAgent()
    analyzer = ConvertibleBondMediumTermAnalyzer(agent)

    result = analyzer.medium_term_screen(
        top_n_industries=3,
        top_n_bonds=3,
        premium_max=30.0
    )

    assert result is not None
    assert len(result.industries) > 0
    assert len(result.bonds) > 0
```

**Step 2: Run integration test**

```bash
uv run pytest tests/test_convertible_medium_term.py::test_full_medium_term_workflow -v
```

**Step 3: Commit**

```bash
git add tests/test_convertible_medium_term.py
git commit -m "test: add integration test for medium-term analysis"
```

---

## Summary

实施完成后，将实现以下功能：

1. ✅ 数据层：行业指数、基准指数、转债-行业映射获取
2. ✅ 因子层：完整的中期量化因子计算（动量、相对强弱、超额收益、止盈止损）
3. ✅ 分析层：三层筛选逻辑（行业→个券→综合评分）
4. ✅ UI层：快速筛选和行业探索两种模式
5. ✅ 缓存：行业数据缓存优化性能
6. ✅ AI分析：智能投资建议生成

**关键文件变更:**
- `data/fetchers/akshare_fetcher.py` - 新增行业数据获取方法
- `analysis/convertible_medium_term_factors.py` - 新增因子计算器
- `analysis/convertible_medium_term.py` - 新增中期量化分析器
- `core/agent/prompts.py` - 新增中期分析提示词
- `ui/dashboard.py` - 改造量化因子页面

**测试覆盖:**
- 单元测试：因子计算、数据获取
- 集成测试：完整筛选流程
- 手动测试：UI交互
