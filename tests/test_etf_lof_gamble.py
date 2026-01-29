"""
ETF/LOF投机异常波动分析模块测试
"""
import pytest
import pandas as pd
import numpy as np
from analysis.etf_lof_gamble import VolatilityDetector, AbnormalEvent


def test_detect_sudden_moves_no_abnormal():
    """测试无异常波动的情况"""
    detector = VolatilityDetector()

    # 创建稳定的价格序列（1%的日常波动）
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
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
    assert 'return_pct' in event
    assert 'volatility' in event
    assert abs(event['return_pct']) > 0.15


def test_multi_timeframe_analysis():
    """测试多时间框架分析"""
    detector = VolatilityDetector()

    # 创建有波动的价格序列
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
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


def test_volatility_detector_initialization():
    """测试VolatilityDetector初始化"""
    detector = VolatilityDetector()
    assert detector.events == []
    assert hasattr(detector, 'detect_sudden_moves')
    assert hasattr(detector, 'multi_timeframe_analysis')


def test_abnormal_event_dataclass():
    """测试AbnormalEvent数据类"""
    date = pd.Timestamp('2024-01-15')
    event = AbnormalEvent(
        date=date,
        return_pct=0.18,
        start_price=100.0,
        end_price=118.0,
        volatility=0.12,
        window=3
    )

    assert event.date == date
    assert event.return_pct == 0.18
    assert event.start_price == 100.0
    assert event.end_price == 118.0
    assert event.volatility == 0.12
    assert event.window == 3
