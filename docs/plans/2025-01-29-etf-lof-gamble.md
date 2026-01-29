# ETF/LOF投机异常波动筛选器实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个ETF/LOF异常波动检测系统，识别2-3天内的突增突降现象，计算预测因子，并通过AI提供买入时机、点位和止盈止损建议。

**架构:** 采用Analyzer模式，创建LOFETFGambleAnalyzer作为主分析器，集成VolatilityDetector（异常检测）、PredictiveFactorAnalyzer（因子计算）和AI Agent（智能分析）。数据通过AKShareFetcher扩展获取，UI通过Streamlit dashboard展示。

**Tech Stack:** Python 3.10+, AKShare, scikit-learn, Streamlit, GLM-4.7 (ModelScope Agent), pytest

---

## 前置准备

### Task 0: 安装依赖

**Files:**
- Modify: `pyproject.toml`

**Step 1: 添加scikit-learn依赖**

在`dependencies`部分添加：
```toml
dependencies = [
    # ... 现有依赖
    "scikit-learn>=1.3.0",
]
```

**Step 2: 安装依赖**

```bash
uv sync
```

**Step 3: 验证安装**

```bash
uv run python -c "import sklearn; print(sklearn.__version__)"
```
Expected: 输出版本号 >= 1.3.0

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add scikit-learn for prediction modeling"
```

---

## Phase 1: 数据获取扩展

### Task 1: 扩展AKShareFetcher - LOF/ETF列表获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`

**Step 1: 添加LOF/ETF列表获取方法**

在`AKShareFetcher`类中添加以下方法：

```python
def get_lof_list(self) -> pd.DataFrame:
    """
    获取所有LOF基金列表

    Returns:
        DataFrame with columns: code, name, fund_type
    """
    try:
        import akshare as ak
        df = ak.fund_em_fund_name()
        # 筛选LOF基金
        lof_df = df[df['基金类型'].str.contains('LOF', na=False)].copy()
        lof_df.columns = ['code', 'name', 'fund_type']
        return lof_df
    except Exception as e:
        logger.error(f"获取LOF列表失败: {e}")
        return pd.DataFrame(columns=['code', 'name', 'fund_type'])

def get_commodity_lof_list(self) -> list[dict]:
    """
    获取大宗商品LOF列表

    Returns:
        List of dict: [{'code': 'xxx', 'name': 'xxx', 'type': 'LOF'}]
    """
    try:
        lof_df = self.get_lof_list()
        commodity_keywords = ['商品', '黄金', '原油', '石油', '白银', '有色金属',
                              '能源', '农产品', '豆粕', '煤炭', '钢铁']

        commodity_lof = []
        for _, row in lof_df.iterrows():
            name = row['name']
            if any(keyword in name for keyword in commodity_keywords):
                commodity_lof.append({
                    'code': row['code'],
                    'name': name,
                    'type': 'LOF'
                })

        logger.info(f"找到{len(commodity_lof)}个大宗商品LOF")
        return commodity_lof
    except Exception as e:
        logger.error(f"获取大宗商品LOF列表失败: {e}")
        return []

def get_overseas_etf_list(self) -> list[dict]:
    """
    获取海外相关ETF列表

    Returns:
        List of dict: [{'code': 'xxx', 'name': 'xxx', 'type': 'ETF'}]
    """
    try:
        import akshare as ak
        # 获取ETF列表
        etf_df = ak.fund_etf_category_sina(symbol="ETF基金")

        overseas_keywords = ['美股', '港股', '德国', '日本', '美国', '纳斯达克',
                            '标普', '恒生', '欧洲', '亚太', '全球']

        overseas_etf = []
        for _, row in etf_df.iterrows():
            name = row.get('name', '')
            code = row.get('code', '')
            if any(keyword in name for keyword in overseas_keywords):
                overseas_etf.append({
                    'code': code,
                    'name': name,
                    'type': 'ETF'
                })

        logger.info(f"找到{len(overseas_etf)}个海外ETF")
        return overseas_etf
    except Exception as e:
        logger.error(f"获取海外ETF列表失败: {e}")
        return []
```

**Step 2: Commit**

```bash
git add data/fetchers/akshare_fetcher.py
git commit -m "feat: add LOF/ETF list fetching methods"
```

---

### Task 2: 扩展AKShareFetcher - 历史数据获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`

**Step 1: 添加LOF/ETF历史数据获取方法**

在`AKShareFetcher`类中添加：

```python
def get_lof_etf_history(self, symbol: str, period: int = 365) -> pd.DataFrame | None:
    """
    获取LOF/ETF历史行情数据

    Args:
        symbol: 基金代码
        period: 获取天数，默认365天

    Returns:
        DataFrame with columns: date, open, close, high, low, volume, amount
        or None if failed
    """
    from datetime import datetime, timedelta

    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')

    try:
        import akshare as ak

        # 尝试使用基金历史数据接口
        df = ak.fund_em_etf_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date
        )

        if df is not None and len(df) > 0:
            # 标准化列名
            df = df[['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']].copy()
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            # 确保数据类型正确
            for col in ['open', 'close', 'high', 'low']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

            logger.info(f"获取{symbol}历史数据成功，共{len(df)}条记录")
            return df

    except Exception as e:
        logger.error(f"获取{symbol}历史数据失败: {e}")

    # 备用方法：尝试sina数据源
    try:
        import akshare as ak
        df = ak.fund_etf_hist_sina(symbol=symbol)
        if df is not None and len(df) > 0:
            df.index = pd.to_datetime(df.index)
            # 重命名列以匹配标准格式
            column_mapping = {
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'volume': 'volume'
            }
            df = df.rename(columns=column_mapping)
            df = df[[col for col in column_mapping.values() if col in df.columns]]
            logger.info(f"通过备用接口获取{symbol}历史数据")
            return df
    except Exception as e:
        logger.error(f"备用接口也失败: {e}")

    return None
```

**Step 2: 编写测试**

创建文件：`tests/test_akshare_fetcher_extension.py`

```python
import pytest
from data.fetchers.akshare_fetcher import AKShareFetcher


@pytest.mark.integration
def test_get_lof_list():
    """测试获取LOF列表"""
    fetcher = AKShareFetcher()
    result = fetcher.get_lof_list()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert 'code' in result.columns
    assert 'name' in result.columns


@pytest.mark.integration
def test_get_commodity_lof_list():
    """测试获取大宗商品LOF列表"""
    fetcher = AKShareFetcher()
    result = fetcher.get_commodity_lof_list()

    assert isinstance(result, list)
    # 应该能找到一些大宗商品LOF
    assert len(result) >= 0
    if len(result) > 0:
        assert 'code' in result[0]
        assert 'name' in result[0]
        assert 'type' in result[0]


@pytest.mark.integration
def test_get_lof_etf_history():
    """测试获取LOF/ETF历史数据"""
    fetcher = AKShareFetcher()
    # 使用一个常见的LOF代码
    result = fetcher.get_lof_etf_history('163415', period=30)

    if result is not None:
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'close' in result.columns
        assert 'volume' in result.columns
    else:
        pytest.skip("无法获取测试数据")


def test_get_lof_etf_history_with_mock():
    """使用Mock测试历史数据获取"""
    from unittest.mock import Mock, patch
    import pandas as pd

    mock_data = pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02'],
        '开盘': [1.0, 1.1],
        '收盘': [1.05, 1.15],
        '最高': [1.1, 1.2],
        '最低': [0.95, 1.05],
        '成交量': [1000000, 1200000],
        '成交额': [1000000, 1380000]
    })

    with patch('akshare.fund_em_etf_hist', return_value=mock_data):
        fetcher = AKShareFetcher()
        result = fetcher.get_lof_etf_history('163415', period=30)

        assert result is not None
        assert len(result) == 2
        assert 'close' in result.columns
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_akshare_fetcher_extension.py::test_get_lof_etf_history_with_mock -v
```
Expected: PASS

