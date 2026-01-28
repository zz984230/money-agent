import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import pandas as pd

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetchers.tushare_fetcher import TushareFetcher


class TestTushareFetcher:
    """TushareFetcher 单元测试"""

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_init_success(self, mock_pro_api):
        """测试成功初始化"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api

        fetcher = TushareFetcher(token="test_token")
        assert fetcher.token == "test_token"
        assert fetcher.ts_api == mock_api
        mock_pro_api.assert_called_once_with("test_token")

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    @patch('config.settings.settings')
    def test_init_from_settings(self, mock_settings, mock_pro_api):
        """测试从环境变量读取 Token 初始化"""
        mock_settings.tushare_token = "env_token"
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api

        fetcher = TushareFetcher()
        assert fetcher.token == "env_token"
        mock_pro_api.assert_called_once_with("env_token")

    def test_init_no_token(self):
        """测试没有 Token 时初始化失败"""
        with patch('config.settings.settings') as mock_settings:
            mock_settings.tushare_token = ""
            with pytest.raises(ValueError, match="Tushare Token 未提供"):
                TushareFetcher()

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_get_latest_financials_success(self, mock_pro_api):
        """测试成功获取最新财务数据"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api

        # Mock 利润表数据
        mock_income_df = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'ann_date': ['2024-04-25'],
            'end_date': ['2024-03-31'],
            'report_type': ['一季报'],
            'basic_eps': [0.5],
            'revenue': [500000000],
            'operate_profit': [100000000],
            'n_income': [80000000]
        })
        mock_api.income.return_value = mock_income_df

        # Mock 资产负债表数据
        mock_balance_df = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'ann_date': ['2024-04-25'],
            'end_date': ['2024-03-31'],
            'report_type': ['一季报'],
            'total_assets': [2000000000],
            'total_hldr_eqy_exc_min_int': [1000000000]
        })
        mock_api.balancesheet.return_value = mock_balance_df

        # Mock 现金流量表数据
        mock_cashflow_df = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'ann_date': ['2024-04-25'],
            'end_date': ['2024-03-31'],
            'report_type': ['一季报'],
            'n_cashflow_act': [50000000],
            'n_cashflow_inv_act': [-30000000],
            'n_cash_flows_fnc_act': [-10000000]
        })
        mock_api.cashflow.return_value = mock_cashflow_df

        fetcher = TushareFetcher(token="test_token")
        result = fetcher.get_latest_financials("688798.SH")

        assert result is not None
        assert 'latest_income' in result
        assert 'latest_balance' in result
        assert 'latest_cashflow' in result
        assert result['report_date'] == '2024-03-31'

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_get_latest_financials_empty_income(self, mock_pro_api):
        """测试利润表数据为空时抛出异常"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api
        mock_api.income.return_value = pd.DataFrame()

        fetcher = TushareFetcher(token="test_token")
        with pytest.raises(RuntimeError, match="未能获取.*的利润表数据"):
            fetcher.get_latest_financials("688798.SH")

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_get_latest_financials_empty_balance(self, mock_pro_api):
        """测试资产负债表数据为空时抛出异常"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api

        # 利润表有数据
        mock_api.income.return_value = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'end_date': ['2024-03-31']
        })
        # 资产负债表为空
        mock_api.balancesheet.return_value = pd.DataFrame()

        fetcher = TushareFetcher(token="test_token")
        with pytest.raises(RuntimeError, match="未能获取.*的资产负债表数据"):
            fetcher.get_latest_financials("688798.SH")

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_get_latest_financials_empty_cashflow(self, mock_pro_api):
        """测试现金流量表数据为空时抛出异常"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api

        # 利润表和资产负债表有数据
        mock_api.income.return_value = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'end_date': ['2024-03-31']
        })
        mock_api.balancesheet.return_value = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'end_date': ['2024-03-31']
        })
        # 现金流量表为空
        mock_api.cashflow.return_value = pd.DataFrame()

        fetcher = TushareFetcher(token="test_token")
        with pytest.raises(RuntimeError, match="未能获取.*的现金流量表数据"):
            fetcher.get_latest_financials("688798.SH")

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_get_basic_info_success(self, mock_pro_api):
        """测试成功获取基本信息"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api

        mock_df = pd.DataFrame({
            'ts_code': ['688798.SH'],
            'name': ['艾为电子'],
            'area': ['上海'],
            'industry': ['电子'],
            'market': ['科创板'],
            'list_date': ['2021-08-16']
        })
        mock_api.stock_basic.return_value = mock_df

        fetcher = TushareFetcher(token="test_token")
        result = fetcher.get_basic_info("688798.SH")

        assert result is not None
        assert result['name'] == '艾为电子'
        assert result['industry'] == '电子'

    @patch('data.fetchers.tushare_fetcher.ts.pro_api')
    def test_get_basic_info_empty(self, mock_pro_api):
        """测试基本信息为空时抛出异常"""
        mock_api = MagicMock()
        mock_pro_api.return_value = mock_api
        mock_api.stock_basic.return_value = pd.DataFrame()

        fetcher = TushareFetcher(token="test_token")
        with pytest.raises(RuntimeError, match="未能获取.*的基本信息"):
            fetcher.get_basic_info("688798.SH")

    def test_stock_code_to_ts_code_sh(self):
        """测试上交所股票代码转换"""
        assert TushareFetcher.stock_code_to_ts_code("688798") == "688798.SH"
        assert TushareFetcher.stock_code_to_ts_code("600000") == "600000.SH"

    def test_stock_code_to_ts_code_sz(self):
        """测试深交所股票代码转换"""
        assert TushareFetcher.stock_code_to_ts_code("000001") == "000001.SZ"
        assert TushareFetcher.stock_code_to_ts_code("300001") == "300001.SZ"

    def test_stock_code_to_ts_code_bj(self):
        """测试北交所股票代码转换"""
        assert TushareFetcher.stock_code_to_ts_code("832566") == "832566.BJ"

    def test_stock_code_to_ts_code_with_suffix(self):
        """测试带后缀的股票代码转换"""
        assert TushareFetcher.stock_code_to_ts_code("688798.SH") == "688798.SH"
        assert TushareFetcher.stock_code_to_ts_code("000001.SZ") == "000001.SZ"

    def test_stock_code_to_ts_code_invalid(self):
        """测试无效股票代码"""
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            TushareFetcher.stock_code_to_ts_code("123")

        with pytest.raises(ValueError, match="无效的股票代码格式"):
            TushareFetcher.stock_code_to_ts_code("abcdef")

        with pytest.raises(ValueError, match="股票代码不能为空"):
            TushareFetcher.stock_code_to_ts_code("")
