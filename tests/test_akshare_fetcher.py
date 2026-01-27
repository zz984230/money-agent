import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import pandas as pd

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetchers.akshare_fetcher import AKShareFetcher

@patch('akshare.stock_zh_a_spot_em')
def test_get_stock_list(mock_stock_zh_a_spot_em):
    """测试获取 A 股列表"""
    # Mock返回数据
    mock_data = pd.DataFrame({
        '代码': ['000001', '000002', '600000'],
        '名称': ['平安银行', '万科A', '浦发银行'],
        '最新价': [12.5, 18.8, 15.2],
        '涨跌幅': [1.2, 0.8, -0.5]
    })
    mock_stock_zh_a_spot_em.return_value = mock_data

    fetcher = AKShareFetcher()
    stock_list = fetcher.get_stock_list()
    assert isinstance(stock_list, list)
    assert len(stock_list) > 0
    assert '代码' in stock_list[0] or 'code' in stock_list[0]
    mock_stock_zh_a_spot_em.assert_called_once()

@patch('akshare.stock_zh_a_hist')
def test_get_stock_daily(mock_stock_zh_a_hist):
    """测试获取日线数据"""
    # Mock返回数据
    mock_data = pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
        '开盘': [10.0, 10.5, 11.0],
        '收盘': [10.5, 11.0, 11.5],
        '最高': [10.8, 11.2, 11.8],
        '最低': [9.9, 10.4, 10.9],
        '成交量': [1000000, 1200000, 1500000],
        '成交额': [10500000, 12600000, 17250000]
    })
    mock_stock_zh_a_hist.return_value = mock_data

    fetcher = AKShareFetcher()
    df = fetcher.get_stock_daily("000001", "2024-01-01", "2024-01-31")
    assert df is not None
    assert len(df) > 0
    assert 'close' in df.columns
    assert df['date'].dtype == 'datetime64[ns]'
    mock_stock_zh_a_hist.assert_called_once_with(symbol="000001", period="daily", start_date="2024-01-01", end_date="2024-01-31", adjust="")

@patch('akshare.fund_etf_hist_sina')
def test_get_etf_daily(mock_fund_etf_hist_sina):
    """测试获取ETF日线数据"""
    # Mock返回数据
    mock_data = pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
        '开盘': [5.0, 5.1, 5.2],
        '收盘': [5.1, 5.2, 5.3],
        '最高': [5.2, 5.3, 5.4],
        '最低': [4.9, 5.0, 5.1],
        '成交量': [500000, 600000, 700000],
        '成交额': [2550000, 3120000, 3710000]
    })
    mock_fund_etf_hist_sina.return_value = mock_data

    fetcher = AKShareFetcher()
    df = fetcher.get_etf_daily("510300", "2024-01-01", "2024-01-31")
    assert df is not None
    assert len(df) > 0
    assert 'close' in df.columns
    assert df['date'].dtype == 'datetime64[ns]'
    mock_fund_etf_hist_sina.assert_called_once_with(symbol="510300", period="daily", start_date="2024-01-01", end_date="2024-01-31")

def test_get_etf_list():
    """测试获取 ETF 列表"""
    fetcher = AKShareFetcher()
    etf_list = fetcher.get_etf_list()
    assert isinstance(etf_list, list)
    assert len(etf_list) > 0

@patch('akshare.bond_cb_jsl')
def test_get_convertible_list(mock_bond_cb_jsl):
    """测试获取可转债列表"""
    # Mock返回数据
    mock_data = pd.DataFrame({
        '代码': ['113527', '113528'],
        '名称': ['兴业转债', '国君转债'],
        '现价': [100.5, 101.2],
        '涨跌幅': [0.5, 1.2]
    })
    mock_bond_cb_jsl.return_value = mock_data

    fetcher = AKShareFetcher()
    cb_list = fetcher.get_convertible_list()
    assert isinstance(cb_list, list)
    assert len(cb_list) > 0
    mock_bond_cb_jsl.assert_called_once()

@patch('akshare.bond_zh_hs_cov_daily')
def test_get_convertible_daily(mock_bond_cb_hist):
    """测试获取可转债日线数据"""
    # Mock返回数据
    mock_data = pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
        '开盘': [100.0, 100.5, 101.0],
        '收盘': [100.5, 101.0, 101.5],
        '最高': [100.8, 101.2, 101.8],
        '最低': [99.9, 100.4, 100.9],
        '成交量': [10000, 12000, 15000],
        '成交额': [1005000, 1212000, 1522500]
    })
    mock_bond_cb_hist.return_value = mock_data

    fetcher = AKShareFetcher()
    df = fetcher.get_convertible_daily("113527", "2024-01-01", "2024-01-31")
    assert df is not None
    assert len(df) > 0
    assert 'close' in df.columns
    assert df['date'].dtype == 'datetime64[ns]'
    mock_bond_cb_hist.assert_called_once_with(symbol="113527")