**Step 4: 运行集成测试（可选）**

```bash
uv run pytest tests/test_akshare_fetcher_extension.py -v -m integration
```

**Step 5: Commit**

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher_extension.py
git commit -m "feat: add LOF/ETF history data fetching with tests"
```

---

## Phase 2: 异常波动检测

### Task 3: 创建VolatilityDetector类

**Files:**
- Create: `analysis/etf_lof_gamble.py`

**Step 1: 创建文件和VolatilityDetector类**

```python
"""
ETF/LOF投机异常波动分析模块

包含:
- VolatilityDetector: 异常波动检测
- PredictiveFactorAnalyzer: 预测因子计算
- LOFETFGambleAnalyzer: 主分析器
"""

import logging
import pandas as pd
import numpy as np
from typing import list, dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AbnormalEvent:
    """异常波动事件"""
    date: pd.Timestamp
    return: float
    start_price: float
    end_price: float
    volatility: float
    window: int


class VolatilityDetector:
    """异常波动检测器"""

    def __init__(self):
        self.events = []

    def detect_sudden_moves(
        self,
        price_series: pd.Series,
        window: int = 3,
        threshold: float = 0.15
    ) -> tuple[list[pd.Timestamp], list[dict]]:
        """
        检测突增突降

        Args:
            price_series: 价格序列，必须为pd.Series且有DatetimeIndex
            window: 观察窗口（天），默认3天
            threshold: 阈值，默认15%

        Returns:
            (abnormal_dates, abnormal_info)
            - abnormal_dates: 异常日期列表
            - abnormal_info: 异常事件详情列表
        """
        if len(price_series) < window + 1:
            return [], []

        # 计算累计收益率
        returns = price_series.pct_change(window)

        abnormal_dates = []
        abnormal_info = []

        for i in range(window, len(returns)):
            if pd.isna(returns.iloc[i]):
                continue

            if abs(returns.iloc[i]) > threshold:
                date = returns.index[i]
                start_price = price_series.iloc[i - window]
                end_price = price_series.iloc[i]
                change_pct = returns.iloc[i]

                # 计算波动率
                window_prices = price_series.iloc[i - window:i + 1]
                volatility = window_prices.std() / window_prices.mean()

                abnormal_dates.append(date)
                abnormal_info.append({
                    'date': date,
                    'return': change_pct,
                    'start_price': start_price,
                    'end_price': end_price,
                    'volatility': volatility,
                    'window': window
                })

        logger.info(f"检测到{len(abnormal_dates)}个异常波动事件（窗口={window}天，阈值={threshold*100}%）")
        return abnormal_dates, abnormal_info

    def multi_timeframe_analysis(self, price_series: pd.Series) -> dict:
        """
        多时间框架分析

        Args:
            price_series: 价格序列

        Returns:
            包含不同时间窗口和综合指标的结果字典
        """
        results = {}

        # 不同时间窗口检测
        for window in [2, 3, 5]:
            dates, info = self.detect_sudden_moves(
                price_series,
                window=window,
                threshold=0.1 if window == 2 else 0.15
            )
            results[f'window_{window}'] = {
                'dates': dates,
                'info': info,
                'count': len(dates)
            }

        # 计算综合波动指标
        returns = price_series.pct_change()
        results['metrics'] = {
            'max_1d_return': returns.max(),
            'min_1d_return': returns.min(),
            'volatility_20d': returns.rolling(20).std().mean() if len(returns) >= 20 else None,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        }

        return results
```

**Step 2: 编写测试**

在文件开头添加测试：

```python
# 在 tests/test_etf_lof_gamble.py 中

import pytest
import pandas as pd
import numpy as np
from analysis.etf_lof_gamble import VolatilityDetector


def test_detect_sudden_moves_no_abnormal():
    """测试无异常波动的情况"""
    detector = VolatilityDetector()

    # 创建稳定的价格序列（1%的日常波动）
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = pd.Series([100 + i * 0.01 + np.random.randn() * 0.5 for i in range(100)], index=dates)

    abnormal_dates, abnormal_info = detector.detect_sudden_moves(prices, window=3, threshold=0.15)

    assert len(abnormal_dates) == 0
    assert len(abnormal_info) == 0


def test_detect_sudden_moves_with_abnormal():
    """测试有异常波动的情况"""
    detector = VolatilityDetector()

    # 创建价格序列：在第10-12天有20%的涨幅
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    prices = []
    for i in range(50):
        if i < 10:
            prices.append(100.0)
        elif i < 13:
            # 3天内从100涨到120
            prices.append(100.0 + (i - 9) * 10.0)
        else:
            prices.append(120.0)

    price_series = pd.Series(prices, index=dates)

    abnormal_dates, abnormal_info = detector.detect_sudden_moves(price_series, window=3, threshold=0.15)

    # 应该检测到异常
    assert len(abnormal_dates) > 0
    assert len(abnormal_info) > 0

    # 检查异常事件的数据结构
    event = abnormal_info[0]
    assert 'date' in event
    assert 'return' in event
    assert 'volatility' in event
    assert abs(event['return']) > 0.15


def test_multi_timeframe_analysis():
    """测试多时间框架分析"""
    detector = VolatilityDetector()

    # 创建有波动的价格序列
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = pd.Series([100 + np.sin(i / 10) * 10 for i in range(100)], index=dates)

    results = detector.multi_timeframe_analysis(prices)

    # 检查结果结构
    assert 'window_2' in results
    assert 'window_3' in results
    assert 'window_5' in results
    assert 'metrics' in results

    # 检查metrics
    assert 'max_1d_return' in results['metrics']
    assert 'min_1d_return' in results['metrics']
    assert 'sharpe_ratio' in results['metrics']
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_detect_sudden_moves_no_abnormal -v
uv run pytest tests/test_etf_lof_gamble.py::test_detect_sudden_moves_with_abnormal -v
uv run pytest tests/test_etf_lof_gamble.py::test_multi_timeframe_analysis -v
```
Expected: All PASS

**Step 4: Commit**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add VolatilityDetector for abnormal move detection"
```

---

## Phase 3: 预测因子计算

### Task 4: 创建PredictiveFactorAnalyzer类 - 技术因子

**Files:**
- Modify: `analysis/etf_lof_gamble.py`

**Step 1: 添加PredictiveFactorAnalyzer类和技术因子计算**

