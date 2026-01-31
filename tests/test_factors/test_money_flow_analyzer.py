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


def test_get_northbound_flow(flow_analyzer):
    """测试获取北向资金流"""
    mock_northbound_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10, freq='D'),
        'northbound_net_inflow': [100, 200, 150, 180, 220,
                                   190, 210, 230, 200, 180]
    })
    flow_analyzer.fetcher.get_northbound_capital_data = Mock(
        return_value=mock_northbound_data
    )

    result = flow_analyzer.get_northbound_flow('163415')

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10
