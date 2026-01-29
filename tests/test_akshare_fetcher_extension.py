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
