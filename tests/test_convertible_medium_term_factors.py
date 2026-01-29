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
