"""
Convertible Bond Analysis Module Tushare Integration Tests
可转债分析模块 Tushare 集成测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from analysis.convertible_analysis import ConvertibleBondAnalyzer
from core.agent.base_agent import BaseAgent
import pandas as pd


@pytest.fixture
def mock_agent():
    """创建模拟的Agent"""
    agent = Mock(spec=BaseAgent)
    return agent


@pytest.fixture
def analyzer(mock_agent):
    """创建ConvertibleBondAnalyzer实例"""
    with patch('analysis.convertible_analysis.AKShareFetcher'):
        return ConvertibleBondAnalyzer(mock_agent)


class TestTushareIntegration:
    """Tushare 集成测试"""

    @patch('analysis.convertible_analysis.TushareFetcher')
    def test_analyze_convertible_with_tushare_success(self, mock_tushare_cls, analyzer, mock_agent):
        """测试 Tushare 成功获取财务数据的场景"""
        # 模拟可转债列表数据
        mock_cb_list = [{
            'cb_code': '113050',
            'cb_name': '南银转债',
            'price': 105.5,
            'change': 0.5,
            'stock_code': '601009',  # 正股代码
            'stock_name': '南京银行'
        }]

        # 模拟 TushareFetcher 实例和方法
        mock_tushare = MagicMock()
        mock_tushare_cls.return_value = mock_tushare_cls
        mock_tushare_cls.stock_code_to_ts_code.return_value = '601009.SH'
        mock_tushare_cls.return_value.get_latest_financials.return_value = {
            'latest_income': {'revenue': 500000000, 'n_income': 100000000},
            'latest_balance': {'total_assets': 2000000000},
            'latest_cashflow': {'n_cashflow_act': 50000000},
            'report_date': '2024-09-30'
        }

        # 模拟 AI 分析响应
        mock_agent.chat.return_value = "南银转债分析报告..."

        # Mock get_convertible_list 返回可转债列表
        with patch.object(analyzer, 'get_convertible_list', return_value=mock_cb_list):
            result = analyzer.analyze_convertible(cb_code="113050", cb_name="南银转债")

            # 验证结果
            assert result is not None
            assert result["cb_code"] == "113050"
            assert result["cb_name"] == "南银转债"
            # 不应该包含 error 字段（因为成功）
            assert "error" not in result
            assert mock_agent.chat.called

    @patch('analysis.convertible_analysis.TushareFetcher')
    def test_analyze_convertible_tushare_failure(self, mock_tushare_cls, analyzer, mock_agent):
        """测试 Tushare 失败时直接返回错误的场景"""
        # 模拟可转债列表数据
        mock_cb_list = [{
            'cb_code': '113050',
            'cb_name': '南银转债',
            'price': 105.5,
            'change': 0.5,
            'stock_code': '601009',
            'stock_name': '南京银行'
        }]

        # 模拟 TushareFetcher 初始化失败（没有 token）
        mock_tushare_cls.side_effect = ValueError("Tushare Token 未提供")

        # Mock get_convertible_list 返回可转债列表
        with patch.object(analyzer, 'get_convertible_list', return_value=mock_cb_list):
            result = analyzer.analyze_convertible(cb_code="113050", cb_name="南银转债")

            # 验证返回了错误
            assert result is not None
            assert result.get("error") is not None
            # AI 不应该被调用
            assert not mock_agent.chat.called

    @patch('analysis.convertible_analysis.TushareFetcher')
    def test_analyze_convertible_tushare_api_error(self, mock_tushare_cls, analyzer, mock_agent):
        """测试 Tushare API 调用失败的场景"""
        # 模拟可转债列表数据
        mock_cb_list = [{
            'cb_code': '113050',
            'cb_name': '南银转债',
            'price': 105.5,
            'change': 0.5,
            'stock_code': '601009',
            'stock_name': '南京银行'
        }]

        # 模拟 TushareFetcher 实例
        mock_tushare = MagicMock()
        mock_tushare_cls.return_value = mock_tushare_cls
        mock_tushare_cls.stock_code_to_ts_code.return_value = '601009.SH'
        # API 调用失败
        mock_tushare_cls.return_value.get_latest_financials.side_effect = RuntimeError(
            "获取 Tushare 财务数据失败: API 请求超时"
        )

        # Mock get_convertible_list 返回可转债列表
        with patch.object(analyzer, 'get_convertible_list', return_value=mock_cb_list):
            result = analyzer.analyze_convertible(cb_code="113050", cb_name="南银转债")

            # 验证返回了错误
            assert result is not None
            assert result.get("error") is not None
            assert "Tushare" in result.get("summary", "")
            # AI 不应该被调用
            assert not mock_agent.chat.called

    @patch('analysis.convertible_analysis.TushareFetcher')
    def test_analyze_convertible_no_stock_code(self, mock_tushare_cls, analyzer, mock_agent):
        """测试可转债没有正股代码的场景（不调用 Tushare）"""
        # 模拟可转债列表数据（没有正股代码）
        mock_cb_list = [{
            'cb_code': '113050',
            'cb_name': '南银转债',
            'price': 105.5,
            'change': 0.5,
            'stock_code': '',  # 空的正股代码
            'stock_name': ''
        }]

        # 模拟 AI 分析响应
        mock_agent.chat.return_value = "南银转债分析报告..."

        # Mock get_convertible_list 返回可转债列表
        with patch.object(analyzer, 'get_convertible_list', return_value=mock_cb_list):
            result = analyzer.analyze_convertible(cb_code="113050", cb_name="南银转债")

            # 验证结果
            assert result is not None
            assert result["cb_code"] == "113050"
            # 不应该包含 error 字段（因为没有正股代码，跳过 Tushare）
            assert "error" not in result
            assert mock_agent.chat.called
            # Tushare 不应该被调用
            assert not mock_tushare_cls.called

    @patch('analysis.convertible_analysis.TushareFetcher')
    def test_ensure_tushare_fetcher_initialized_once(self, mock_tushare_cls, analyzer):
        """测试 TushareFetcher 只初始化一次"""
        mock_tushare = MagicMock()
        mock_tushare_cls.return_value = mock_tushare_cls
        mock_tushare_cls.stock_code_to_ts_code.return_value = '601009.SH'
        mock_tushare_cls.return_value.get_latest_financials.return_value = {
            'report_date': '2024-09-30'
        }

        # 模拟可转债列表数据
        mock_cb_list = [{
            'cb_code': '113050',
            'cb_name': '南银转债',
            'price': 105.5,
            'change': 0.5,
            'stock_code': '601009',
            'stock_name': '南京银行'
        }]

        with patch.object(analyzer, 'get_convertible_list', return_value=mock_cb_list):
            # 第一次调用 - 应该初始化
            analyzer._ensure_tushare_fetcher()
            assert analyzer.tushare_fetcher is not None

            # 第二次调用 - 不应该重新初始化
            mock_tushare_cls.reset_mock()
            analyzer._ensure_tushare_fetcher()
            # TushareFetcher 构造函数不应该被再次调用
            assert not mock_tushare_cls.called

    def test_stock_code_to_ts_code_conversion(self):
        """测试股票代码转换"""
        from data.fetchers.tushare_fetcher import TushareFetcher

        # 测试上交所
        assert TushareFetcher.stock_code_to_ts_code("688798") == "688798.SH"
        assert TushareFetcher.stock_code_to_ts_code("600000") == "600000.SH"

        # 测试深交所
        assert TushareFetcher.stock_code_to_ts_code("000001") == "000001.SZ"
        assert TushareFetcher.stock_code_to_ts_code("300001") == "300001.SZ"

        # 测试北交所
        assert TushareFetcher.stock_code_to_ts_code("832566") == "832566.BJ"

    @patch('analysis.convertible_analysis.TushareFetcher')
    def test_analyze_convertible_ai_only_mode(self, mock_tushare_cls, analyzer, mock_agent):
        """测试 use_ai_only 模式（不调用 Tushare）"""
        # 模拟 AI 分析响应
        mock_agent.chat.return_value = "集智转债分析报告..."

        # 执行分析（use_ai_only=True）
        result = analyzer.analyze_convertible(
            cb_code="未知",
            cb_name="集智转债",
            use_ai_only=True
        )

        # 验证结果
        assert result is not None
        assert result["cb_code"] == "未知"
        assert result["cb_name"] == "集智转债"
        assert mock_agent.chat.called
        # Tushare 不应该被调用
        assert not mock_tushare_cls.called
