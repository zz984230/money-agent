# ETF/LOF投机分析因子增强实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为ETF/LOF投机分析模块添加情绪指标、资金流指标、ETF/LOF特有因子和增强的技术指标，并优化AI提示词呈现方式

**Architecture:** 新增3个分析器组件（SentimentAnalyzer、MoneyFlowAnalyzer、ETFLOFSpecificAnalyzer），增强AKShareFetcher和PredictiveFactorAnalyzer，优化AI提示词结构

**Tech Stack:** Python 3.x, pandas, numpy, akshare, pytest

---

## Task 1: 创建factors目录结构

**Files:**
- Create: `analysis/factors/__init__.py`

**Step 1: 创建目录和__init__.py文件**

```bash
mkdir -p analysis/factors
```

创建文件 `analysis/factors/__init__.py`:

```python
"""
ETF/LOF因子分析模块

包含:
- SentimentAnalyzer: 市场情绪因子分析器
- MoneyFlowAnalyzer: 资金流因子分析器
- ETFLOFSpecificAnalyzer: ETF/LOF特有因子分析器
"""

from .sentiment_analyzer import SentimentAnalyzer
from .money_flow_analyzer import MoneyFlowAnalyzer
from .etf_lof_specific import ETFLOFSpecificAnalyzer

__all__ = [
    'SentimentAnalyzer',
    'MoneyFlowAnalyzer',
    'ETFLOFSpecificAnalyzer',
]
```

**Step 2: 运行测试验证模块导入**

```bash
cd D:/code/money-agent
uv run python -c "from analysis.factors import SentimentAnalyzer; print('Import successful')"
```

Expected: `Import successful`

**Step 3: 提交**

```bash
git add analysis/factors/__init__.py
git commit -m "feat: create factors module structure"
```

---

## Task 2: 实现SentimentAnalyzer基础结构

**Files:**
- Create: `analysis/factors/sentiment_analyzer.py`
- Test: `tests/test_factors/test_sentiment_analyzer.py`

**Step 1: 编写SentimentAnalyzer类的测试**

创建 `tests/test_factors/__init__.py`:

```python
"""测试因子分析模块"""
```

创建 `tests/test_factors/test_sentiment_analyzer.py`:

```python
"""SentimentAnalyzer测试"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from analysis.factors.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def mock_fetcher():
    """Mock AKShareFetcher"""
    fetcher = Mock()
    return fetcher


@pytest.fixture
def sentiment_analyzer(mock_fetcher):
    """SentimentAnalyzer fixture"""
    return SentimentAnalyzer(mock_fetcher)


def test_sentiment_analyzer_init(sentiment_analyzer, mock_fetcher):
    """测试初始化"""
    assert sentiment_analyzer.fetcher == mock_fetcher
    assert sentiment_analyzer._market_breadth_cache is None
    assert sentiment_analyzer._cache_time is None


def test_get_market_breadth_returns_valid_structure(sentiment_analyzer):
    """测试市场宽度返回正确结构"""
    # Mock数据
    mock_df = pd.DataFrame({
        '涨跌幅': [5.0, -3.0, 0.0, 2.5, -1.0, 4.0, -2.0]
    })
    sentiment_analyzer.fetcher.get_market_breadth_data = Mock(return_value=mock_df)

    result = sentiment_analyzer.get_market_breadth()

    assert 'up_count' in result
    assert 'down_count' in result
    assert 'flat_count' in result
    assert 'total' in result
    assert 'advance_decline_ratio' in result
    assert result['total'] == 7
    assert result['advance_decline_ratio'] == result['up_count'] / result['total']


def test_sentiment_score_in_valid_range(sentiment_analyzer):
    """测试情绪得分在0-100范围内"""
    # Mock市场宽度数据
    sentiment_analyzer.get_market_breadth = Mock(return_value={
        'up_count': 2500,
        'down_count': 1500,
        'flat_count': 200,
        'total': 4200,
        'advance_decline_ratio': 0.595
    })
    # Mock涨停数据
    sentiment_analyzer.get_limit_up_stats = Mock(return_value={
        'limit_up_count': 80,
        'limit_up_ratio': 0.019
    })

    score = sentiment_analyzer.calculate_sentiment_score()

    assert 0 <= score <= 100


@patch('analysis.factors.sentiment_analyzer.pd.date_range')
def test_calculate_sentiment_factors_dataframe_structure(mock_date_range, sentiment_analyzer):
    """测试情绪因子DataFrame结构"""
    mock_date_range.return_value = pd.date_range('2024-01-01', periods=100, freq='D')

    sentiment_analyzer.get_market_breadth = Mock(return_value={
        'up_count': 2500,
        'down_count': 1500,
        'flat_count': 200,
        'total': 4200,
        'advance_decline_ratio': 0.595
    })
    sentiment_analyzer.calculate_sentiment_score = Mock(return_value=60)

    df = pd.DataFrame({'close': [100] * 100})
    df.index = pd.date_range('2024-01-01', periods=100, freq='D')

    factors = sentiment_analyzer.calculate_sentiment_factors(df)

    assert 'market_breadth_ratio' in factors.columns
    assert 'market_sentiment_score' in factors.columns
    assert len(factors) == 100
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_factors/test_sentiment_analyzer.py -v
```

Expected: FAIL with "SentimentAnalyzer not defined"

**Step 3: 实现SentimentAnalyzer类**

创建 `analysis/factors/sentiment_analyzer.py`:

```python
"""
市场情绪因子分析器
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """市场情绪因子分析器

    提供市场宽度、涨停统计、情绪得分等情绪指标
    """

    CACHE_TTL = 300  # 缓存5分钟

    def __init__(self, fetcher):
        """初始化情绪分析器

        Args:
            fetcher: AKShareFetcher实例
        """
        self.fetcher = fetcher
        self._market_breadth_cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None

    def get_market_breadth(self) -> Dict[str, Any]:
        """获取市场宽度统计数据

        Returns:
            {
                'up_count': 上涨家数,
                'down_count': 下跌家数,
                'flat_count': 平盘家数,
                'total': 总家数,
                'advance_decline_ratio': 涨跌比
            }
        """
        # 检查缓存
        if self._is_cache_valid():
            return self._market_breadth_cache

        try:
            data = self.fetcher.get_market_breadth_data()

            if data is None or data.empty:
                logger.warning("市场宽度数据为空，返回默认值")
                return self._get_default_market_breadth()

            up_count = len(data[data['涨跌幅'] > 0])
            down_count = len(data[data['涨跌幅'] < 0])
            flat_count = len(data[data['涨跌幅'] == 0])
            total = len(data)

            result = {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'total': total,
                'advance_decline_ratio': up_count / total if total > 0 else 0.5
            }

            # 更新缓存
            self._market_breadth_cache = result
            self._cache_time = datetime.now()

            return result

        except Exception as e:
            logger.error(f"获取市场宽度失败: {e}")
            return self._get_default_market_breadth()

    def get_limit_up_stats(self) -> Dict[str, Any]:
        """获取涨停统计数据

        Returns:
            {
                'limit_up_count': 涨停家数,
                'limit_up_ratio': 涨停比例,
                'limit_down_count': 跌停家数,
                'limit_down_ratio': 跌停比例
            }
        """
        try:
            data = self.fetcher.get_limit_up_stats_data()

            if data is None or data.empty:
                return self._get_default_limit_up_stats()

            # 假设数据包含涨停和跌停统计
            result = {
                'limit_up_count': data.get('limit_up_count', 0),
                'limit_up_ratio': data.get('limit_up_count', 0) / data.get('total', 1),
                'limit_down_count': data.get('limit_down_count', 0),
                'limit_down_ratio': data.get('limit_down_count', 0) / data.get('total', 1)
            }

            return result

        except Exception as e:
            logger.error(f"获取涨停统计失败: {e}")
            return self._get_default_limit_up_stats()

    def calculate_sentiment_score(self) -> float:
        """计算综合情绪得分 (0-100)

        考虑因素：
        - 市场宽度 (0-40分)
        - 涨停比例 (0-30分)
        - 涨停vs跌停比率 (0-30分)

        Returns:
            0-100分，>70偏多，<30偏空
        """
        try:
            breadth = self.get_market_breadth()
            limit_stats = self.get_limit_up_stats()

            # 1. 市场宽度得分 (0-40分)
            # 涨跌比 > 0.7 得40分，< 0.3 得0分
            ad_ratio = breadth['advance_decline_ratio']
            breadth_score = min(40, max(0, (ad_ratio - 0.3) / 0.4 * 40))

            # 2. 涨停比例得分 (0-30分)
            # 涨停比例 > 3% 得30分，< 1% 得0分
            limit_up_ratio = limit_stats['limit_up_ratio']
            limit_score = min(30, max(0, (limit_up_ratio - 0.01) / 0.02 * 30))

            # 3. 涨跌停比率得分 (0-30分)
            # 涨停家数 / 跌停家数
            limit_up_count = max(1, limit_stats['limit_up_count'])
            limit_down_count = max(1, limit_stats['limit_down_count'])
            balance_ratio = limit_up_count / limit_down_count
            balance_score = min(30, max(0, (balance_ratio - 0.5) / 1.5 * 30))

            total_score = breadth_score + limit_score + balance_score

            return round(total_score, 2)

        except Exception as e:
            logger.error(f"计算情绪得分失败: {e}")
            return 50.0  # 返回中性得分

    def get_historical_sentiment(self, days: int = 30) -> pd.DataFrame:
        """获取历史情绪数据（用于计算百分位）

        注意：由于市场数据是实时的，这里返回模拟的历史百分位数据

        Args:
            days: 历史天数

        Returns:
            包含历史情绪得分的DataFrame
        """
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        # 返回基于当前得分的历史分布模拟
        current_score = self.calculate_sentiment_score()

        data = []
        for i in range(days):
            # 简单的随机波动模拟
            variation = np.random.randn() * 10
            score = max(0, min(100, current_score + variation))
            data.append({'date': dates[i], 'sentiment_score': score})

        return pd.DataFrame(data).set_index('date')

    def calculate_sentiment_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算情绪因子DataFrame

        Args:
            df: 价格数据DataFrame（用于对齐索引）

        Returns:
            因子DataFrame，包含：
            - market_breadth_ratio: 市场涨跌比
            - market_sentiment_score: 市场情绪得分
        """
        factors = pd.DataFrame(index=df.index)

        try:
            breadth = self.get_market_breadth()
            sentiment_score = self.calculate_sentiment_score()

            # 广播市场级别的指标到所有行
            factors['market_breadth_ratio'] = breadth['advance_decline_ratio']
            factors['market_sentiment_score'] = sentiment_score

        except Exception as e:
            logger.error(f"计算情绪因子失败: {e}")
            factors['market_breadth_ratio'] = 0.5
            factors['market_sentiment_score'] = 50.0

        return factors

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache_time is None:
            return False

        elapsed = (datetime.now() - self._cache_time).total_seconds()
        return elapsed < self.CACHE_TTL

    def _get_default_market_breadth(self) -> Dict[str, Any]:
        """获取默认市场宽度数据"""
        return {
            'up_count': 2000,
            'down_count': 2000,
            'flat_count': 200,
            'total': 4200,
            'advance_decline_ratio': 0.5
        }

    def _get_default_limit_up_stats(self) -> Dict[str, Any]:
        """获取默认涨停统计数据"""
        return {
            'limit_up_count': 30,
            'limit_up_ratio': 0.007,
            'limit_down_count': 20,
            'limit_down_ratio': 0.005
        }
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_factors/test_sentiment_analyzer.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add analysis/factors/sentiment_analyzer.py tests/test_factors/test_sentiment_analyzer.py
git commit -m "feat: implement SentimentAnalyzer with market breadth and sentiment score"
```