```python
# 在 analysis/etf_lof_gamble.py 中添加

class PredictiveFactorAnalyzer:
    """预测因子分析器"""

    def __init__(self):
        self.factors = {}

    def calculate_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术因子

        Args:
            df: DataFrame，必须包含 close, high, low, volume 列

        Returns:
            因子DataFrame，索引与df相同
        """
        factors = pd.DataFrame(index=df.index)

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

        return factors
```

**Step 2: 编写测试**

```python
# 在 tests/test_etf_lof_gamble.py 中添加

def test_calculate_technical_factors():
    """测试技术因子计算"""
    from analysis.etf_lof_gamble import PredictiveFactorAnalyzer

    analyzer = PredictiveFactorAnalyzer()

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'close': [100 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'high': [102 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'low': [98 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'volume': [1000000 + np.random.randn() * 100000 for i in range(100)]
    }, index=dates)

    factors = analyzer.calculate_technical_factors(df)

    # 检查因子是否存在
    expected_factors = [
        'momentum_5', 'momentum_10', 'momentum_20',
        'volatility_20', 'atr_14', 'volume_ratio',
        'volume_ma_5', 'rsi_14', 'macd', 'bollinger_bandwidth',
        'pv_divergence'
    ]

    for factor in expected_factors:
        assert factor in factors.columns

    # 检查索引一致
    assert len(factors) == len(df)

    # 检查RSI范围（0-100）
    assert factors['rsi_14'].dropna().max() <= 100
    assert factors['rsi_14'].dropna().min() >= 0
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_calculate_technical_factors -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add technical factors calculation"
```

---

### Task 5: 完善PredictiveFactorAnalyzer - 流动性和商品因子

**Files:**
- Modify: `analysis/etf_lof_gamble.py`

**Step 1: 添加流动性和商品因子计算方法**

```python
# 在 PredictiveFactorAnalyzer 类中添加

    def calculate_liquidity_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算流动性因子

        Args:
            df: DataFrame，必须包含 close, high, low, volume 列

        Returns:
            因子DataFrame
        """
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
        """
        计算大宗商品特有因子

        Args:
            df: DataFrame，必须包含 close 列

        Returns:
            因子DataFrame
        """
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

    def calculate_all_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有因子

        Args:
            df: 历史数据DataFrame

        Returns:
            合并后的因子DataFrame
        """
        tech_factors = self.calculate_technical_factors(df)
        liq_factors = self.calculate_liquidity_factors(df)
        commodity_factors = self.calculate_commodity_specific_factors(df)

        # 合并所有因子
        all_factors = pd.concat([tech_factors, liq_factors, commodity_factors], axis=1)

        return all_factors
```

**Step 2: 编写测试**

```python
# 在 tests/test_etf_lof_gamble.py 中添加

def test_calculate_all_factors():
    """测试所有因子计算"""
    from analysis.etf_lof_gamble import PredictiveFactorAnalyzer

    analyzer = PredictiveFactorAnalyzer()

    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'close': [100 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'high': [102 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'low': [98 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'volume': [1000000 + np.random.randn() * 100000 for i in range(100)]
    }, index=dates)

    factors = analyzer.calculate_all_factors(df)

    # 检查是否有因子
    assert len(factors.columns) > 0

    # 检查一些关键因子
    assert 'momentum_5' in factors.columns
    assert 'spread_pct' in factors.columns
    assert 'price_trend' in factors.columns
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_calculate_all_factors -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add liquidity and commodity factors"
```

---

### Task 6: 添加预测模型构建方法

**Files:**
- Modify: `analysis/etf_lof_gamble.py`

**Step 1: 添加build_prediction_model方法**

```python
# 在 PredictiveFactorAnalyzer 类中添加

    def build_prediction_model(
        self,
        factors: pd.DataFrame,
        target_events: list[pd.Timestamp],
        lookback_days: int = 1
    ) -> tuple:
        """
        构建预测模型

        Args:
            factors: 因子DataFrame
            target_events: 突增突降事件日期列表
            lookback_days: 事件前观察天数

        Returns:
            (model, feature_importance) 或 (None, None)
        """
        if len(factors) == 0 or len(target_events) == 0:
            return None, None

        # 创建标签
        labels = pd.Series(0, index=factors.index)
        for event_date in target_events:
            if event_date in factors.index:
                # 找到事件前N天的索引
                event_idx = factors.index.get_loc(event_date)
                if event_idx >= lookback_days:
                    pred_idx = event_idx - lookback_days
                    labels.iloc[pred_idx] = 1

        # 对齐数据，删除NaN
        aligned_data = pd.concat([factors, labels], axis=1)
        aligned_data.columns = list(factors.columns) + ['label']
        aligned_data = aligned_data.dropna()

        if len(aligned_data) == 0 or aligned_data['label'].sum() == 0:
            logger.warning("没有足够的正样本构建模型")
            return None, None

        # 特征和标签
        X = aligned_data.iloc[:, :-1]
        y = aligned_data['label']

        # 检查正负样本比例
        pos_count = y.sum()
        neg_count = len(y) - pos_count
        logger.info(f"正样本: {pos_count}, 负样本: {neg_count}")

        try:
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestClassifier

            # 划分训练测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )

            # 训练模型
            clf = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            clf.fit(X_train, y_train)

            # 计算特征重要性
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': clf.feature_importances_
            }).sort_values('importance', ascending=False)

            # 记录模型性能
            train_score = clf.score(X_train, y_train)
            test_score = clf.score(X_test, y_test)
            logger.info(f"模型训练准确率: {train_score:.3f}, 测试准确率: {test_score:.3f}")

            return clf, feature_importance

        except Exception as e:
            logger.error(f"构建预测模型失败: {e}")
            return None, None
```

**Step 2: 编写测试**

```python
# 在 tests/test_etf_lof_gamble.py 中添加

def test_build_prediction_model():
    """测试预测模型构建"""
    from analysis.etf_lof_gamble import PredictiveFactorAnalyzer

    analyzer = PredictiveFactorAnalyzer()

    # 创建模拟因子数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    factors = pd.DataFrame({
        'factor1': np.random.randn(100),
        'factor2': np.random.randn(100),
        'factor3': np.random.randn(100),
    }, index=dates)

    # 创建一些目标事件
    target_events = [dates[50], dates[70], dates[90]]

    model, importance = analyzer.build_prediction_model(factors, target_events)

    if model is not None:
        assert importance is not None
        assert len(importance) == 3
        assert 'feature' in importance.columns
        assert 'importance' in importance.columns
    else:
        pytest.skip("无法构建模型（可能正样本不足）")


def test_build_prediction_model_no_events():
    """测试无事件时返回None"""
    from analysis.etf_lof_gamble import PredictiveFactorAnalyzer

    analyzer = PredictiveFactorAnalyzer()

    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    factors = pd.DataFrame({
        'factor1': np.random.randn(50),
    }, index=dates)

    model, importance = analyzer.build_prediction_model(factors, [])

    assert model is None
    assert importance is None
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_build_prediction_model -v
uv run pytest tests/test_etf_lof_gamble.py::test_build_prediction_model_no_events -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add prediction model building with RandomForest"
```

---

## Phase 4: AI Prompt集成

### Task 7: 添加ETF/LOF投机分析Prompt

**Files:**
- Modify: `core/agent/prompts.py`

