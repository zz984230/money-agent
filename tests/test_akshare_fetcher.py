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


class TestAKShareFetcherConvertible:
    """测试可转债数据获取"""

    @pytest.fixture
    def fetcher(self):
        return AKShareFetcher()

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_detail_success(self, mock_bond_cb_jsl, fetcher):
        """测试成功获取可转债详细信息"""
        # Mock AKShare返回数据 - 使用实际的数据结构
        # 列：代码, 转债名称, 现价, 涨跌幅, 正股代码, 正股名称, 正股价, 正股涨跌, 正股PB, 转股价, 转股价值, 转股溢价率, 债券评级, 回售触发价, 强赎触发价
        mock_df = pd.DataFrame({
            '代码': ['113527'],
            '转债名称': ['利民转债'],
            '现价': [105.5],
            '涨跌幅': [0.5],
            '正股代码': ['603798'],
            '正股名称': ['利民股份'],
            '正股价': [10.5],
            '正股涨跌': [1.2],
            '正股PB': [2.5],
            '转股价': [15.0],
            '转股价值': [100.5],
            '转股溢价率': [5.0],
            '债券评级': ['AA-'],
            '回售触发价': [90],
            '强赎触发价': [130],
        })
        mock_bond_cb_jsl.return_value = mock_df

        result = fetcher.get_convertible_detail('113527')

        assert result is not None
        assert result['cb_code'] == '113527'
        assert result['cb_name'] == '利民转债'
        assert result['put_trigger_price'] == 90
        assert result['call_trigger_price'] == 130
        assert result['conversion_price'] == 15.0
        assert result['stock_code'] == '603798'
        assert result['stock_name'] == '利民股份'

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_detail_not_found(self, mock_bond_cb_jsl, fetcher):
        """测试转债不存在的情况"""
        mock_df = pd.DataFrame()
        mock_bond_cb_jsl.return_value = mock_df

        result = fetcher.get_convertible_detail('999999')

        assert result is None

    @patch('akshare.bond_zh_hs_cov_spot')
    def test_get_convertible_realtime_success(self, mock_bond_spot, fetcher):
        """测试成功获取实时行情和盘口"""
        mock_spot_data = pd.DataFrame({
            'code': ['113527'],
            'name': ['利民转债'],
            'trade': [105.5],
            'changepercent': [0.5],
            'volume': [1000000],
            'amount': [105500000],
            'high': [106.0],
            'low': [105.0],
            'open': [105.2],
        })
        mock_bond_spot.return_value = mock_spot_data

        result = fetcher.get_convertible_realtime('113527')

        assert result is not None
        assert result['price'] == 105.5
        assert result['volume'] == 1000000
        assert result['change'] == 0.5

    @patch('akshare.bond_zh_hs_cov_spot')
    def test_get_convertible_realtime_api_error(self, mock_bond_spot, fetcher):
        """测试API调用失败"""
        mock_bond_spot.side_effect = Exception("Network error")

        result = fetcher.get_convertible_realtime('113527')

        assert result is None

    @patch('akshare.bond_zh_hs_cov_spot')
    def test_get_convertible_realtime_not_found(self, mock_bond_spot, fetcher):
        """测试转债代码不存在的情况"""
        mock_spot_data = pd.DataFrame({
            'code': ['113528', '113529'],
            'name': ['其他转债1', '其他转债2'],
            'trade': [100.0, 101.0],
            'changepercent': [0.0, 0.5],
            'volume': [500000, 600000],
            'amount': [50000000, 60600000],
            'high': [100.5, 101.5],
            'low': [99.5, 100.5],
            'open': [100.0, 101.0],
        })
        mock_bond_spot.return_value = mock_spot_data

        result = fetcher.get_convertible_realtime('113527')

        assert result is None

    @patch('akshare.bond_zh_hs_cov_daily')
    def test_get_convertible_history_success(self, mock_bond_daily, fetcher):
        """测试获取历史数据"""
        mock_history = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=30),
            'close': [100 + i for i in range(30)],
            'volume': [100000] * 30,
        })
        mock_bond_daily.return_value = mock_history

        result = fetcher.get_convertible_history('113527', days=30)

        assert result is not None
        assert len(result) == 30
        assert 'close' in result.columns

    def test_calculate_indicators(self, fetcher):
        """测试技术指标计算"""
        # 构造测试数据
        dates = pd.date_range('2025-01-01', periods=30)
        prices = [100 + i for i in range(30)]
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': [100000] * 30,
        })

        indicators = fetcher.calculate_indicators(df)

        assert 'ma5' in indicators
        assert 'ma20' in indicators
        assert 'volatility_20d' in indicators
        assert indicators['ma5'] > indicators['ma20']  # 上涨趋势
    @patch('akshare.bond_zh_hs_cov_daily')
    def test_get_convertible_history_empty_response(self, mock_bond_daily, fetcher):
        """测试API返回空数据"""
        mock_bond_daily.return_value = pd.DataFrame()
        result = fetcher.get_convertible_history('113527')
        assert result is None

    @patch('akshare.bond_zh_hs_cov_daily')
    def test_get_convertible_history_api_error(self, mock_bond_daily, fetcher):
        """测试API调用失败"""
        mock_bond_daily.side_effect = Exception("Network error")
        result = fetcher.get_convertible_history('113527')
        assert result is None

    def test_calculate_indicators_insufficient_data(self, fetcher):
        """测试数据不足时的指标计算"""
        df = pd.DataFrame({'close': [100, 101]})
        indicators = fetcher.calculate_indicators(df)
        assert 'ma5' not in indicators
        assert 'ma20' not in indicators
        assert 'trend_5d' not in indicators

    def test_get_convertible_history_invalid_cb_code(self, fetcher):
        """测试无效的可转债代码"""
        assert fetcher.get_convertible_history('') is None
        assert fetcher.get_convertible_history(None) is None

    def test_get_convertible_history_invalid_days(self, fetcher):
        """测试无效的天数参数"""
        assert fetcher.get_convertible_history('113527', days=0) is None
        assert fetcher.get_convertible_history('113527', days=-1) is None

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_by_name_exact_match(self, mock_bond_jsl, fetcher):
        """测试通过名称精确查找可转债代码"""
        mock_bond_jsl.return_value = pd.DataFrame({
            '代码': ['113527', '113050'],
            '转债名称': ['利民转债', '南银转债']
        })

        result = fetcher.get_convertible_by_name('利民转债')
        assert result == '113527'

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_by_name_fuzzy_match(self, mock_bond_jsl, fetcher):
        """测试通过名称模糊查找可转债代码"""
        mock_bond_jsl.return_value = pd.DataFrame({
            '代码': ['113527', '113050'],
            '转债名称': ['利民转债', '南银转债']
        })

        result = fetcher.get_convertible_by_name('利民')
        assert result == '113527'

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_by_name_not_found(self, mock_bond_jsl, fetcher):
        """测试查找不存在的可转债名称"""
        mock_bond_jsl.return_value = pd.DataFrame({
            '代码': ['113527'],
            '转债名称': ['利民转债']
        })

        result = fetcher.get_convertible_by_name('不存在')
        assert result is None

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_name_by_code(self, mock_bond_jsl, fetcher):
        """测试通过代码查找可转债名称"""
        mock_bond_jsl.return_value = pd.DataFrame({
            '代码': ['113527', '113050'],
            '转债名称': ['利民转债', '南银转债']
        })

        result = fetcher.get_convertible_name_by_code('113527')
        assert result == '利民转债'

    @patch('akshare.bond_cb_jsl')
    def test_get_convertible_name_by_code_not_found(self, mock_bond_jsl, fetcher):
        """测试查找不存在的可转债代码"""
        mock_bond_jsl.return_value = pd.DataFrame({
            '代码': ['113527'],
            '转债名称': ['利民转债']
        })

        result = fetcher.get_convertible_name_by_code('999999')
        assert result is None