---

## Task 3: 增强AKShareFetcher添加市场宽度数据获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`

**Step 1: 添加测试验证新方法**

在 `tests/test_factors/test_sentiment_analyzer.py` 末尾添加:

```python
@patch('akshare.ak.stock_zh_a_spot_em')
def test_market_breadth_integration(mock_spot_em, sentiment_analyzer):
    """集成测试：真实AKShare接口调用"""
    # Mock返回数据
    mock_df = pd.DataFrame({
        '代码': ['000001', '000002', '600000'],
        '名称': ['平安银行', '万科A', '浦发银行'],
        '涨跌幅': [5.0, -3.0, 0.0]
    })
    mock_spot_em.return_value = mock_df

    sentiment_analyzer.fetcher.get_market_breadth_data = Mock(
        side_effect=lambda: mock_spot_em()
    )

    result = sentiment_analyzer.get_market_breadth()

    assert result['up_count'] == 1
    assert result['down_count'] == 1
    assert result['flat_count'] == 1
    assert result['total'] == 3
```

**Step 2: 运行测试**

```bash
uv run pytest tests/test_factors/test_sentiment_analyzer.py::test_market_breadth_integration -v
```

**Step 3: 在AKShareFetcher中添加市场宽度数据获取方法**

在 `data/fetchers/akshare_fetcher.py` 中添加以下方法（在类的末尾）:

```python
    def get_market_breadth_data(self) -> Optional[pd.DataFrame]:
        """获取市场宽度原始数据

        使用ak.stock_zh_a_spot_em()获取A股实时行情

        Returns:
            包含涨跌幅数据的DataFrame，失败返回None
        """
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                logger.info(f"获取市场宽度数据成功，共{len(df)}只股票")
            return df
        except Exception as e:
            logger.error(f"获取市场宽度数据失败: {e}")
            return None

    def get_limit_up_stats_data(self) -> Optional[Dict]:
        """获取涨停统计数据

        使用ak.stock_market_activity_legu()获取市场活动数据

        Returns:
            包含涨停统计的字典，失败返回None
        """
        try:
            df = ak.stock_market_activity_legu()
            if df is not None and not df.empty:
                # 解析返回的数据，提取涨停统计
                # 具体列名需要根据实际返回调整
                result = {
                    'limit_up_count': df.get('涨停家数', [0])[0] if '涨停家数' in df else 0,
                    'limit_down_count': df.get('跌停家数', [0])[0] if '跌停家数' in df else 0,
                    'total': df.get('总家数', [4000])[0] if '总家数' in df else 4000
                }
                logger.info(f"获取涨停统计成功: {result}")
                return result
            return None
        except Exception as e:
            logger.error(f"获取涨停统计失败: {e}")
            return None
```

**Step 4: 运行测试**

```bash
uv run pytest tests/test_factors/test_sentiment_analyzer.py -v
```

**Step 5: 提交**

```bash
git add data/fetchers/akshare_fetcher.py tests/test_factors/test_sentiment_analyzer.py
git commit -m "feat: add market breadth and limit-up stats data fetching to AKShareFetcher"
```

---

## Task 4: 实现MoneyFlowAnalyzer基础结构

**Files:**
- Create: `analysis/factors/money_flow_analyzer.py`
- Test: `tests/test_factors/test_money_flow_analyzer.py`

**Step 1: 编写MoneyFlowAnalyzer类的测试**

创建 `tests/test_factors/test_money_flow_analyzer.py`:

```python
"""MoneyFlowAnalyzer测试"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
from analysis.factors.money_flow_analyzer import MoneyFlowAnalyzer


@pytest.fixture
def mock_fetcher():
    """Mock AKShareFetcher"""
    return Mock()


@pytest.fixture
def flow_analyzer(mock_fetcher):
    """MoneyFlowAnalyzer fixture"""
    return MoneyFlowAnalyzer(mock_fetcher)


@pytest.fixture
def mock_fund_flow_data():
    """Mock资金流数据"""
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    return pd.DataFrame({
        'date': dates,
        '主力净流入-净额': [100000000, 150000000, 80000000, 200000000, 120000000,
                           -50000000, -80000000, 100000000, 150000000, 180000000,
                           200000000, 220000000, 190000000, 170000000, 150000000,
                           130000000, 110000000, 90000000, 70000000, 50000000],
        '主力净流入-净占比': [0.05, 0.08, 0.04, 0.10, 0.06,
                           -0.03, -0.04, 0.05, 0.08, 0.09,
                           0.10, 0.11, 0.095, 0.085, 0.075,
                           0.065, 0.055, 0.045, 0.035, 0.025],
        '大单净流入-净占比': [0.03, 0.05, 0.02, 0.07, 0.04,
                           -0.02, -0.03, 0.03, 0.05, 0.06,
                           0.07, 0.08, 0.065, 0.055, 0.045,
                           0.035, 0.025, 0.015, 0.005, -0.005]
    })


def test_money_flow_analyzer_init(flow_analyzer, mock_fetcher):
    """测试初始化"""
    assert flow_analyzer.fetcher == mock_fetcher


def test_get_individual_fund_flow_returns_dataframe(flow_analyzer, mock_fund_flow_data):
    """测试获取个股资金流返回DataFrame"""
    flow_analyzer.fetcher.get_individual_fund_flow_data = Mock(return_value=mock_fund_flow_data)

    result = flow_analyzer.get_individual_fund_flow('163415', 'sz')

    assert isinstance(result, pd.DataFrame)
    assert '主力净流入-净占比' in result.columns
    assert '大单净流入-净占比' in result.columns
    assert len(result) == 20


def test_calculate_capital_accumulation(flow_analyzer, mock_fund_flow_data):
    """测试资金累积计算"""
    # 累计主力净流入
    accumulation = flow_analyzer.calculate_capital_accumulation(mock_fund_flow_data)

    assert isinstance(accumulation, pd.Series)
    assert len(accumulation) == len(mock_fund_flow_data)
    # 最后一个值应该是累计值
    assert accumulation.iloc[-1] > accumulation.iloc[0]


def test_calculate_order_momentum(flow_analyzer, mock_fund_flow_data):
    """测试大单动能计算"""
    momentum = flow_analyzer.calculate_order_momentum(mock_fund_flow_data, period=5)

    assert isinstance(momentum, pd.Series)
    # 由于用了5日变化率，前5个值应该是NaN
    assert momentum.iloc[:5].isna().any()
    # 后面的值应该有数值
    assert not momentum.iloc[5:].isna().all()


def test_calculate_money_flow_factors(flow_analyzer, mock_fund_flow_data):
    """测试资金流因子计算"""
    flow_analyzer.fetcher.get_individual_fund_flow_data = Mock(return_value=mock_fund_flow_data)

    df = pd.DataFrame({'close': [1.0] * 20})
    df.index = pd.date_range('2024-01-01', periods=20, freq='D')

    factors = flow_analyzer.calculate_money_flow_factors(df, '163415', 'sz')

    assert 'main_force_net_inflow_ratio' in factors.columns
    assert 'large_order_momentum' in factors.columns
    assert len(factors) == 20
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_factors/test_money_flow_analyzer.py -v
```