**Step 1: 添加build_etf_lof_gamble_prompt方法**

在`PromptBuilder`类中添加：

```python
    @staticmethod
    def build_etf_lof_gamble_prompt(
        symbol: str,
        name: str,
        fund_type: str,
        abnormal_events: list[dict],
        current_factors: dict,
        feature_importance: pd.DataFrame,
        current_data: dict
    ) -> str:
        """
        构建ETF/LOF投机分析的Prompt

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
            f"{e['return']*100:.1f}% (波动率: {e['volatility']*100:.1f}%)"
            for e in recent_events
        ]) if recent_events else "无历史异常事件"

        # 格式化关键因子（Top 5）
        top_factors = feature_importance.head(5)
        factors_text = "\n".join([
            f"- {row['feature']}: {current_factors.get(row['feature'], 'N/A')} "
            f"(重要性: {row['importance']:.3f})"
            for _, row in top_factors.iterrows()
        ])

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

## 历史异常波动事件（最近5个）
{events_text}
总计发现 {len(abnormal_events)} 个异常波动事件

## 当前关键因子（Top 5）
{factors_text}

## 分析要求

请按以下结构进行分析（使用Markdown格式）：

### 1. 因子解读
分析当前关键因子值说明了什么？是否有预警信号？

### 2. 历史规律
该标的异常波动的特点是什么？通常持续多久？

### 3. 时机判断
当前是否适合买入？请给出明确判断：
- ✅ **适合买入** - 因子显示即将出现异常波动
- ⏸️ **观望** - 信号不明确，建议继续观察
- ❌ **不适合买入** - 因子显示风险较高

### 4. 操作建议
如果判断适合买入，请给出：
- **买入点位**: 具体价格（基于当前价格给出）
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

**Step 2: 编写测试**

创建文件：`tests/test_prompts_extension.py`

```python
import pytest
import pandas as pd
from core.agent.prompts import PromptBuilder
from datetime import datetime


def test_build_etf_lof_gamble_prompt():
    """测试ETF/LOF投机分析Prompt构建"""
    # 准备测试数据
    symbol = "163415"
    name = "白银LOF"
    fund_type = "LOF"

    abnormal_events = [
        {
            'date': pd.Timestamp('2024-01-15'),
            'return': 0.18,
            'volatility': 0.12
        },
        {
            'date': pd.Timestamp('2024-02-10'),
            'return': -0.20,
            'volatility': 0.15
        }
    ]

    current_factors = {
        'momentum_5': 0.05,
        'volume_ratio': 2.5,
        'rsi_14': 65
    }

    feature_importance = pd.DataFrame({
        'feature': ['momentum_5', 'volume_ratio', 'rsi_14'],
        'importance': [0.35, 0.28, 0.15]
    })

    current_data = {
        'price': 1.234,
        'change_pct': 2.5,
        'volume': 5000000,
        'volatility_20d': 0.08
    }

    prompt = PromptBuilder.build_etf_lof_gamble_prompt(
        symbol, name, fund_type, abnormal_events,
        current_factors, feature_importance, current_data
    )

    # 验证Prompt包含关键信息
    assert symbol in prompt
    assert name in prompt
    assert "因子解读" in prompt
    assert "历史规律" in prompt
    assert "时机判断" in prompt
    assert "操作建议" in prompt
    assert "风险提示" in prompt
    assert "适合买入" in prompt or "观望" in prompt or "不适合买入" in prompt

    print("\n" + "="*50)
    print(prompt)
    print("="*50)


def test_build_etf_lof_gamble_prompt_no_events():
    """测试无异常事件时的Prompt构建"""
    prompt = PromptBuilder.build_etf_lof_gamble_prompt(
        "163415", "白银LOF", "LOF",
        [],  # 无异常事件
        {}, {},
        {}
    )

    assert "无历史异常事件" in prompt
    assert "总计发现 0 个异常波动事件" in prompt
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_prompts_extension.py::test_build_etf_lof_gamble_prompt -v -s
```
Expected: PASS (并打印出Prompt示例)

**Step 4: Commit**

```bash
git add core/agent/prompts.py tests/test_prompts_extension.py
git commit -m "feat: add ETF/LOF gamble analysis prompt builder"
```

---

## Phase 5: 主分析器实现

### Task 8: 创建GambleAnalysisResult数据类和LOFETFGambleAnalyzer

**Files:**
- Modify: `analysis/etf_lof_gamble.py`

**Step 1: 添加数据类和主分析器**

```python
# 在 analysis/etf_lof_gamble.py 中添加

from dataclasses import dataclass
from typing import Optional
from core.agent.base_agent import BaseAgent


@dataclass
class GambleAnalysisResult:
    """ETF/LOF投机分析结果"""
    symbol: str
    name: str
    fund_type: str

    # 异常波动数据
    abnormal_events_count: int
    abnormal_events: list[dict]

    # 因子数据
    current_factors: dict
    feature_importance: Optional[pd.DataFrame]

    # AI分析
    ai_summary: str = ""
    timing_advice: str = ""
    action_advice: str = ""

    # 具体操作
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[list[float]] = None
    position_size: Optional[str] = None
    hold_period: Optional[str] = None


class LOFETFGambleAnalyzer:
    """ETF/LOF投机主分析器"""

    def __init__(self, agent: BaseAgent):
        """
        初始化分析器

        Args:
            agent: AI Agent实例
        """
        self.agent = agent
        from data.fetchers.akshare_fetcher import AKShareFetcher
        self.fetcher = AKShareFetcher()
        self.detector = VolatilityDetector()
        self.factor_analyzer = PredictiveFactorAnalyzer()

    def analyze_single(self, symbol: str, name: str, fund_type: str = "LOF") -> Optional[GambleAnalysisResult]:
        """
        分析单个LOF/ETF

        Args:
            symbol: 基金代码
            name: 基金名称
            fund_type: 基金类型

        Returns:
            GambleAnalysisResult 或 None
        """
        logger.info(f"开始分析 {name} ({symbol})")

        # 1. 获取历史数据
        df = self.fetcher.get_lof_etf_history(symbol, period=365)
        if df is None or len(df) < 100:
            logger.warning(f"{symbol} 数据不足，跳过")
            return None

        # 2. 检测异常波动
        abnormal_dates, abnormal_info = self.detector.detect_sudden_moves(
            df['close'], window=3, threshold=0.15
        )

        if len(abnormal_info) == 0:
            logger.info(f"{symbol} 未发现异常波动事件")
            return None

        logger.info(f"{symbol} 发现 {len(abnormal_info)} 个异常波动事件")

        # 3. 计算所有因子
        all_factors = self.factor_analyzer.calculate_all_factors(df)

        # 4. 构建预测模型
        model, feature_importance = self.factor_analyzer.build_prediction_model(
            all_factors, abnormal_dates
        )

        if feature_importance is None:
            logger.warning(f"{symbol} 无法构建预测模型")
            feature_importance = pd.DataFrame(columns=['feature', 'importance'])

        # 5. 准备当前数据
        current_factors = all_factors.iloc[-1].dropna().to_dict()

        current_data = {
            'price': df['close'].iloc[-1],
            'change_pct': df['close'].pct_change().iloc[-1] * 100 if len(df) > 1 else 0,
            'volume': df['volume'].iloc[-1] if 'volume' in df.columns else 0,
            'volatility_20d': df['close'].pct_change().rolling(20).std().iloc[-1] if len(df) >= 20 else None
        }

        # 6. AI分析
        try:
            from core.agent.prompts import PromptBuilder

            prompt = PromptBuilder.build_etf_lof_gamble_prompt(
                symbol, name, fund_type, abnormal_info,
                current_factors, feature_importance, current_data
            )

            ai_response = self.agent.chat(prompt)

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            ai_response = f"AI分析失败: {str(e)}"

        # 7. 构建结果
        result = GambleAnalysisResult(
            symbol=symbol,
            name=name,
            fund_type=fund_type,
            abnormal_events_count=len(abnormal_info),
            abnormal_events=abnormal_info,
            current_factors=current_factors,
            feature_importance=feature_importance,
            ai_summary=ai_response
        )

        return result
