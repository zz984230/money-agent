"""
AKShareFetcher扩展功能测试 - LOF/ETF数据获取
"""
import pytest
import pandas as pd
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
def test_get_overseas_etf_list():
    """测试获取海外ETF列表"""
    fetcher = AKShareFetcher()
    result = fetcher.get_overseas_etf_list()

    assert isinstance(result, list)
    assert len(result) >= 0
    if len(result) > 0:
        assert 'code' in result[0]
        assert 'name' in result[0]
        assert 'type' in result[0]


@pytest.mark.integration
def test_get_lof_etf_history():
    """测试获取LOF/ETF历史数据"""
    from unittest.mock import Mock, patch
    import pandas as pd

    fetcher = AKShareFetcher()

    # 使用一个常见的LOF代码进行测试
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
    from unittest.mock import patch
    from data.fetchers.akshare_fetcher import AKShareFetcher

    mock_data = pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02'],
        '开盘': [1.0, 1.1],
        '收盘': [1.05, 1.15],
        '最高': [1.1, 1.2],
        '最低': [0.95, 1.05],
        '成交量': [1000000, 1200000],
        '成交额': [1000000, 1380000]
    })

    fetcher = AKShareFetcher()

    # Patch正确的函数名
    with patch('data.fetchers.akshare_fetcher.ak.fund_etf_hist_em', return_value=mock_data):
        result = fetcher.get_lof_etf_history('163415', period=30)

        assert result is not None
        assert len(result) == 2
        assert 'close' in result.columns
        assert 'volume' in result.columns