Expected: FAIL with "MoneyFlowAnalyzer not defined"

**Step 3: 实现MoneyFlowAnalyzer类**

创建 `analysis/factors/money_flow_analyzer.py`:

```python
"""
资金流因子分析器
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MoneyFlowAnalyzer:
    """资金流因子分析器

    提供主力净流入、大单动能等资金流指标
    """

    def __init__(self, fetcher):
        """初始化资金流分析器

        Args:
            fetcher: AKShareFetcher实例
        """
        self.fetcher = fetcher

    def get_individual_fund_flow(
        self, symbol: str, market: str = 'sz'
    ) -> Optional[pd.DataFrame]:
        """获取个股资金流数据

        Args:
            symbol: 基金代码
            market: 市场代码 ('sh', 'sz', 'bj')

        Returns:
            资金流数据DataFrame，失败返回None
        """
        try:
            data = self.fetcher.get_individual_fund_flow_data(symbol, market)
            if data is None or data.empty:
                logger.warning(f"{symbol} 资金流数据为空")
                return None
            return data
        except Exception as e:
            logger.error(f"获取{symbol}资金流数据失败: {e}")
            return None

    def calculate_capital_accumulation(
        self, flow_df: pd.DataFrame
    ) -> pd.Series:
        """计算资金累积程度

        累计主力净流入 / 当前流通市值
        这里简化为累计主力净流入的归一化值

        Args:
            flow_df: 资金流数据，必须包含'主力净流入-净额'列

        Returns:
            资金累积度序列
        """
        if '主力净流入-净额' not in flow_df.columns:
            logger.warning("资金流数据缺少'主力净流入-净额'列")
            return pd.Series([0] * len(flow_df), index=flow_df.index)

        # 累计主力净流入
        cumulative_flow = flow_df['主力净流入-净额'].cumsum()

        # 归一化到 -1 到 1 之间
        max_abs = cumulative_flow.abs().max()
        if max_abs > 0:
            normalized = cumulative_flow / max_abs
        else:
            normalized = cumulative_flow

        return normalized

    def calculate_order_momentum(
        self, flow_df: pd.DataFrame, period: int = 5
    ) -> pd.Series:
        """计算大单动能

        大单净流入占比的变化率

        Args:
            flow_df: 资金流数据，必须包含'大单净流入-净占比'列
            period: 周期，默认5日

        Returns:
            动能序列
        """
        if '大单净流入-净占比' not in flow_df.columns:
            logger.warning("资金流数据缺少'大单净流入-净占比'列")
            return pd.Series([0] * len(flow_df), index=flow_df.index)

        # 计算变化率
        momentum = flow_df['大单净流入-净占比'].diff(period)

        return momentum

    def get_northbound_flow(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """获取北向资金流向数据

        Args:
            symbol: 个股代码（可选，None表示全市场）

        Returns:
            北向资金数据DataFrame，失败返回None
        """
        try:
            data = self.fetcher.get_northbound_capital_data(symbol)
            if data is None or data.empty:
                logger.warning("北向资金数据为空")
                return None
            return data
        except Exception as e:
            logger.error(f"获取北向资金数据失败: {e}")
            return None

    def calculate_money_flow_factors(
        self, df: pd.DataFrame, symbol: str, market: str = 'sz'
    ) -> pd.DataFrame:
        """计算资金流因子DataFrame

        Args:
            df: 价格数据DataFrame（用于对齐索引）
            symbol: 基金代码
            market: 市场代码

        Returns:
            因子DataFrame，包含：
            - main_force_net_inflow_ratio: 主力净流入占比
            - large_order_momentum: 大单动能
            - capital_accumulation: 资金累积度
        """
        factors = pd.DataFrame(index=df.index)

        try:
            flow_data = self.get_individual_fund_flow(symbol, market)

            if flow_data is None:
                # 返回默认值
                factors['main_force_net_inflow_ratio'] = 0.0
                factors['large_order_momentum'] = 0.0
                factors['capital_accumulation'] = 0.0
                return factors

            # 获取最新的资金流数据并广播到所有行
            latest_ratio = flow_data['主力净流入-净占比'].iloc[-1]
            factors['main_force_net_inflow_ratio'] = latest_ratio

            # 计算大单动能
            momentum = self.calculate_order_momentum(flow_data)
            latest_momentum = momentum.iloc[-1] if not pd.isna(momentum.iloc[-1]) else 0.0
            factors['large_order_momentum'] = latest_momentum

            # 计算资金累积度
            accumulation = self.calculate_capital_accumulation(flow_data)
            latest_accumulation = accumulation.iloc[-1]
            factors['capital_accumulation'] = latest_accumulation

        except Exception as e:
            logger.error(f"计算资金流因子失败: {e}")
            factors['main_force_net_inflow_ratio'] = 0.0
            factors['large_order_momentum'] = 0.0
            factors['capital_accumulation'] = 0.0

        return factors
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_factors/test_money_flow_analyzer.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add analysis/factors/money_flow_analyzer.py tests/test_factors/test_money_flow_analyzer.py
git commit -m "feat: implement MoneyFlowAnalyzer with capital accumulation and order momentum"
```

---

## Task 5: 增强AKShareFetcher添加资金流数据获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`

**Step 1: 在AKShareFetcher中添加资金流数据获取方法**

在 `data/fetchers/akshare_fetcher.py` 中添加以下方法:

```python
    def get_individual_fund_flow_data(
        self, symbol: str, market: str = 'sz'
    ) -> Optional[pd.DataFrame]:
        """获取个股资金流数据

        使用ak.stock_individual_fund_flow()接口

        Args:
            symbol: 6位股票代码
            market: 市场代码 ('sh', 'sz', 'bj')

        Returns:
            包含主力净流入、大单数据的DataFrame，失败返回None
        """
        try:
            df = ak.stock_individual_fund_flow(symbol=symbol, market=market)
            if df is not None and not df.empty:
                logger.info(f"获取{symbol}资金流数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取{symbol}资金流数据失败: {e}")
            return None

    def get_northbound_capital_data(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """获取北向资金数据

        使用ak.stock_hsgt_individual_em()或stock_hsgt_hist_em()

        Args:
            symbol: 个股代码，None表示全市场

        Returns:
            北向资金持仓或流向DataFrame，失败返回None
        """
        try:
            if symbol:
                df = ak.stock_hsgt_individual_em(symbol=symbol)
            else:
                df = ak.stock_hsgt_hist_em(symbol="北向资金")

            if df is not None and not df.empty:
                logger.info(f"获取北向资金数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取北向资金数据失败: {e}")
            return None
```

**Step 2: 运行测试**

```bash
uv run pytest tests/test_factors/test_money_flow_analyzer.py -v
```

**Step 3: 提交**

```bash
git add data/fetchers/akshare_fetcher.py
git commit -m "feat: add fund flow and northbound capital data fetching to AKShareFetcher"
```

---

## Task 6: 实现ETFLOFSpecificAnalyzer

**Files:**
- Create: `analysis/factors/etf_lof_specific.py`
- Test: `tests/test_factors/test_etf_lof_specific.py`

**Step 1: 编写ETFLOFSpecificAnalyzer类的测试**

创建 `tests/test_factors/test_etf_lof_specific.py`:

```python
"""ETFLOFSpecificAnalyzer测试"""
import pytest
import pandas as pd
from unittest.mock import Mock
from analysis.factors.etf_lof_specific import ETFLOFSpecificAnalyzer


@pytest.fixture
def mock_fetcher():
    """Mock AKShareFetcher"""
    return Mock()


@pytest.fixture
def specific_analyzer(mock_fetcher):
    """ETFLOFSpecificAnalyzer fixture"""
    return ETFLOFSpecificAnalyzer(mock_fetcher)


def test_etf_lof_specific_analyzer_init(specific_analyzer, mock_fetcher):
    """测试初始化"""
    assert specific_analyzer.fetcher == mock_fetcher


def test_calc_premium_rate(specific_analyzer):
    """测试溢价率计算"""
    # 溢价率 = (市价 - 净值) / 净值
    price = 1.030
    nav = 1.000
    rate = specific_analyzer._calc_premium_rate(price, nav)

    assert abs(rate - 0.03) < 0.001


def test_calc_premium_rate_discount(specific_analyzer):
    """测试折价率计算"""
    price = 0.980
    nav = 1.000
    rate = specific_analyzer._calc_premium_rate(price, nav)

    assert abs(rate - (-0.02)) < 0.001


def test_calculate_arbitrage_space(specific_analyzer):
    """测试套利空间计算"""
    premium_rate = 0.035  # 3.5%溢价
    arbitrage_cost = 0.015  # 1.5%成本
    space = specific_analyzer.calculate_arbitrage_space(premium_rate, arbitrage_cost)

    assert abs(space - 0.02) < 0.001  # 2%空间


def test_calculate_arbitrage_space_negative(specific_analyzer):
    """测试负套利空间"""
    premium_rate = 0.01  # 1%溢价
    arbitrage_cost = 0.015  # 1.5%成本
    space = specific_analyzer.calculate_arbitrage_space(premium_rate, arbitrage_cost)

    # 空间应该是负数（无套利机会）
    assert space < 0


def test_calculate_liquidity_rank(specific_analyzer):
    """测试流动性排名计算"""
    all_funds = [
        {'code': '163415', 'name': '白银LOF', 'amount': 1000000},
        {'code': '161226', 'name': '白银基金', 'amount': 500000},
        {'code': '518880', 'name': '黄金ETF', 'amount': 2000000}
    ]

    rank = specific_analyzer.calculate_liquidity_rank('161226', all_funds)

    # 白银基金成交额排名第二
    assert rank == 2


def test_calculate_turnover_percentile(specific_analyzer):
    """测试换手率百分位计算"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'turnover_rate': np.random.rand(100) * 5  # 0-5%的换手率
    }, index=dates)

    percentile = specific_analyzer.calculate_turnover_percentile('163415', df)

    assert 0 <= percentile <= 1


def test_calculate_etf_lof_specific_factors(specific_analyzer):
    """测试ETF/LOF特有因子计算"""
    # Mock数据
    specific_analyzer.fetcher.get_etf_lof_nav = Mock(return_value=1.000)
    specific_analyzer.fetcher.get_etf_lof_realtime_quote = Mock(return_value={'price': 1.030, 'amount': 1000000})

    all_funds = [
        {'code': '163415', 'name': '白银LOF', 'amount': 1000000},
        {'code': '161226', 'name': '白银基金', 'amount': 500000}
    ]

    df = pd.DataFrame({'close': [1.0] * 100})
    df.index = pd.date_range('2024-01-01', periods=100, freq='D')

    factors = specific_analyzer.calculate_etf_lof_specific_factors(
        df, '163415', 'LOF', all_funds
    )

    assert 'premium_discount_rate' in factors.columns
    assert 'arbitrage_space' in factors.columns
    assert 'liquidity_rank' in factors.columns
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_factors/test_etf_lof_specific.py -v
```