```

**Step 2: 编写测试**

```python
# 在 tests/test_etf_lof_gamble.py 中添加

@pytest.mark.integration
def test_analyze_single_with_mock_agent():
    """测试单个标的分析（使用Mock Agent）"""
    from unittest.mock import Mock
    from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
    from core.agent.base_agent import BaseAgent

    # 创建Mock Agent
    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="""
### 1. 因子解读
当前动量因子显示上升趋势...

### 2. 历史规律
该标的异常波动通常持续2-3天...

### 3. 时机判断
⏸️ **观望** - 信号不明确，建议继续观察

### 4. 操作建议
暂不建议买入，建议关注成交量和波动率变化...

### 5. 风险提示
主要风险在于...
    """)

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # 使用一个真实的LOF代码进行测试
    result = analyzer.analyze_single("163415", "白银LOF", "LOF")

    if result is not None:
        assert result.symbol == "163415"
        assert result.name == "白银LOF"
        assert result.abnormal_events_count >= 0
        assert result.ai_summary != ""
    else:
        pytest.skip("无法获取测试数据或无异常事件")


def test_analyze_single_with_insufficient_data():
    """测试数据不足的情况"""
    from unittest.mock import Mock
    from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
    from core.agent.base_agent import BaseAgent

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # Mock fetcher返回不足数据
    analyzer.fetcher.get_lof_etf_history = Mock(return_value=None)

    result = analyzer.analyze_single("000000", "Test", "LOF")

    assert result is None
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_analyze_single_with_mock_agent -v -s
```
Expected: PASS (需要真实数据)

**Step 4: Commit**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add LOFETFGambleAnalyzer main analyzer"
```

---

### Task 9: 添加批量筛选和分析方法

**Files:**
- Modify: `analysis/etf_lof_gamble.py`

**Step 1: 添加screen_and_analyze方法**

在`LOFETFGambleAnalyzer`类中添加：

```python
    def screen_and_analyze(
        self,
        criteria: dict = None,
        top_n: int = 20
    ) -> list[GambleAnalysisResult]:
        """
        筛选并对多个标的进行AI分析

        Args:
            criteria: 筛选条件，可包含:
                - window: 时间窗口（默认3）
                - threshold: 波动阈值（默认0.15）
                - fund_types: 基金类型列表 ['LOF', 'ETF'] 或 ['commodity', 'overseas']
            top_n: 返回数量

        Returns:
            分析结果列表
        """
        if criteria is None:
            criteria = {}

        window = criteria.get('window', 3)
        threshold = criteria.get('threshold', 0.15)
        fund_types = criteria.get('fund_types', ['commodity', 'overseas'])

        logger.info(f"开始筛选分析，窗口={window}天，阈值={threshold*100}%")

        # 1. 获取目标列表
        target_list = []
        if 'commodity' in fund_types:
            commodity_lof = self.fetcher.get_commodity_lof_list()
            target_list.extend(commodity_lof)

        if 'overseas' in fund_types:
            overseas_etf = self.fetcher.get_overseas_etf_list()
            target_list.extend(overseas_etf)

        logger.info(f"获取到 {len(target_list)} 个目标标的")

        # 2. 快速筛选：检测异常波动
        screened = []
        for item in target_list[:top_n * 3]:  # 多取一些用于筛选
            symbol = item['code']
            name = item['name']
            fund_type = item['type']

            try:
                df = self.fetcher.get_lof_etf_history(symbol, period=180)
                if df is None or len(df) < 100:
                    continue

                abnormal_dates, _ = self.detector.detect_sudden_moves(
                    df['close'], window=window, threshold=threshold
                )

                if len(abnormal_dates) > 0:
                    screened.append({
                        'symbol': symbol,
                        'name': name,
                        'fund_type': fund_type,
                        'events_count': len(abnormal_dates),
                        'recent_change': df['close'].pct_change(window).iloc[-1]
                    })

            except Exception as e:
                logger.error(f"筛选 {symbol} 失败: {e}")
                continue

        # 3. 按异常事件数量排序，取前top_n个
        screened.sort(key=lambda x: x['events_count'], reverse=True)
        top_targets = screened[:top_n]

        logger.info(f"筛选出 {len(top_targets)} 个目标进行深度分析")

        # 4. 深度分析
        results = []
        for target in top_targets:
            try:
                result = self.analyze_single(
                    target['symbol'],
                    target['name'],
                    target['fund_type']
                )
                if result is not None:
                    results.append(result)

            except Exception as e:
                logger.error(f"分析 {target['symbol']} 失败: {e}")
                continue

        logger.info(f"完成 {len(results)} 个标的的分析")
        return results

    def get_top_factors_across_funds(self, results: list[GambleAnalysisResult]) -> pd.DataFrame:
        """
        获取所有标的中的重要因子

        Args:
            results: 分析结果列表

        Returns:
            因子重要性排序DataFrame
        """
        all_importances = []
        for result in results:
            if result.feature_importance is not None and len(result.feature_importance) > 0:
                importance_df = result.feature_importance.copy()
                importance_df['fund'] = result.symbol
                importance_df['fund_name'] = result.name
                all_importances.append(importance_df)

        if not all_importances:
            return pd.DataFrame(columns=['feature', 'mean', 'count'])

        combined = pd.concat(all_importances, ignore_index=True)

        # 计算因子在所有基金中的平均重要性
        factor_ranking = combined.groupby('feature')['importance'].agg(['mean', 'count']).reset_index()
        factor_ranking = factor_ranking.sort_values('mean', ascending=False)
        factor_ranking.columns = ['feature', 'mean_importance', 'occurrence_count']

        return factor_ranking
```

**Step 2: 编写测试**

