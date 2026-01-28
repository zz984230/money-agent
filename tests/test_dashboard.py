"""
Test Dashboard Module
测试 Streamlit 仪表板模块
"""

import os
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDashboard:
    """测试仪表板功能"""

    def test_dashboard_import(self):
        """测试仪表板模块导入"""
        from ui.dashboard import main, initialize_agent, get_analyzers
        assert main is not None
        assert initialize_agent is not None
        assert get_analyzers is not None

    def test_ui_module_import(self):
        """测试 ui 模块导入"""
        from ui import main
        assert main is not None

    def test_page_functions_exist(self):
        """测试页面函数存在"""
        from ui import dashboard

        # 检查所有页面渲染函数是否存在
        assert hasattr(dashboard, 'render_home_page')
        assert hasattr(dashboard, 'render_stock_screening_page')
        assert hasattr(dashboard, 'render_market_analysis_page')
        assert hasattr(dashboard, 'render_etf_analysis_page')
        assert hasattr(dashboard, 'render_convertible_analysis_page')

    def test_initialize_agent_without_api_key(self, monkeypatch):
        """测试在没有 API Key 时初始化 Agent"""
        # 临时移除 API key
        monkeypatch.setenv('GLM_API_KEY', '')

        from ui.dashboard import initialize_agent

        # 应该返回 None 或抛出异常
        result = initialize_agent()
        # 由于没有 API key，应该返回 None
        assert result is None

    def test_streamlit_config(self):
        """测试 Streamlit 配置"""
        from ui.dashboard import st

        # 检查页面配置
        assert st is not None


@pytest.mark.integration
class TestDashboardIntegration:
    """集成测试 - 需要 API Key"""

    @pytest.fixture(scope="class")
    def agent(self):
        """初始化 Agent (需要有效的 API Key)"""
        from ui.dashboard import initialize_agent

        import os
        if not os.getenv('GLM_API_KEY'):
            pytest.skip("需要 GLM_API_KEY 环境变量")

        agent = initialize_agent()
        return agent

    def test_agent_initialization(self, agent):
        """测试 Agent 初始化"""
        assert agent is not None

    def test_analyzers_initialization(self, agent):
        """测试分析器初始化"""
        from ui.dashboard import get_analyzers

        screener, market_analyzer, etf_analyzer, cb_analyzer = get_analyzers(agent)

        assert screener is not None
        assert market_analyzer is not None
        assert etf_analyzer is not None
        assert cb_analyzer is not None

        # 检查类型
        from analysis.screening import StockScreener
        from analysis.market_analysis import MarketAnalyzer
        from analysis.etf_analysis import ETFAnalyzer
        from analysis.convertible_analysis import ConvertibleBondAnalyzer

        assert isinstance(screener, StockScreener)
        assert isinstance(market_analyzer, MarketAnalyzer)
        assert isinstance(etf_analyzer, ETFAnalyzer)
        assert isinstance(cb_analyzer, ConvertibleBondAnalyzer)


@pytest.mark.skipif(
    not os.getenv('GLM_API_KEY'),
    reason="需要 GLM_API_KEY 环境变量"
)
class TestDashboardWithRealAPI:
    """使用真实 API 的测试"""

    def test_stock_screening_integration(self):
        """测试选股筛选功能集成"""
        from ui.dashboard import initialize_agent, get_analyzers

        agent = initialize_agent()
        if agent is None:
            pytest.skip("无法初始化 Agent")

        screener, _, _, _ = get_analyzers(agent)
        if screener is None:
            pytest.skip("无法初始化 StockScreener")

        # 测试简单的筛选条件
        criteria = {"pe": {"max": 50}}
        result = screener.screen_stocks(criteria, top_n=5)

        assert result is not None
        assert "stocks" in result
        assert "reasoning" in result
        assert isinstance(result["stocks"], list)

    def test_etf_recommendation_integration(self):
        """测试 ETF 推荐功能集成"""
        from ui.dashboard import initialize_agent, get_analyzers

        agent = initialize_agent()
        if agent is None:
            pytest.skip("无法初始化 Agent")

        _, _, etf_analyzer, _ = get_analyzers(agent)
        if etf_analyzer is None:
            pytest.skip("无法初始化 ETFAnalyzer")

        # 测试获取 ETF 列表
        etf_list = etf_analyzer.get_etf_list()
        assert etf_list is not None
        assert isinstance(etf_list, list)


if __name__ == "__main__":
    # 运行基本测试
    test = TestDashboard()

    print("Running dashboard import test...")
    test.test_dashboard_import()
    print("✓ Dashboard import test passed")

    print("\nRunning ui module import test...")
    test.test_ui_module_import()
    print("✓ UI module import test passed")

    print("\nRunning page functions test...")
    test.test_page_functions_exist()
    print("✓ Page functions test passed")

    print("\nRunning Streamlit config test...")
    test.test_streamlit_config()
    print("✓ Streamlit config test passed")

    print("\n" + "=" * 50)
    print("All basic tests passed!")
    print("=" * 50)