Expected: FAIL with "ETFLOFSpecificAnalyzer not defined"

**Step 3: 实现ETFLOFSpecificAnalyzer类**

创建 `analysis/factors/etf_lof_specific.py`:

```python
"""
ETF/LOF特有因子分析器
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ETFLOFSpecificAnalyzer:
    """ETF/LOF特有因子分析器

    提供溢价率、套利空间、流动性排名等ETF/LOF特有指标
    """

    def __init__(self, fetcher):
        """初始化ETF/LOF特有因子分析器

        Args:
            fetcher: AKShareFetcher实例
        """
        self.fetcher = fetcher

    def _calc_premium_rate(self, price: float, nav: float) -> float:
        """计算溢价率/折价率

        Args:
            price: 市场价格
            nav: 净值

        Returns:
            溢价率（正数）或折价率（负数）
        """
        if nav == 0:
            return 0.0
        return (price - nav) / nav

    def get_premium_discount_rate(
        self, symbol: str, fund_type: str = 'LOF'
    ) -> Optional[float]:
        """获取溢价率/折价率

        Args:
            symbol: 基金代码
            fund_type: 基金类型 ('LOF' or 'ETF')

        Returns:
            溢价率（正数）或折价率（负数），失败返回None
        """
        try:
            nav = self.fetcher.get_etf_lof_nav(symbol)
            quote = self.fetcher.get_etf_lof_realtime_quote(symbol)

            if nav is None or quote is None:
                logger.warning(f"{symbol} 净值或行情数据为空")
                return None

            price = quote.get('price', nav)
            return self._calc_premium_rate(price, nav)

        except Exception as e:
            logger.error(f"获取{symbol}溢价率失败: {e}")
            return None

    def calculate_arbitrage_space(
        self,
        premium_rate: float,
        arbitrage_cost: float = 0.015
    ) -> float:
        """计算套利空间

        Args:
            premium_rate: 溢价率（正溢价或负折价）
            arbitrage_cost: 套利成本（默认1.5%）

        Returns:
            套利空间，>0表示有套利机会
        """
        # 对于溢价的情况，套利空间 = 溢价率 - 成本
        # 对于折价的情况，套利空间 = abs(折价率) - 成本
        return abs(premium_rate) - arbitrage_cost

    def get_price_nav_correlation(
        self, symbol: str, period: int = 20
    ) -> Optional[float]:
        """获取价格与净值相关系数

        Args:
            symbol: 基金代码
            period: 周期

        Returns:
            相关系数，失败返回None
        """
        try:
            # 需要获取历史价格和净值数据
            # 这里简化实现，返回默认值
            return 0.98
        except Exception as e:
            logger.error(f"计算{symbol}价格净值相关性失败: {e}")
            return None

    def calculate_liquidity_rank(
        self, symbol: str, all_funds: List[Dict]
    ) -> int:
        """计算流动性排名

        Args:
            symbol: 基金代码
            all_funds: 所有基金列表（必须包含'amount'键）

        Returns:
            排名（越小流动性越好），找不到返回999
        """
        try:
            # 按成交额降序排序
            sorted_funds = sorted(
                all_funds,
                key=lambda x: x.get('amount', 0),
                reverse=True
            )

            for i, fund in enumerate(sorted_funds):
                if fund.get('code') == symbol:
                    return i + 1

            return 999

        except Exception as e:
            logger.error(f"计算{symbol}流动性排名失败: {e}")
            return 999

    def calculate_turnover_percentile(
        self, symbol: str, historical_data: pd.DataFrame
    ) -> float:
        """计算换手率历史百分位

        Args:
            symbol: 基金代码
            historical_data: 历史数据（必须包含换手率列）

        Returns:
            百分位值 (0-1)，失败返回0.5
        """
        try:
            if 'turnover_rate' not in historical_data.columns:
                # 如果没有换手率数据，用成交额代替
                if 'amount' in historical_data.columns:
                    series = historical_data['amount']
                else:
                    return 0.5
            else:
                series = historical_data['turnover_rate']

            current_value = series.iloc[-1]
            percentile = (series < current_value).sum() / len(series)

            return round(percentile, 2)

        except Exception as e:
            logger.error(f"计算{symbol}换手率百分位失败: {e}")
            return 0.5

    def calculate_etf_lof_specific_factors(
        self, df: pd.DataFrame, symbol: str, fund_type: str = 'LOF',
        all_funds: List[Dict] = None
    ) -> pd.DataFrame:
        """计算ETF/LOF特有因子

        Args:
            df: 价格数据DataFrame（用于对齐索引）
            symbol: 基金代码
            fund_type: 基金类型
            all_funds: 所有基金列表

        Returns:
            因子DataFrame，包含：
            - premium_discount_rate: 溢价率/折价率
            - arbitrage_space: 套利空间
            - liquidity_rank: 流动性排名
        """
        factors = pd.DataFrame(index=df.index)

        try:
            # 获取溢价率
            premium_rate = self.get_premium_discount_rate(symbol, fund_type)
            if premium_rate is not None:
                factors['premium_discount_rate'] = premium_rate
                factors['arbitrage_space'] = self.calculate_arbitrage_space(premium_rate)
            else:
                factors['premium_discount_rate'] = 0.0
                factors['arbitrage_space'] = 0.0

            # 计算流动性排名
            if all_funds:
                liquidity_rank = self.calculate_liquidity_rank(symbol, all_funds)
                factors['liquidity_rank'] = liquidity_rank
            else:
                factors['liquidity_rank'] = 999

        except Exception as e:
            logger.error(f"计算ETF/LOF特有因子失败: {e}")
            factors['premium_discount_rate'] = 0.0
            factors['arbitrage_space'] = 0.0
            factors['liquidity_rank'] = 999

        return factors
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_factors/test_etf_lof_specific.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add analysis/factors/etf_lof_specific.py tests/test_factors/test_etf_lof_specific.py
git commit -m "feat: implement ETFLOFSpecificAnalyzer with premium rate and liquidity rank"
```

---

## Task 7: 增强AKShareFetcher添加ETF/LOF净值和实时行情获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`

**Step 1: 在AKShareFetcher中添加ETF/LOF相关方法**

在 `data/fetchers/akshare_fetcher.py` 中添加以下方法:

```python
    def get_etf_lof_nav(self, symbol: str) -> Optional[float]:
        """获取ETF/LOF净值

        Args:
            symbol: 基金代码

        Returns:
            最新净值，失败返回None
        """
        try:
            # 使用基金净值接口
            df = ak.fund_open_fund_info_em(symbol, indicator="单位净值")
            if df is not None and not df.empty:
                nav = df.iloc[-1]['单位净值']
                logger.info(f"获取{symbol}净值成功: {nav}")
                return float(nav)
            return None
        except Exception as e:
            logger.error(f"获取{symbol}净值失败: {e}")
            return None

    def get_etf_lof_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """获取ETF/LOF实时行情

        Args:
            symbol: 基金代码

        Returns:
            实时行情字典，包含price和amount，失败返回None
        """
        try:
            # 获取实时行情
            df = ak.fund_etf_spot_em()
            if df is not None and not df.empty:
                fund_data = df[df['代码'] == symbol]
                if not fund_data.empty:
                    result = {
                        'price': float(fund_data.iloc[0]['最新价']),
                        'amount': float(fund_data.iloc[0]['成交额']) if '成交额' in fund_data.columns else 0
                    }
                    logger.info(f"获取{symbol}实时行情成功: {result}")
                    return result
            return None
        except Exception as e:
            logger.error(f"获取{symbol}实时行情失败: {e}")
            return None
```

**Step 2: 运行测试**

```bash
uv run pytest tests/test_factors/test_etf_lof_specific.py -v
```