```python
# 在 tests/test_etf_lof_gamble.py 中添加

@pytest.mark.integration
def test_screen_and_analyze():
    """测试批量筛选分析"""
    from unittest.mock import Mock
    from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
    from core.agent.base_agent import BaseAgent

    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="测试AI分析结果...")

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    results = analyzer.screen_and_analyze(criteria, top_n=5)

    # 验证结果
    assert isinstance(results, list)
    # 注意：实际数量取决于数据可用性
    if len(results) > 0:
        assert all(isinstance(r, GambleAnalysisResult) for r in results)


def test_get_top_factors_across_funds():
    """测试跨标的因子汇总"""
    from analysis.etf_lof_gamble import LOFETFGambleAnalyzer, GambleAnalysisResult
    from core.agent.base_agent import BaseAgent
    from unittest.mock import Mock

    analyzer = LOFETFGambleAnalyzer(Mock(spec=BaseAgent))

    # 创建模拟结果
    importance1 = pd.DataFrame({
        'feature': ['momentum_5', 'volume_ratio', 'rsi_14'],
        'importance': [0.4, 0.3, 0.2]
    })

    importance2 = pd.DataFrame({
        'feature': ['volume_ratio', 'momentum_5', 'macd'],
        'importance': [0.35, 0.25, 0.15]
    })

    result1 = GambleAnalysisResult(
        symbol="001", name="Fund1", fund_type="LOF",
        abnormal_events_count=5, abnormal_events=[],
        current_factors={}, feature_importance=importance1
    )

    result2 = GambleAnalysisResult(
        symbol="002", name="Fund2", fund_type="ETF",
        abnormal_events_count=3, abnormal_events=[],
        current_factors={}, feature_importance=importance2
    )

    factor_ranking = analyzer.get_top_factors_across_funds([result1, result2])

    assert len(factor_ranking) > 0
    assert 'momentum_5' in factor_ranking['feature'].values
    assert 'volume_ratio' in factor_ranking['feature'].values

    # momentum_5应该出现2次
    momentum_row = factor_ranking[factor_ranking['feature'] == 'momentum_5']
    assert momentum_row['occurrence_count'].values[0] == 2
```

**Step 3: 运行测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py::test_get_top_factors_across_funds -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add batch screening and analysis methods"
```

---

## Phase 6: UI集成

### Task 10: 添加菜单和页面结构

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: 导入新分析器**

在文件顶部的导入部分添加：

```python
# 在现有导入后添加
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
```

**Step 2: 添加到get_analyzers函数**

修改`get_analyzers`函数：

```python
@st.cache_resource
def get_analyzers(_agent):
    """获取分析器实例（缓存以提高性能）"""
    if _agent is None:
        return None, None, None, None, None

    try:
        screener = StockScreener(_agent)
        market_analyzer = MarketAnalyzer(_agent)
        etf_analyzer = ETFAnalyzer(_agent)
        cb_technical_analyzer = ConvertibleBondTechnicalAnalyzer(_agent)
        gamble_analyzer = LOFETFGambleAnalyzer(_agent)  # 新增
        return screener, market_analyzer, etf_analyzer, cb_technical_analyzer, gamble_analyzer
    except Exception as e:
        st.error(f"初始化分析器失败: {str(e)}")
        return None, None, None, None, None
```

**Step 3: 修改main函数中的初始化**

```python
def main():
    """主函数"""
    # 初始化 Agent 和分析器
    agent = initialize_agent()
    screener, market_analyzer, etf_analyzer, cb_technical_analyzer, gamble_analyzer = get_analyzers(agent)
    # ... 其余代码
```

**Step 4: 添加侧边栏菜单**

在侧边栏的page选项中添加：

```python
page = st.radio(
    "选择功能",
    ["首页", "选股筛选", "市场分析", "ETF 分析", "可转债分析", "ETF/LOF投机"],  # 新增
    label_visibility="collapsed"
)
```

**Step 5: 添加系统状态显示**

在侧边栏的系统状态部分添加：

```python
if gamble_analyzer is not None:
    st.success("✅ 投机分析模块就绪")
else:
    st.error("❌ 投机分析模块未就绪")
```

**Step 6: 添加页面路由**

在main函数的页面路由部分添加：

```python
elif page == "ETF/LOF投机":
    if gamble_analyzer is None:
        st.error("投机分析模块未初始化，请检查配置！")
    else:
        render_etf_lof_gamble_page(gamble_analyzer)
```

**Step 7: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add ETF/LOF speculation menu and navigation"
```

---

### Task 11: 实现异常波动筛选页面

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: 创建render_etf_lof_gamble_page函数**

在文件中添加：

```python
def render_etf_lof_gamble_page(gamble_analyzer):
    """渲染ETF/LOF投机分析页面"""
    st.markdown('<div class="sub-header">🎰 ETF/LOF 投机分析</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        识别大宗商品LOF和海外ETF的异常波动（2-3天突增突降），计算预测因子，AI分析并给出操作建议。
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["异常波动筛选", "AI深度分析"])

    with tab1:
        render_abnormal_screening_page(gamble_analyzer)

    with tab2:
        render_ai_analysis_page(gamble_analyzer)


def render_abnormal_screening_page(gamble_analyzer):
    """渲染异常波动筛选页面"""
    st.subheader("异常波动筛选")

    with st.form("abnormal_screening_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            window = st.selectbox(
                "时间窗口",
                options=[2, 3, 5],
                format_func=lambda x: f"{x}天",
                index=1  # 默认3天
            )

        with col2:
            threshold = st.slider(
                "波动阈值",
                min_value=5,
                max_value=30,
                value=15,
                help="累计涨跌幅超过此百分比视为异常"
            )

        with col3:
            fund_types = st.multiselect(
                "标的选择",
                options=["大宗商品LOF", "海外ETF"],
                default=["大宗商品LOF", "海外ETF"]
            )

        top_n = st.slider("返回数量", min_value=5, max_value=50, value=20)

        submitted = st.form_submit_button("开始筛选", use_container_width=True)

    if submitted:
        if not fund_types:
            st.error("请至少选择一种标的类型！")
            return

        # 转换fund_types
        fund_type_map = {
            "大宗商品LOF": "commodity",
            "海外ETF": "overseas"
        }
        criteria_types = [fund_type_map[t] for t in fund_types]

        criteria = {
            'window': window,
            'threshold': threshold / 100,  # 转换为小数
            'fund_types': criteria_types
        }

        # 显示筛选条件
        st.markdown("### 筛选条件")
        criteria_df = pd.DataFrame([
            {"参数": "时间窗口", "值": f"{window}天"},
            {"参数": "波动阈值", "值": f"≥ ±{threshold}%"},
            {"参数": "标的类型", "值": ", ".join(fund_types)},
            {"参数": "返回数量", "值": top_n}
        ])
        st.dataframe(criteria_df, use_container_width=True, hide_index=True)

        # 执行筛选
        with st.spinner("正在筛选分析，请稍候..."):
            try:
                results = gamble_analyzer.screen_and_analyze(criteria, top_n)

                if results:
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>筛选完成！找到 {len(results)} 个异常波动标的</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    # 显示结果列表
                    display_screening_results(results)

                else:
                    st.markdown("""
                    <div class="warning-box">
                        <h4>未找到符合条件的标的</h4>
                        <p>请尝试调整筛选条件...</p>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                    <h4>筛选失败</h4>
                    <p>错误信息: {str(e)}</p>
                </div>
                """, unsafe_allow_html=True)


def display_screening_results(results: list):
    """显示筛选结果"""
    # 准备数据
    result_data = []
    for r in results:
        # 获取最近异常事件
        recent_event = r.abnormal_events[-1] if r.abnormal_events else None
        recent_change = recent_event['return'] * 100 if recent_event else 0

        result_data.append({
            "代码": r.symbol,
            "名称": r.name,
            "类型": r.fund_type,
            "异常事件数": r.abnormal_events_count,
            "最近波动": f"{recent_change:.1f}%",
            "当前价格": f"{r.current_data.get('price', 'N/A')}"
        })

    df = pd.DataFrame(result_data)

    st.dataframe(
        df,
        column_config={
            "代码": st.column_config.TextColumn("代码", width="short"),
            "名称": st.column_config.TextColumn("名称", width="medium"),
            "类型": st.column_config.TextColumn("类型", width="short"),
            "异常事件数": st.column_config.NumberColumn("异常事件", width="short"),
            "最近波动": st.column_config.TextColumn("最近波动", width="short"),
            "当前价格": st.column_config.TextColumn("当前价格", width="short")
        },
        use_container_width=True,
        hide_index=True
    )

    # 选择查看详情
    st.markdown("---")
    st.subheader("查看AI分析详情")

    selected_code = st.selectbox(
        "选择标的查看详情",
        options=[r.symbol for r in results],
        format_func=lambda x: next((r.name for r in results if r.symbol == x), x)
    )

    if selected_code:
        selected_result = next((r for r in results if r.symbol == selected_code), None)
        if selected_result:
            with st.expander(f"📊 {selected_result.name} ({selected_result.symbol}) - AI分析", expanded=True):
                st.markdown(selected_result.ai_summary)
```

