"""
测试可转债技术面分析模块
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict
from datetime import datetime, timedelta
import pandas as pd

from analysis.convertible_technical_analysis import (
    ConvertibleTechnicalData,
    TechnicalAnalysisResult,
    ConvertibleBondTechnicalAnalyzer
)


class TestConvertibleTechnicalData:
    """测试ConvertibleTechnicalData数据类"""

    def test_create_minimal_data(self):
        """测试创建最小数据集"""
        data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[],
            ask_price=[],
            bid_volume=[],
            ask_volume=[],
            ma5=0.0,
            ma20=0.0,
            volatility_20d=0.0,
        )

        assert data.cb_code == "113527"
        assert data.price == 105.5
        assert data.premium_rate == 15.5

    def test_data_serialization(self):
        """测试数据序列化"""
        data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[104.5, 104.4],
            ask_price=[105.5, 105.6],
            bid_volume=[1000, 2000],
            ask_volume=[1000, 2000],
            ma5=104.5,
            ma20=103.0,
            volatility_20d=2.5,
        )

        result = asdict(data)

        assert isinstance(result, dict)
        assert result['cb_code'] == "113527"
        assert len(result['bid_price']) == 2


class TestTechnicalAnalysisResult:
    """测试TechnicalAnalysisResult数据类"""

    def test_create_result(self):
        """测试创建分析结果"""
        technical_data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[],
            ask_price=[],
            bid_volume=[],
            ask_volume=[],
            ma5=0.0,
            ma20=0.0,
            volatility_20d=0.0,
        )

        result = TechnicalAnalysisResult(
            technical_data=technical_data,
            analysis="这是AI分析结果",
            signals=["看涨", "低溢价"],
            summary="分析摘要",
            recommendation="买入"
        )

        assert result.technical_data.cb_code == "113527"
        assert result.analysis == "这是AI分析结果"
        assert len(result.signals) == 2
        assert result.recommendation == "买入"


class TestConvertibleBondTechnicalAnalyzer:
    """测试ConvertibleBondTechnicalAnalyzer类"""

    @pytest.fixture
    def mock_agent(self):
        """创建mock agent"""
        agent = Mock()
        agent.chat = Mock(return_value="## 技术面分析\n\n价格走势：上涨\n\n**信号**：看涨, 低溢价\n\n**建议**：买入\n\n**摘要**：该转债技术面良好，建议买入。")
        return agent

    @pytest.fixture
    def mock_fetcher(self):
        """创建mock fetcher"""
        fetcher = Mock()

        # Mock get_convertible_daily - 历史数据
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        history_df = pd.DataFrame({
            'date': dates,
            'close': [100 + i * 0.5 for i in range(30)],
            'volume': [1000000] * 30,
        })
        fetcher.get_convertible_daily = Mock(return_value=history_df)

        return fetcher

    @pytest.fixture
    def analyzer(self, mock_agent, mock_fetcher):
        """创建analyzer实例"""
        with patch('analysis.convertible_technical_analysis.AKShareFetcher', return_value=mock_fetcher):
            return ConvertibleBondTechnicalAnalyzer(mock_agent)

    def test_initialization(self, mock_agent):
        """测试初始化"""
        with patch('analysis.convertible_technical_analysis.AKShareFetcher'):
            analyzer = ConvertibleBondTechnicalAnalyzer(mock_agent)
            assert analyzer.agent == mock_agent
            assert analyzer.prompt_builder is not None
            assert analyzer.fetcher is not None

    def test_analyze_technical_success(self, analyzer, mock_fetcher):
        """测试成功的技术分析"""
        result = analyzer.analyze_technical("113527", "利民转债")

        assert result is not None
        assert isinstance(result, TechnicalAnalysisResult)
        assert result.technical_data.cb_code == "113527"
        assert result.technical_data.cb_name == "利民转债"
        assert result.analysis is not None
        assert len(result.signals) > 0
        assert result.recommendation is not None
        assert result.summary is not None

    def test_analyze_technical_with_empty_code(self, analyzer):
        """测试空代码的处理"""
        result = analyzer.analyze_technical("", "利民转债")
        assert result is None

    def test_analyze_technical_with_empty_name(self, analyzer):
        """测试空名称的处理"""
        result = analyzer.analyze_technical("113527", "")
        assert result is None

    def test_analyze_technical_ai_failure(self, analyzer, mock_agent):
        """测试AI分析失败的处理"""
        mock_agent.chat = Mock(return_value=None)

        result = analyzer.analyze_technical("113527", "利民转债")

        # AI分析失败应该返回None
        assert result is None

    def test_analyze_technical_fetcher_failure(self, analyzer, mock_fetcher):
        """测试数据获取失败的处理"""
        mock_fetcher.get_convertible_daily = Mock(side_effect=Exception("Network error"))

        result = analyzer.analyze_technical("113527", "利民转债")

        # 应该降级到AI-only模式
        assert result is not None
        assert result.technical_data is not None

    def test_extract_signals(self, analyzer):
        """测试信号提取"""
        analysis = """
        ## 技术分析

        价格走势良好，成交量放大。

        **交易信号**：看涨, 低溢价, 强势

        **建议**：买入
        """

        signals = analyzer._extract_signals(analysis)
        assert isinstance(signals, list)
        assert len(signals) > 0
        # 应该包含一些信号
        assert any("看涨" in signal or "低溢价" in signal for signal in signals)

    def test_extract_summary(self, analyzer):
        """测试摘要提取"""
        analysis = "这是一段很长的分析文本" * 50

        summary = analyzer._extract_summary(analysis)

        assert isinstance(summary, str)
        assert len(summary) <= 200

    def test_extract_recommendation(self, analyzer):
        """测试建议提取"""
        analysis = """
        ## 分析结果

        综合分析后建议：**买入**

        风险提示：注意市场波动
        """

        recommendation = analyzer._extract_recommendation(analysis)

        assert isinstance(recommendation, str)
        assert len(recommendation) > 0

    def test_build_technical_data_with_history(self, analyzer, mock_fetcher):
        """测试从历史数据构建技术数据"""
        mock_fetcher.get_convertible_daily = Mock(return_value=pd.DataFrame({
            'date': pd.date_range(end=datetime.now(), periods=30, freq='D'),
            'close': [100 + i * 0.5 for i in range(30)],
            'volume': [1000000] * 30,
        }))

        data = analyzer._build_technical_data("113527", "利民转债")

        assert data is not None
        assert data.cb_code == "113527"
        assert data.cb_name == "利民转债"
        assert data.ma5 > 0 or data.ma20 > 0  # 应该计算了均线

    def test_build_technical_data_empty_history(self, analyzer, mock_fetcher):
        """测试空历史数据的处理"""
        mock_fetcher.get_convertible_daily = Mock(return_value=pd.DataFrame())

        data = analyzer._build_technical_data("113527", "利民转债")

        assert data is not None
        assert data.cb_code == "113527"
        # 应该使用默认值
        assert data.ma5 == 0.0

    def test_analyze_terms_call_trigger(self, analyzer, monkeypatch):
        """测试强赎条款触发分析"""
        # Mock fetcher.get_convertible_detail 返回转债详情
        monkeypatch.setattr(analyzer.fetcher, 'get_convertible_detail',
                           lambda x: {
                               'cb_code': '113527',
                               'cb_name': '利民转债',
                               'call_trigger_price': 130.0,
                               'put_trigger_price': 90.0,
                               'conversion_price': 100.0,
                           })

        # 正股价超过强赎触发价
        result = analyzer.analyze_terms('113527', stock_price=135.0, stock_name='利民股份')

        assert result is not None
        assert result['cb_code'] == '113527'
        assert '强赎' in result['full_analysis'] or 'call_distance' in result
        assert result['call_distance'] > 0  # 应该是正数（超过触发价）

    def test_analyze_terms_put_trigger(self, analyzer, monkeypatch):
        """测试回售条款触发分析"""
        monkeypatch.setattr(analyzer.fetcher, 'get_convertible_detail',
                           lambda x: {
                               'cb_code': '113527',
                               'cb_name': '利民转债',
                               'call_trigger_price': 130.0,
                               'put_trigger_price': 90.0,
                               'conversion_price': 100.0,
                           })

        # 正股价低于回售触发价
        result = analyzer.analyze_terms('113527', stock_price=85.0, stock_name='利民股份')

        assert result is not None
        assert result['put_distance'] < 0  # 应该是负数（低于触发价）

    def test_analyze_terms_not_found(self, analyzer, monkeypatch):
        """测试转债不存在的情况"""
        monkeypatch.setattr(analyzer.fetcher, 'get_convertible_detail', lambda x: None)

        result = analyzer.analyze_terms('999999', stock_price=100.0)

        assert result is None

    def test_screen_by_technical_price_filter(self, analyzer, monkeypatch):
        """测试价格筛选"""
        # Mock 可转债列表
        mock_list = [
            {'cb_code': '113001', 'cb_name': '平煤转债', 'price': 105, 'change': 2, 'amount': 50000000},
            {'cb_code': '113002', 'cb_name': '神马转债', 'price': 115, 'change': 5, 'amount': 30000000},
            {'cb_code': '113003', 'cb_name': '韦尔转债', 'price': 95, 'change': 1, 'amount': 100000000},
        ]
        monkeypatch.setattr(analyzer.fetcher, 'get_convertible_list', lambda: mock_list)

        criteria = {
            "price_range": (100, 110),
            "premium_max": 15,
        }

        results = analyzer.screen_by_technical(criteria, top_n=10)

        assert results is not None
        assert len(results) == 1  # 只有平煤转债符合（价格105，涨跌幅2）
        assert results[0]['cb_code'] == '113001'

    def test_screen_by_technical_empty_result(self, analyzer, monkeypatch):
        """测试无符合条件结果"""
        monkeypatch.setattr(analyzer.fetcher, 'get_convertible_list', lambda: [])

        results = analyzer.screen_by_technical({"price_range": (90, 110)})

        assert results == []

    def test_screen_by_technical_with_liquidity_filter(self, analyzer, monkeypatch):
        """测试流动性筛选"""
        mock_list = [
            {'cb_code': '113001', 'cb_name': '平煤转债', 'price': 105, 'change': 2, 'amount': 50000000},  # 5000万
            {'cb_code': '113004', 'cb_name': '隆基转债', 'price': 102, 'change': 3, 'amount': 150000000},  # 1.5亿
        ]
        monkeypatch.setattr(analyzer.fetcher, 'get_convertible_list', lambda: mock_list)

        criteria = {
            "price_range": (100, 110),
            "liquidity_min": 100000000,  # 要求成交额 >= 1亿
        }

        results = analyzer.screen_by_technical(criteria, top_n=10)

        assert len(results) == 1
        assert results[0]['cb_code'] == '113004'  # 只有隆基转债符合流动性要求

    def test_calculate_screen_score(self, analyzer):
        """测试评分计算"""
        cb = {
            'price': 105,
            'change': 5,
            'amount': 80000000,  # 8000万
        }
        criteria = {"price_range": (100, 110)}

        score = analyzer._calculate_screen_score(cb, criteria)

        # 价格在范围内 +50分，溢价率-5分，流动性+10分
        assert score == 55  # 50 - 5 + 10
