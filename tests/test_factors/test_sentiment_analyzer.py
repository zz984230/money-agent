"""SentimentAnalyzer测试"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
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


def test_calculate_sentiment_factors_dataframe_structure(sentiment_analyzer):
    """测试情绪因子DataFrame结构"""
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