class TestAKShareFetcherIndustryData:
    """测试行业数据获取功能"""

    @pytest.fixture
    def fetcher(self):
        return AKShareFetcher()

    @patch('akshare.stock_board_industry_hist_em')
    def test_get_industry_index_hist(self, mock_industry_hist, fetcher):
        """测试获取行业指数历史数据"""
        # Mock返回数据
        mock_data = pd.DataFrame({
            '日期': pd.date_range('2024-01-01', periods=60),
            '收盘': [100.0 + i for i in range(60)],
        })
        mock_industry_hist.return_value = mock_data

        df = fetcher.get_industry_index_hist("new_energy", days=60)

        assert df is not None
        assert not df.empty
        assert 'close' in df.columns
        assert len(df) <= 60  # 不应超过请求的天数
        mock_industry_hist.assert_called_once()

    @patch('akshare.stock_zh_index_daily')
    def test_get_benchmark_index_hist(self, mock_index_daily, fetcher):
        """测试获取基准指数历史数据"""
        # Mock返回数据
        mock_data = pd.DataFrame({
            '日期': pd.date_range('2024-01-01', periods=60),
            '收盘': [3000.0 + i for i in range(60)],
        })
        mock_index_daily.return_value = mock_data

        df = fetcher.get_benchmark_index_hist("000300", days=60)

        assert df is not None
        assert not df.empty
        assert 'close' in df.columns
        mock_index_daily.assert_called_once()

    @patch('akshare.stock_board_industry_name_em')
    def test_get_industry_list(self, mock_industry_list, fetcher):
        """测试获取行业列表"""
        # Mock返回数据
        mock_data = pd.DataFrame({
            '板块代码': ['BK0001', 'BK0002', 'BK0003'],
            '板块名称': ['电子', '化工', '机械设备'],
        })
        mock_industry_list.return_value = mock_data

        industries = fetcher.get_industry_list()

        assert industries is not None
        assert len(industries) > 0
        assert isinstance(industries[0], dict)
        assert 'industry_code' in industries[0] or 'name' in industries[0]
        mock_industry_list.assert_called_once()