**Step 3: 提交**

```bash
git add data/fetchers/akshare_fetcher.py
git commit -m "feat: add ETF/LOF NAV and realtime quote fetching to AKShareFetcher"
```

---

## Task 8: 增强PredictiveFactorAnalyzer添加新因子

**Files:**
- Modify: `analysis/etf_lof_gamble.py`
- Test: `tests/test_etf_lof_gamble.py`

**Step 1: 编写增强因子计算的测试**

在 `tests/test_etf_lof_gamble.py` 末尾添加:

```python
def test_predictive_factor_analyzer_with_sentiment_factors():
    """测试情绪因子计算"""
    from unittest.mock import Mock
    from analysis.factors import SentimentAnalyzer

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # 创建情绪分析器
    mock_fetcher = Mock()
    sentiment_analyzer = SentimentAnalyzer(mock_fetcher)
    sentiment_analyzer.get_market_breadth = Mock(return_value={
        'up_count': 2500,
        'down_count': 1500,
        'flat_count': 200,
        'total': 4200,
        'advance_decline_ratio': 0.595
    })
    sentiment_analyzer.calculate_sentiment_score = Mock(return_value=60)

    analyzer.factor_analyzer.sentiment_analyzer = sentiment_analyzer

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': [100] * 100,
        'high': [102] * 100,
        'low': [98] * 100,
        'close': [100] * 100,
        'volume': [1000000] * 100
    }, index=dates)

    factors = analyzer.factor_analyzer.calculate_sentiment_factors(df)

    assert 'market_breadth_ratio' in factors.columns
    assert 'market_sentiment_score' in factors.columns
    assert factors['market_breadth_ratio'].iloc[0] == 0.595
    assert factors['market_sentiment_score'].iloc[0] == 60


def test_predictive_factor_analyzer_with_money_flow_factors():
    """测试资金流因子计算"""
    from analysis.factors import MoneyFlowAnalyzer

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # 创建资金流分析器
    mock_fetcher = Mock()
    money_flow_analyzer = MoneyFlowAnalyzer(mock_fetcher)

    # Mock资金流数据
    flow_df = pd.DataFrame({
        '主力净流入-净占比': [0.05] * 20,
        '大单净流入-净占比': [0.03] * 20
    })

    money_flow_analyzer.get_individual_fund_flow = Mock(return_value=flow_df)
    money_flow_analyzer.calculate_order_momentum = Mock(return_value=pd.Series([0.01] * 20))

    analyzer.factor_analyzer.money_flow_analyzer = money_flow_analyzer

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'close': [1.0] * 100,
        'volume': [1000000] * 100
    }, index=dates)

    factors = analyzer.factor_analyzer.calculate_money_flow_factors(df, '163415', 'sz')

    assert 'main_force_net_inflow_ratio' in factors.columns
    assert 'large_order_momentum' in factors.columns


def test_predictive_factor_analyzer_with_etf_lof_specific_factors():
    """测试ETF/LOF特有因子计算"""
    from analysis.factors import ETFLOFSpecificAnalyzer

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # 创建ETF/LOF特有分析器
    mock_fetcher = Mock()
    specific_analyzer = ETFLOFSpecificAnalyzer(mock_fetcher)
    specific_analyzer.get_premium_discount_rate = Mock(return_value=0.03)
    specific_analyzer.calculate_liquidity_rank = Mock(return_value=2)

    all_funds = [
        {'code': '163415', 'amount': 1000000},
        {'code': '161226', 'amount': 500000}
    ]

    analyzer.factor_analyzer.specific_analyzer = specific_analyzer

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({'close': [1.0] * 100}, index=dates)

    factors = analyzer.factor_analyzer.calculate_etf_lof_specific_factors(
        df, '163415', 'LOF', all_funds
    )

    assert 'premium_discount_rate' in factors.columns
    assert 'arbitrage_space' in factors.columns
    assert 'liquidity_rank' in factors.columns
```

**Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_predictive_factor_analyzer_with_sentiment_factors -v
```

Expected: FAIL (方法不存在)

**Step 3: 修改PredictiveFactorAnalyzer类添加新因子计算方法**

在 `analysis/etf_lof_gamble.py` 中修改 `PredictiveFactorAnalyzer` 类:

```python
class PredictiveFactorAnalyzer:
    """预测因子分析器（增强版）"""

    def __init__(
        self,
        sentiment_analyzer = None,
        money_flow_analyzer = None,
        specific_analyzer = None
    ):
        """初始化因子分析器

        Args:
            sentiment_analyzer: 情绪分析器
            money_flow_analyzer: 资金流分析器
            specific_analyzer: ETF/LOF特有因子分析器
        """
        self.factors = {}
        self.sentiment_analyzer = sentiment_analyzer
        self.money_flow_analyzer = money_flow_analyzer
        self.specific_analyzer = specific_analyzer

    def calculate_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术因子

        增强版：新增OBV、KDJ、CCI、Williams %R等指标

        Args:
            df: DataFrame，必须包含 close, high, low, volume 列

        Returns:
            因子DataFrame，索引与df相同
        """
        factors = pd.DataFrame(index=df.index)

        # === 现有因子 ===

        # 价格动量因子
        factors['momentum_5'] = df['close'].pct_change(5)
        factors['momentum_10'] = df['close'].pct_change(10)
        factors['momentum_20'] = df['close'].pct_change(20)

        # 波动率因子
        factors['volatility_20'] = df['close'].pct_change().rolling(20).std()

        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        factors['atr_14'] = true_range.rolling(14).mean()

        # 成交量因子
        if 'volume' in df.columns:
            factors['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            factors['volume_ma_5'] = df['volume'].rolling(5).mean() / df['volume'].rolling(20).mean()

        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        factors['rsi_14'] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        factors['macd'] = ema_12 - ema_26

        # 布林带带宽
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        upper_band = sma_20 + 2 * std_20
        lower_band = sma_20 - 2 * std_20
        factors['bollinger_bandwidth'] = (upper_band - lower_band) / sma_20

        # 价量背离
        price_change = df['close'].pct_change(5)
        if 'volume' in df.columns:
            volume_change = df['volume'].pct_change(5)
            factors['pv_divergence'] = price_change - volume_change
        else:
            factors['pv_divergence'] = price_change

        # === 新增技术指标 ===

        # OBV (On-Balance Volume)
        if 'volume' in df.columns:
            obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
            factors['obv'] = obv

        # KDJ (随机指标)
        low_9 = df['low'].rolling(9).min()
        high_9 = df['high'].rolling(9).max()
        rsv = (df['close'] - low_9) / (high_9 - low_9) * 100
        factors['kdj_k'] = rsv.ewm(com=2).mean()
        factors['kdj_d'] = factors['kdj_k'].ewm(com=2).mean()
        factors['kdj_j'] = 3 * factors['kdj_k'] - 2 * factors['kdj_d']

        # CCI (Commodity Channel Index)
        tp = (df['high'] + df['low'] + df['close']) / 3
        ma_tp = tp.rolling(20).mean()
        md = (tp - ma_tp).abs().rolling(20).mean()
        factors['cci'] = (tp - ma_tp) / (0.015 * md)

        # Williams %R
        high_14 = df['high'].rolling(14).max()
        low_14 = df['low'].rolling(14).min()
        factors['williams_r'] = -100 * (high_14 - df['close']) / (high_14 - low_14)

        return factors

    def calculate_sentiment_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算情绪因子

        Args:
            df: 价格数据DataFrame

        Returns:
            情绪因子DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        if self.sentiment_analyzer is not None:
            try:
                sentiment_factors = self.sentiment_analyzer.calculate_sentiment_factors(df)
                factors = pd.concat([factors, sentiment_factors], axis=1)
            except Exception as e:
                logger.error(f"计算情绪因子失败: {e}")
                factors['market_breadth_ratio'] = 0.5
                factors['market_sentiment_score'] = 50.0
        else:
            # 默认值
            factors['market_breadth_ratio'] = 0.5
            factors['market_sentiment_score'] = 50.0

        return factors

    def calculate_money_flow_factors(
        self, df: pd.DataFrame, symbol: str, market: str = 'sz'
    ) -> pd.DataFrame:
        """计算资金流因子

        Args:
            df: 价格数据DataFrame
            symbol: 基金代码
            market: 市场代码

        Returns:
            资金流因子DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        if self.money_flow_analyzer is not None:
            try:
                flow_factors = self.money_flow_analyzer.calculate_money_flow_factors(
                    df, symbol, market
                )
                factors = pd.concat([factors, flow_factors], axis=1)
            except Exception as e:
                logger.error(f"计算资金流因子失败: {e}")
                factors['main_force_net_inflow_ratio'] = 0.0
                factors['large_order_momentum'] = 0.0
                factors['capital_accumulation'] = 0.0
        else:
            # 默认值
            factors['main_force_net_inflow_ratio'] = 0.0
            factors['large_order_momentum'] = 0.0
            factors['capital_accumulation'] = 0.0

        return factors

    def calculate_etf_lof_specific_factors(
        self, df: pd.DataFrame, symbol: str, fund_type: str = 'LOF',
        all_funds: list = None
    ) -> pd.DataFrame:
        """计算ETF/LOF特有因子

        Args:
            df: 价格数据DataFrame
            symbol: 基金代码
            fund_type: 基金类型
            all_funds: 所有基金列表

        Returns:
            ETF/LOF特有因子DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        if self.specific_analyzer is not None:
            try:
                specific_factors = self.specific_analyzer.calculate_etf_lof_specific_factors(
                    df, symbol, fund_type, all_funds
                )
                factors = pd.concat([factors, specific_factors], axis=1)
            except Exception as e:
                logger.error(f"计算ETF/LOF特有因子失败: {e}")
                factors['premium_discount_rate'] = 0.0
                factors['arbitrage_space'] = 0.0
                factors['liquidity_rank'] = 999
        else:
            # 默认值
            factors['premium_discount_rate'] = 0.0
            factors['arbitrage_space'] = 0.0
            factors['liquidity_rank'] = 999

        return factors

    def calculate_all_factors(
        self, df: pd.DataFrame, symbol: str = None, fund_type: str = 'LOF',
        market: str = 'sz', all_funds: list = None
    ) -> pd.DataFrame:
        """计算所有因子

        Args:
            df: 历史数据DataFrame
            symbol: 基金代码
            fund_type: 基金类型
            market: 市场代码
            all_funds: 所有基金列表

        Returns:
            合并后的因子DataFrame
        """
        tech_factors = self.calculate_technical_factors(df)
        liq_factors = self.calculate_liquidity_factors(df)
        commodity_factors = self.calculate_commodity_specific_factors(df)

        # 新增因子
        sentiment_factors = self.calculate_sentiment_factors(df)
        money_flow_factors = self.calculate_money_flow_factors(df, symbol, market) if symbol else pd.DataFrame(index=df.index)
        etf_lof_factors = self.calculate_etf_lof_specific_factors(df, symbol, fund_type, all_funds) if symbol else pd.DataFrame(index=df.index)

        # 合并所有因子
        all_factors = pd.concat([
            tech_factors, liq_factors, commodity_factors,
            sentiment_factors, money_flow_factors, etf_lof_factors
        ], axis=1)

        return all_factors

    def calculate_liquidity_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算流动性因子（现有方法，保持不变）"""
        factors = pd.DataFrame(index=df.index)

        # 价差指标
        factors['spread_pct'] = (df['high'] - df['low']) / df['close']

        # 流动性冲击
        daily_return = df['close'].pct_change()
        if 'volume' in df.columns:
            factors['liquidity_impact'] = daily_return.abs() / (df['volume'] + 1e-6)
        else:
            factors['liquidity_impact'] = daily_return.abs()

        return factors

    def calculate_commodity_specific_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算大宗商品特有因子（现有方法，保持不变）"""
        factors = pd.DataFrame(index=df.index)

        # 价格趋势
        def trend_func(x):
            if len(x) < 2:
                return 0
            return 1 if x.iloc[-1] > x.iloc[0] else -1

        factors['price_trend'] = df['close'].rolling(20).apply(trend_func)

        # 波动聚集性
        returns = df['close'].pct_change()
        volatility_5 = returns.rolling(5).std()
        volatility_20 = returns.rolling(20).std()
        factors['vol_clustering'] = volatility_5 / (volatility_20 + 1e-6)

        return factors

    def build_prediction_model(
        self,
        factors: pd.DataFrame,
        target_events: list,
        lookback_days: int = 1
    ) -> tuple:
        """基于统计分析计算因子重要性（现有方法，保持不变）"""
        if len(factors) == 0 or len(target_events) == 0:
            return None, None

        # 创建标签：事件前lookback_days天标记为1
        labels = pd.Series(0, index=factors.index)
        for event_date in target_events:
            if event_date in factors.index:
                event_idx = factors.index.get_loc(event_date)
                if event_idx >= lookback_days:
                    pred_idx = event_idx - lookback_days
                    labels.iloc[pred_idx] = 1

        # 对齐数据
        aligned_data = pd.concat([factors, labels], axis=1)
        aligned_data.columns = list(factors.columns) + ['label']
        aligned_data = aligned_data.dropna()

        if len(aligned_data) == 0 or aligned_data['label'].sum() == 0:
            logger.warning("没有足够的正样本进行分析")
            return None, None

        # 基于统计的因子重要性分析
        feature_scores = {}

        for col in factors.columns:
            if col not in aligned_data.columns:
                continue

            # 1. 事件前后因子均值差异
            event_values = aligned_data[aligned_data['label'] == 1][col]
            normal_values = aligned_data[aligned_data['label'] == 0][col]

            if len(event_values) > 0 and len(normal_values) > 0:
                mean_diff = abs(event_values.mean() - normal_values.mean())
                std_ratio = mean_diff / (normal_values.std() + 1e-6)

                # 2. 因子波动率（事件前）
                volatility = event_values.std() if len(event_values) > 1 else 0

                # 3. 综合得分（标准化后相加）
                score = std_ratio * 0.7 + volatility * 0.3
                feature_scores[col] = score

        # 按得分排序
        feature_importance = pd.DataFrame({
            'feature': list(feature_scores.keys()),
            'importance': list(feature_scores.values())
        }).sort_values('importance', ascending=False)

        logger.info(f"统计因子分析完成，共{len(feature_importance)}个因子")
        return None, feature_importance
```

**Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_predictive_factor_analyzer_with_sentiment_factors -v
uv run pytest tests/test_etf_lof_gamble.py::test_predictive_factor_analyzer_with_money_flow_factors -v
uv run pytest tests/test_etf_lof_gamble.py::test_predictive_factor_analyzer_with_etf_lof_specific_factors -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: enhance PredictiveFactorAnalyzer with sentiment, money flow and ETF/LOF specific factors"
```

---

## Task 9: 优化AI提示词结构

**Files:**
- Modify: `core/agent/prompts.py`

**Step 1: 添加信号判断辅助函数和阈值配置**

在 `core/agent/prompts.py` 中添加（在 `PromptBuilder` 类中）:

```python
    # 信号阈值配置
    SIGNAL_THRESHOLDS = {
        'rsi': {'buy': 70, 'sell': 30},
        'macd': {'buy': 0, 'sell': 0},
        'momentum_5': {'buy': 0.03, 'sell': -0.02},
        'momentum_20': {'buy': 0.10, 'sell': -0.05},
        'main_force_ratio': {'buy': 0.05, 'sell': -0.05},
        'large_order_momentum': {'buy': 0.02, 'sell': -0.02},
        'market_breadth': {'buy': 0.6, 'sell': 0.4},
        'sentiment_score': {'buy': 70, 'sell': 30},
        'premium_rate': {'buy': -0.02, 'sell': 0.02},
        'arbitrage_space': {'buy': 0.01, 'sell': 0},
    }

    SIGNAL_INTERPRETATIONS = {
        'rsi': {
            'buy': '超买区域，可能回调',
            'neutral': '正常区间',
            'sell': '超卖区域，可能反弹'
        },
        'macd': {
            'buy': '金叉或零轴上方',
            'neutral': '零轴附近',
            'sell': '死叉或零轴下方'
        },
        'momentum_5': {
            'buy': '短期动量强势',
            'neutral': '短期动量中性',
            'sell': '短期动量弱势'
        },
        'market_breadth': {
            'buy': '市场宽度健康，多头占优',
            'neutral': '市场宽度中性',
            'sell': '市场宽度偏弱，空头占优'
        },
        'premium_rate': {
            'buy': '折价状态，具备安全边际',
            'neutral': '平价状态',
            'sell': '溢价状态，注意风险'
        },
    }

    def _get_signal(self, value: float, factor_name: str) -> tuple:
        """生成信号标记和解释

        Args:
            value: 当前值
            factor_name: 因子名称

        Returns:
            (signal_emoji, interpretation)
        """
        thresholds = self.SIGNAL_THRESHOLDS.get(factor_name, {})
        interpretations = self.SIGNAL_INTERPRETATIONS.get(factor_name, {})

        buy_threshold = thresholds.get('buy', 0)
        sell_threshold = thresholds.get('sell', 0)

        if value >= buy_threshold:
            return '🟢', interpretations.get('buy', '偏多')
        elif value <= sell_threshold:
            return '🔴', interpretations.get('sell', '偏空')
        else:
            return '⚪', interpretations.get('neutral', '中性')

    def _format_factor_value(self, value: float, factor_name: str) -> str:
        """格式化因子值

        Args:
            value: 因子值
            factor_name: 因子名称

        Returns:
            格式化后的字符串
        """
        if pd.isna(value):
            return 'N/A'

        # 根据因子类型格式化
        if factor_name in ['rsi', 'kdj_k', 'kdj_d', 'kdj_j', 'williams_r']:
            return f"{value:.1f}"
        elif factor_name in ['market_breadth_ratio', 'premium_discount_rate', 'arbitrage_space',
                            'main_force_net_inflow_ratio', 'large_order_momentum', 'capital_accumulation']:
            return f"{value*100:.2f}%"
        else:
            return f"{value:.4f}"

    def _build_factor_table(self, factors: dict, factor_names: list, category: str) -> str:
        """构建因子表格

        Args:
            factors: 因子字典
            factor_names: 要包含的因子名称列表
            category: 因子类别名称

        Returns:
            Markdown表格字符串
        """
        rows = []
        for name in factor_names:
            if name in factors:
                value = factors[name]
                signal, interpretation = self._get_signal(value, name)
                formatted_value = self._format_factor_value(value, name)
                rows.append(f"| {name} | {formatted_value} | {signal} | {interpretation} |")

        if rows:
            header = f"### {category}\n| 指标 | 当前值 | 信号 | 说明 |\n|------|--------|------|------|"
            return header + "\n" + "\n".join(rows)
        return ""
```

**Step 2: 替换build_etf_lof_gamble_prompt方法**

找到 `build_etf_lof_gamble_prompt` 方法并完全替换为:

```python
    def build_etf_lof_gamble_prompt(
        self,
        symbol: str,
        name: str,
        fund_type: str,
        abnormal_events: List[Dict],
        current_factors: Dict,
        feature_importance: pd.DataFrame,
        current_data: Dict
    ) -> str:
        """构建ETF/LOF投机分析的Prompt（增强版）

        Args:
            symbol: 基金代码
            name: 基金名称
            fund_type: 基金类型 (LOF/ETF)
            abnormal_events: 历史异常波动事件列表
            current_factors: 当前预测因子值字典
            feature_importance: 因子重要性DataFrame
            current_data: 当前行情数据字典

        Returns:
            完整的分析Prompt字符串
        """
        # 格式化异常事件（最近5个）
        recent_events = abnormal_events[-5:] if len(abnormal_events) > 5 else abnormal_events
        events_text = "\n".join([
            f"- {e['date'].strftime('%Y-%m-%d')}: "
            f"{e['return_pct']*100:.1f}% (波动率: {e['volatility']*100:.1f}%)"
            for e in recent_events
        ]) if recent_events else "无历史异常事件"

        # 构建因子表格
        factor_sections = []

        # 趋势类因子
        trend_factors = [
            'macd', 'rsi_14', 'kdj_k', 'kdj_d', 'cci'
        ]
        trend_table = self._build_factor_table(current_factors, trend_factors, "趋势类因子")
        if trend_table:
            factor_sections.append(trend_table)

        # 动量类因子
        momentum_factors = [
            'momentum_5', 'momentum_10', 'momentum_20', 'atr_14'
        ]
        momentum_table = self._build_factor_table(current_factors, momentum_factors, "动量类因子")
        if momentum_table:
            factor_sections.append(momentum_table)

        # 资金流因子
        money_flow_factors = [
            'main_force_net_inflow_ratio', 'large_order_momentum', 'capital_accumulation'
        ]
        money_flow_table = self._build_factor_table(current_factors, money_flow_factors, "资金流因子")
        if money_flow_table:
            factor_sections.append(money_flow_table)

        # 情绪指标
        sentiment_factors = [
            'market_breadth_ratio', 'market_sentiment_score'
        ]
        sentiment_table = self._build_factor_table(current_factors, sentiment_factors, "情绪指标")
        if sentiment_table:
            factor_sections.append(sentiment_table)

        # ETF/LOF特有因子
        etf_lof_factors = [
            'premium_discount_rate', 'arbitrage_space', 'liquidity_rank'
        ]
        etf_lof_table = self._build_factor_table(current_factors, etf_lof_factors, "ETF/LOF特有因子")
        if etf_lof_table:
            factor_sections.append(etf_lof_table)

        # 统计信号数量
        buy_signals = []
        neutral_signals = []
        sell_signals = []

        for factor_name, value in current_factors.items():
            if pd.isna(value):
                continue
            signal, _ = self._get_signal(value, factor_name)
            if signal == '🟢':
                buy_signals.append(factor_name)
            elif signal == '⚪':
                neutral_signals.append(factor_name)
            elif signal == '🔴':
                sell_signals.append(factor_name)

        # 格式化因子重要性
        if len(feature_importance) > 0:
            top_factors = feature_importance.head(10)
            importance_text = "\n".join([
                f"{i+1}. {row['feature']}: {row['importance']:.3f}"
                for i, (_, row) in enumerate(top_factors.iterrows())
            ])
        else:
            importance_text = "无因子重要性数据"

        prompt = f"""
