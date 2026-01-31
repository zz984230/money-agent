"""ETFLOFSpecificAnalyzer测试"""
import pytest
import pandas as pd
import numpy as np
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

    # 白银基金成交额500000，在三者中排名第三（2000000 > 1000000 > 500000）
    assert rank == 3

    # 测试163415排名第二
    rank_163415 = specific_analyzer.calculate_liquidity_rank('163415', all_funds)
    assert rank_163415 == 2

    # 测试518880排名第一
    rank_518880 = specific_analyzer.calculate_liquidity_rank('518880', all_funds)
    assert rank_518880 == 1


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


def test_get_premium_discount_rate_with_nav_and_quote(specific_analyzer):
    """测试获取溢价率（有净值和行情数据）"""
    specific_analyzer.fetcher.get_etf_lof_nav = Mock(return_value=1.000)
    specific_analyzer.fetcher.get_etf_lof_realtime_quote = Mock(return_value={'price': 1.030, 'amount': 1000000})

    rate = specific_analyzer.get_premium_discount_rate('163415', 'LOF')

    assert rate is not None
    assert abs(rate - 0.03) < 0.001


def test_get_premium_discount_rate_with_missing_data(specific_analyzer):
    """测试获取溢价率（缺少数据）"""
    specific_analyzer.fetcher.get_etf_lof_nav = Mock(return_value=None)
    specific_analyzer.fetcher.get_etf_lof_realtime_quote = Mock(return_value=None)

    rate = specific_analyzer.get_premium_discount_rate('163415', 'LOF')

    assert rate is None