**Step 2: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add abnormal volatility screening page"
```

---

### Task 12: 实现AI深度分析页面

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: 创建render_ai_analysis_page函数**

```python
def render_ai_analysis_page(gamble_analyzer):
    """渲染AI深度分析页面"""
    st.subheader("AI深度分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        analysis_code = st.text_input(
            "基金代码",
            placeholder="如 163415",
            help="输入6位基金代码"
        )

    with col2:
        st.write("")  # 占位
        analyze_btn = st.button("开始分析", type="primary")

    if analyze_btn and analysis_code:
        with st.spinner("正在分析，请稍候..."):
            try:
                # 这里简化处理，实际应该根据代码获取名称
                result = gamble_analyzer.analyze_single(
                    analysis_code,
                    f"基金{analysis_code}",  # 简化名称
                    "LOF"  # 默认类型
                )

                if result:
                    display_ai_analysis_result(result)
                else:
                    st.warning("""
                    **分析未完成**

                    可能原因：
                    1. 数据不足（需要至少100天历史数据）
                    2. 未发现异常波动事件
                    3. 无法获取数据

                    请尝试其他代码或调整筛选条件。
                    """)

            except Exception as e:
                st.error(f"分析失败: {str(e)}")

    # 使用说明
    with st.expander("💡 使用说明"):
        st.markdown("""
        ### 常见LOF/ETF代码参考

        **大宗商品LOF：**
        - 163415: 白银LOF
        - 161116: 黄金基金
        - 162411: 华宝油气
        - 160716: 有色金属

        **海外ETF：**
        - 513100: 纳斯达克100
        - 513500: 标普500
        - 513660: 恒生ETF

        ### 分析内容

        AI将为您分析：
        1. **因子解读** - 当前关键因子说明了什么
        2. **历史规律** - 该标的异常波动的特点
        3. **时机判断** - 是否适合买入
        4. **操作建议** - 买入点位、止盈止损
        5. **风险提示** - 主要风险点
        """)


def display_ai_analysis_result(result):
    """显示AI分析结果"""
    # 基础信息卡片
    st.markdown(f"""
    <div class="success-box">
        <h4>📊 {result.name} ({result.symbol})</h4>
        <p>类型: {result.fund_type} | 异常事件: {result.abnormal_events_count}次</p>
    </div>
    """, unsafe_allow_html=True)

    # AI分析
    st.markdown(result.ai_summary)

    # 关键因子展示
    if result.feature_importance is not None and len(result.feature_importance) > 0:
        with st.expander("📈 关键因子排名"):
            st.dataframe(
                result.feature_importance.head(10),
                column_config={
                    "feature": "因子",
                    "importance": st.column_config.NumberColumn("重要性", format="%.3f")
                },
                use_container_width=True,
                hide_index=True
            )

    # 异常事件历史
    if result.abnormal_events:
        with st.expander("📜 异常波动历史"):
            events_df = pd.DataFrame(result.abnormal_events)
            events_df['date'] = events_df['date'].dt.strftime('%Y-%m-%d')
            events_df['return'] = (events_df['return'] * 100).round(1).astype(str) + '%'
            events_df['volatility'] = (events_df['volatility'] * 100).round(1).astype(str) + '%'

            st.dataframe(
                events_df[['date', 'return', 'start_price', 'end_price', 'volatility']],
                column_config={
                    "date": "日期",
                    "return": "涨跌幅",
                    "start_price": "起始价",
                    "end_price": "结束价",
                    "volatility": "波动率"
                },
                use_container_width=True,
                hide_index=True
            )
```

**Step 2: 测试UI**

```bash
uv run streamlit run ui/dashboard.py
```

**Step 3: Commit**

```bash
git add ui/dashboard.py
git add ui/dashboard.py
git commit -m "feat: add AI analysis page for single fund"
```

---

### Task 13: 添加因子分析汇总页面（可选）

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: 添加第三个Tab**

修改`render_etf_lof_gamble_page`函数，添加第三个Tab：

```python
tab1, tab2, tab3 = st.tabs(["异常波动筛选", "AI深度分析", "因子分析汇总"])

# ... 现有代码 ...

with tab3:
    render_factor_summary_page(gamble_analyzer)