你是一位专业的ETF/LOF短线交易分析师。请基于以下数据进行分析：

## 标的概况
- 代码: {symbol}
- 名称: {name}
- 类型: {fund_type}

## 当前行情
- 价格: {current_data.get('price', 'N/A')}
- 涨跌幅: {current_data.get('change_pct', 'N/A')}%
- 成交量: {current_data.get('volume', 'N/A')}
- 波动率(20日): {current_data.get('volatility_20d', 'N/A')}

## 技术指标分析

{chr(10).join(factor_sections)}

## 历史异常波动事件（最近5个）
{events_text}
总计发现 {len(abnormal_events)} 个异常波动事件

## 综合信号统计
- 🟢 **买入信号** ({len(buy_signals)}个): {', '.join(buy_signals[:5])}{'...' if len(buy_signals) > 5 else ''}
- ⚪ **中性信号** ({len(neutral_signals)}个): {', '.join(neutral_signals[:5])}{'...' if len(neutral_signals) > 5 else ''}
- 🔴 **卖出信号** ({len(sell_signals)}个): {', '.join(sell_signals[:5])}{'...' if len(sell_signals) > 5 else ''}

## 因子重要性排序（基于历史波动预测能力）
{importance_text}

## 分析要求

请按以下结构进行分析（使用Markdown格式）：

### 1. 关键因子深度解读

请重点分析以下因子，并给出明确判断：

**趋势判断**
- [ ] MACD处于什么状态？（金叉/死叉/零轴上方/零轴下方）
- [ ] RSI是否进入超买(>70)或超卖(<30)区域？
- [ ] 动量因子是否显示加速或减速？

**资金面**
- [ ] 主力资金是流入还是流出？趋势如何？
- [ ] 大单与散户行为是否背离？

**情绪面**
- [ ] 市场整体情绪是亢奋还是低迷？
- [ ] 涨停家数是否异常？
- [ ] 市场宽度是否健康？

**ETF/LOF特性**
- [ ] 当前溢价/折价程度如何？
- [ ] 是否存在套利机会？
- [ ] 价格与净值背离程度？

请给出每个因子的：当前值、历史位置、信号含义、操作建议

### 2. 历史规律
该标的异常波动的特点是什么？通常持续多久？
触发条件有哪些？

### 3. 时机判断
当前是否适合买入？请给出明确判断：
- ✅ **适合买入** - 因子显示即将出现异常波动
- ⏸️ **观望** - 信号不明确，建议继续观察
- ❌ **不适合买入** - 因子显示风险较高

### 4. 操作建议
如果判断适合买入，请给出：
- **买入点位**: 具体价格（基于当前价格{current_data.get('price', 'N/A')}给出）
- **止盈位**: 目标价格（给出1-2个）
- **止损位**: 风险控制价格
- **建议仓位**: 轻仓/中仓/重仓
- **持有周期**: 预计持有天数

如果不适合买入，请说明原因和后续关注点。

### 5. 风险提示
提示本次交易的主要风险点。
"""

        return prompt
```

**Step 3: 运行测试验证**

```bash
uv run pytest tests/test_etf_lof_gamble.py -k "prompt" -v
```

**Step 4: 提交**

```bash
git add core/agent/prompts.py
git commit -m "feat: enhance ETF/LOF gamble prompt with structured factors and signals"
```

---

## Task 10: 更新LOFETFGambleAnalyzer集成新因子

**Files:**
- Modify: `analysis/etf_lof_gamble.py`

**Step 1: 修改LOFETFGambleAnalyzer的__init__方法**

找到 `LOFETFGambleAnalyzer.__init__` 并修改:

```python
class LOFETFGambleAnalyzer:
    """ETF/LOF投机主分析器（增强版）"""

    def __init__(self, agent):
        """
        初始化分析器

        Args:
            agent: AI Agent实例
        """
        self.agent = agent
        from data.fetchers.akshare_fetcher import AKShareFetcher
        self.fetcher = AKShareFetcher()
        self.detector = VolatilityDetector()

        # 导入新的分析器
        from analysis.factors import (
            SentimentAnalyzer,
            MoneyFlowAnalyzer,
            ETFLOFSpecificAnalyzer
        )

        # 初始化因子分析器，传入新的子分析器
        self.factor_analyzer = PredictiveFactorAnalyzer(
            sentiment_analyzer=SentimentAnalyzer(self.fetcher),
            money_flow_analyzer=MoneyFlowAnalyzer(self.fetcher),
            specific_analyzer=ETFLOFSpecificAnalyzer(self.fetcher)
        )
```

**Step 2: 修改analyze_single方法使用新的因子计算**

找到 `analyze_single` 方法中的因子计算部分并修改:

```python
        # 3. 计算所有因子（增强版）
        all_factors = self.factor_analyzer.calculate_all_factors(
            df,
            symbol=symbol,
            fund_type=fund_type,
            market='sz' if symbol.startswith('1') or symbol.startswith('3') else 'sh'
        )
```

**Step 3: 运行测试验证**

```bash
uv run pytest tests/test_etf_lof_gamble.py -v
```

**Step 4: 提交**

```bash
git add analysis/etf_lof_gamble.py
git commit -m "feat: integrate new sentiment, money flow and ETF/LOF specific analyzers"
```

---

## Task 11: 运行全部测试验证

**Step 1: 运行所有因子测试**

```bash
uv run pytest tests/test_factors/ -v
```

Expected: 所有测试通过

**Step 2: 运行ETF/LOF投机分析测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py -v
```

Expected: 所有测试通过

**Step 3: 运行完整测试套件**

```bash
uv run pytest -v
```

Expected: 所有现有测试继续通过，新测试通过

**Step 4: 如果测试全部通过，无需提交（前面已提交）**

---

## Task 12: 添加集成测试验证AI分析质量

**Files:**
- Create: `tests/integration/test_etf_lof_gamble_integration.py`

**Step 1: 创建集成测试目录和文件**

```bash
mkdir -p tests/integration
touch tests/integration/__init__.py
```

创建 `tests/integration/test_etf_lof_gamble_integration.py`:

```python
"""ETF/LOF投机分析集成测试"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from core.agent.base_agent import BaseAgent
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer


@pytest.mark.integration
@pytest.mark.skip("需要真实API密钥")
def test_full_analysis_with_real_agent():
    """完整分析流程测试（需要真实API）"""
    from core.agent.glm_agent import GLMAgent

    agent = GLMAgent()
    analyzer = LOFETFGambleAnalyzer(agent)

    result = analyzer.analyze_single('163415', '白银LOF', 'LOF')

    assert result is not None
    assert result.ai_summary is not None
    assert len(result.ai_summary) > 100  # AI应该返回详细分析
    # 验证AI响应中包含了关键因子信息
    assert any(keyword in result.ai_summary for keyword in
               ['MACD', 'RSI', '资金流', '溢价', '市场宽度', '情绪'])


@pytest.mark.integration
def test_full_analysis_with_mock_agent():
    """完整分析流程测试（Mock AI响应）"""
    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="""
### 1. 关键因子深度解读

**趋势判断**
- MACD处于金叉状态，DIF>DEA，位于零轴上方，显示上涨趋势
- RSI为65.2，处于正常区间，未进入超买区域
- 动量因子显示短期加速

**资金面**
- 主力资金持续流入，流入占比5.2%
- 大单买入意愿强

**情绪面**
- 市场整体情绪偏多
- 市场宽度健康

**ETF/LOF特性**
- 当前溢价3.2%，需注意风险
- 套利空间有限

### 2. 历史规律
该标的异常波动通常持续2-3天，主要由大宗商品价格驱动

### 3. 时机判断
⏸️ **观望** - 信号不明确，建议继续观察

### 4. 操作建议
当前不适合买入，建议等待溢价缩小或技术信号更明确

### 5. 风险提示
主要风险：溢价回调、大宗商品价格波动
    """)

    # Mock数据获取
    mock_data = pd.DataFrame({
        'open': [1.0] * 100,
        'high': [1.02] * 100,
        'low': [0.98] * 100,
        'close': [1.0] * 100,
        'volume': [1000000] * 100
    })
    mock_data.index = pd.date_range('2024-01-01', periods=100, freq='D')

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # Mock fetcher
    with patch.object(analyzer.fetcher, 'get_lof_etf_history', return_value=mock_data):
        with patch.object(analyzer.fetcher, 'get_market_breadth_data', return_value=None):
            with patch.object(analyzer.fetcher, 'get_individual_fund_flow_data', return_value=None):
                with patch.object(analyzer.fetcher, 'get_etf_lof_nav', return_value=1.0):
                    with patch.object(analyzer.fetcher, 'get_etf_lof_realtime_quote', return_value={'price': 1.03, 'amount': 1000000}):
                        result = analyzer.analyze_single('163415', '白银LOF', 'LOF')

    assert result is not None
    assert result.symbol == '163415'
    assert result.name == '白银LOF'
    assert result.ai_summary is not None
    assert '观望' in result.ai_summary or '买入' in result.ai_summary or '卖出' in result.ai_summary


@pytest.mark.integration
def test_enhanced_factors_in_analysis():
    """测试增强的因子是否被包含在分析中"""
    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="AI分析响应")

    mock_data = pd.DataFrame({
        'open': [1.0] * 100,
        'high': [1.02] * 100,
        'low': [0.98] * 100,
        'close': [1.0] * 100,
        'volume': [1000000] * 100
    })
    mock_data.index = pd.date_range('2024-01-01', periods=100, freq='D')

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # Mock所有数据获取
    with patch.object(analyzer.fetcher, 'get_lof_etf_history', return_value=mock_data):
        with patch.object(analyzer.fetcher, 'get_market_breadth_data', return_value=None):
            with patch.object(analyzer.fetcher, 'get_individual_fund_flow_data', return_value=None):
                with patch.object(analyzer.fetcher, 'get_etf_lof_nav', return_value=1.0):
                    with patch.object(analyzer.fetcher, 'get_etf_lof_realtime_quote', return_value={'price': 1.03, 'amount': 1000000}):
                        result = analyzer.analyze_single('163415', '白银LOF', 'LOF')

    # 验证新因子存在
    assert 'market_breadth_ratio' in result.current_factors or 'premium_discount_rate' in result.current_factors

    # 验证AI被调用时使用了增强的prompt
    call_args = mock_agent.chat.call_args
    prompt = call_args[0][0] if call_args[0] else call_args[1].get('prompt', '')

    # 检查prompt中是否包含新增的因子类别
    factor_keywords = ['情绪指标', '资金流因子', 'ETF/LOF特有因子', '综合信号统计']
    has_enhanced_prompt = any(keyword in prompt for keyword in factor_keywords)

    assert has_enhanced_prompt, "Prompt应该包含增强的因子类别"
```

**Step 2: 运行集成测试**

```bash
uv run pytest tests/integration/test_etf_lof_gamble_integration.py -v
```

Expected: Mock测试通过，真实API测试被跳过

**Step 3: 提交**

```bash
git add tests/integration/
git commit -m "test: add integration tests for enhanced ETF/LOF gamble analysis"
```

---

## Task 13: 更新文档

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 在CLAUDE.md中添加新的因子分析模块说明**

在 `CLAUDE.md` 的 `Analysis Modules` 部分后面添加:

```markdown
### ETF/LOF投机分析增强因子

位于 `analysis/factors/` 目录

**新增的因子类别:**

1. **情绪指标** (`SentimentAnalyzer`)
   - `market_breadth_ratio`: 市场涨跌比
   - `market_sentiment_score`: 综合情绪得分 (0-100)
   - `limit_up_ratio`: 涨停比例

2. **资金流指标** (`MoneyFlowAnalyzer`)
   - `main_force_net_inflow_ratio`: 主力净流入占比
   - `large_order_momentum`: 大单动能
   - `capital_accumulation`: 资金累积度

3. **ETF/LOF特有因子** (`ETFLOFSpecificAnalyzer`)
   - `premium_discount_rate`: 溢价率/折价率
   - `arbitrage_space`: 套利空间
   - `liquidity_rank`: 流动性排名

4. **增强的技术指标** (`PredictiveFactorAnalyzer`)
   - `obv`: 能量潮
   - `kdj_k/d/j`: 随机指标
   - `cci`: 顺势指标
   - `williams_r`: 威廉指标
   - `force_index`: 强力指数
   - `money_flow_index`: 资金流量指数

**使用示例:**
```python
from core.agent.glm_agent import GLMAgent
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer

agent = GLMAgent()
analyzer = LOFETFGambleAnalyzer(agent)

# 分析单个标的（自动使用所有增强因子）
result = analyzer.analyze_single('163415', '白银LOF', 'LOF')

# 查看当前因子值
print(result.current_factors)

# 查看AI分析（包含结构化因子表格）
print(result.ai_summary)
```
```

**Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with enhanced ETF/LOF factor documentation"
```

---

## Task 14: 最终验证和清理

**Step 1: 运行完整测试套件**

```bash
uv run pytest -v --cov=analysis/factors --cov=analysis/etf_lof_gamble --cov-report=term-missing
```

Expected: 所有测试通过，覆盖率报告显示新增代码有良好覆盖

**Step 2: 代码格式检查**

```bash
uv run ruff check analysis/factors/ analysis/etf_lof_gamble.py core/agent/prompts.py
```

如果有格式问题，修复后:

```bash
uv run ruff check --fix analysis/factors/ analysis/etf_lof_gamble.py core/agent/prompts.py
```

**Step 3: 类型检查（如果有）**

```bash
uv run mypy analysis/factors/
```

**Step 4: 最终提交（如果有格式修复）**

```bash
git add -A
git commit -m "chore: code formatting and final cleanup"
```

---

## 实施完成检查清单

- [ ] Task 1: 创建factors目录结构
- [ ] Task 2: 实现SentimentAnalyzer基础结构
- [ ] Task 3: 增强AKShareFetcher添加市场宽度数据获取
- [ ] Task 4: 实现MoneyFlowAnalyzer基础结构
- [ ] Task 5: 增强AKShareFetcher添加资金流数据获取
- [ ] Task 6: 实现ETFLOFSpecificAnalyzer
- [ ] Task 7: 增强AKShareFetcher添加ETF/LOF净值和实时行情获取
- [ ] Task 8: 增强PredictiveFactorAnalyzer添加新因子
- [ ] Task 9: 优化AI提示词结构
- [ ] Task 10: 更新LOFETFGambleAnalyzer集成新因子
- [ ] Task 11: 运行全部测试验证
- [ ] Task 12: 添加集成测试验证AI分析质量
- [ ] Task 13: 更新文档
- [ ] Task 14: 最终验证和清理

---

## 注意事项

1. **数据可用性**: 如果AKShare API不稳定，分析器会返回默认值，确保分析不会中断
2. **性能考虑**: 市场级别数据有5分钟缓存，避免频繁请求
3. **测试策略**: 使用Mock数据隔离外部依赖，确保测试稳定性
4. **向后兼容**: 现有代码和测试继续工作，新功能是增量添加