```

**Step 2: 添加因子汇总页面函数**

```python
def render_factor_summary_page(gamble_analyzer):
    """渲染因子分析汇总页面"""
    st.subheader("因子分析汇总")

    st.markdown("""
    <div class="info-box">
        对多个标的进行批量分析后，查看跨标的因子重要性排名。
    </div>
    """, unsafe_allow_html=True)

    with st.form("factor_summary_form"):
        col1, col2 = st.columns(2)

        with col1:
            summary_window = st.selectbox("时间窗口", [2, 3, 5], index=1)

        with col2:
            summary_threshold = st.slider("波动阈值", 5, 30, 15)
            summary_fund_types = st.multiselect(
                "标的",
                ["大宗商品LOF", "海外ETF"],
                default=["大宗商品LOF", "海外ETF"]
            )

        summary_top_n = st.slider("分析数量", 10, 50, 20)

        submitted = st.form_submit_button("开始分析", use_container_width=True)

    if submitted:
        if not summary_fund_types:
            st.error("请选择标的类型")
            return

        with st.spinner("正在分析多个标的，请稍候..."):
            try:
                fund_type_map = {"大宗商品LOF": "commodity", "海外ETF": "overseas"}
                criteria_types = [fund_type_map[t] for t in summary_fund_types]

                criteria = {
                    'window': summary_window,
                    'threshold': summary_threshold / 100,
                    'fund_types': criteria_types
                }

                results = gamble_analyzer.screen_and_analyze(criteria, summary_top_n)

                if results:
                    st.success(f"分析完成！共分析 {len(results)} 个标的")

                    # 获取因子排名
                    factor_ranking = gamble_analyzer.get_top_factors_across_funds(results)

                    if len(factor_ranking) > 0:
                        st.markdown("### 跨标的因子重要性排名")

                        st.dataframe(
                            factor_ranking,
                            column_config={
                                "feature": st.column_config.TextColumn("因子", width="medium"),
                                "mean_importance": st.column_config.NumberColumn("平均重要性", format="%.3f"),
                                "occurrence_count": st.column_config.NumberColumn("出现次数")
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                        # 因子说明
                        st.markdown("---")
                        st.markdown("### 因子说明")

                        factor_descriptions = {
                            'momentum_5': '5日价格动量 - 反映短期价格趋势',
                            'momentum_10': '10日价格动量 - 反映中期价格趋势',
                            'momentum_20': '20日价格动量 - 反映长期价格趋势',
                            'volatility_20': '20日波动率 - 反映价格波动程度',
                            'atr_14': 'ATR(14) - 平均真实波幅',
                            'volume_ratio': '量比 - 当前成交量/20日平均成交量',
                            'volume_ma_5': '5日/20日成交量比',
                            'rsi_14': 'RSI(14) - 相对强弱指标',
                            'macd': 'MACD - 指数平滑异同移动平均线',
                            'bollinger_bandwidth': '布林带带宽 - 反映价格波动范围',
                            'pv_divergence': '价量背离 - 价格与成交量变化差异',
                            'spread_pct': '买卖价差百分比',
                            'liquidity_impact': '流动性冲击',
                            'price_trend': '价格趋势方向',
                            'vol_clustering': '波动聚集性'
                        }

                        for _, row in factor_ranking.head(10).iterrows():
                            factor = row['feature']
                            desc = factor_descriptions.get(factor, '暂无说明')
                            st.markdown(f"**{factor}**: {desc}")

                else:
                    st.warning("未找到符合条件的标的")

            except Exception as e:
                st.error(f"分析失败: {str(e)}")
```

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add factor analysis summary page"
```

---

## Phase 7: 测试与优化

### Task 14: 完善测试覆盖

**Files:**
- Modify: `tests/test_etf_lof_gamble.py`

**Step 1: 添加集成测试**

```python
@pytest.mark.integration
def test_full_analysis_workflow():
    """完整分析流程测试"""
    from unittest.mock import Mock
    from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
    from core.agent.base_agent import BaseAgent

    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="""
### 1. 因子解读
因子显示...

### 2. 历史规律
历史波动...

### 3. 时机判断
✅ **适合买入**

### 4. 操作建议
- 买入点位: 1.200元
- 止盈位: 1.280元
- 止损位: 1.150元
- 建议仓位: 轻仓
- 持有周期: 2-3天

### 5. 风险提示
注意...
    """)

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # 测试单个分析
    result = analyzer.analyze_single("163415", "白银LOF", "LOF")

    if result:
        assert result.ai_summary != ""
        assert result.symbol == "163415"

    # 测试批量筛选
    criteria = {'window': 3, 'threshold': 0.15, 'fund_types': ['commodity']}
    results = analyzer.screen_and_analyze(criteria, top_n=5)

    assert isinstance(results, list)

    # 测试因子汇总
    if results:
        factor_ranking = analyzer.get_top_factors_across_funds(results)
        assert isinstance(factor_ranking, pd.DataFrame)
```

**Step 2: 运行所有测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py -v
```

**Step 3: 运行集成测试**

```bash
uv run pytest tests/test_etf_lof_gamble.py -v -m integration
```

**Step 4: Commit**

```bash
git add tests/test_etf_lof_gamble.py
git commit -m "test: add comprehensive integration tests"
```

---

### Task 15: 添加缓存优化

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: 添加数据缓存**

在`render_etf_lof_gamble_page`函数中添加缓存：

```python
@st.cache_data(ttl=1800)  # 30分钟缓存
def cached_screen_and_analyze(_analyzer, criteria, top_n):
    """缓存的筛选分析"""
    return _analyzer.screen_and_analyze(criteria, top_n)


@st.cache_data(ttl=1800)
def cached_analyze_single(_analyzer, symbol, name, fund_type):
    """缓存的单个分析"""
    return _analyzer.analyze_single(symbol, name, fund_type)
```

**Step 2: 更新页面函数使用缓存**

```python
def render_abnormal_screening_page(gamble_analyzer):
    # ... 现有代码 ...

        with st.spinner("正在筛选分析，请稍候..."):
            try:
                results = cached_screen_and_analyze(gamble_analyzer, criteria, top_n)
                # ... 其余代码 ...
```

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "perf: add caching for analysis results"
```

---

### Task 16: 更新文档

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 更新项目文档**

在`CLAUDE.md`的Analysis Modules部分后添加：

```markdown
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
from core.agent.glm_agent import GLMAgent
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer

agent = GLMAgent()
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
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with ETF/LOF speculation feature"
```

---

## 完成

### Task 17: 最终验证

**Step 1: 运行完整测试套件**

```bash
uv run pytest tests/ -v
```

**Step 2: 启动UI测试**

```bash
uv run streamlit run ui/dashboard.py
```

**Step 3: 验证功能**

- [ ] 侧边栏显示"ETF/LOF投机"菜单
- [ ] 系统状态显示"投机分析模块就绪"
- [ ] 异常波动筛选页面正常工作
- [ ] AI深度分析页面正常工作
- [ ] 因子分析汇总页面正常工作

**Step 4: 最终提交**

```bash
git add .
git commit -m "feat: complete ETF/LOF speculation analysis feature

- Add VolatilityDetector for abnormal move detection
- Add PredictiveFactorAnalyzer for multi-factor calculation
- Add LOFETFGambleAnalyzer with AI integration
- Add UI pages for screening and analysis
- Add comprehensive tests

Supports:
- 2-3 day abnormal volatility detection
- Technical, liquidity, and commodity-specific factors
- AI-powered entry/exit recommendations
- Cross-security factor ranking
"
```

---

## 实施检查清单

- [ ] Task 0: 安装依赖
- [ ] Task 1: 扩展AKShareFetcher - LOF/ETF列表获取
- [ ] Task 2: 扩展AKShareFetcher - 历史数据获取
- [ ] Task 3: 创建VolatilityDetector类
- [ ] Task 4: 创建PredictiveFactorAnalyzer - 技术因子
- [ ] Task 5: 完善PredictiveFactorAnalyzer - 流动性和商品因子
- [ ] Task 6: 添加预测模型构建方法
- [ ] Task 7: 添加ETF/LOF投机分析Prompt
- [ ] Task 8: 创建GambleAnalysisResult和LOFETFGambleAnalyzer
- [ ] Task 9: 添加批量筛选和分析方法
- [ ] Task 10: 添加菜单和页面结构
- [ ] Task 11: 实现异常波动筛选页面
- [ ] Task 12: 实现AI深度分析页面
- [ ] Task 13: 添加因子分析汇总页面
- [ ] Task 14: 完善测试覆盖
- [ ] Task 15: 添加缓存优化
- [ ] Task 16: 更新文档
- [ ] Task 17: 最终验证
