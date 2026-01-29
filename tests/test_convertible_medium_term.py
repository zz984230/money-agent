"""测试可转债中期量化分析器"""
import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
from analysis.convertible_medium_term import ConvertibleBondMediumTermAnalyzer


def test_screen_top_industries():
    """测试筛选强势行业"""
    agent = Mock()
    analyzer = ConvertibleBondMediumTermAnalyzer(agent)

    # Mock数据获取
    analyzer.fetcher.get_industry_list = Mock(return_value=[
        {'industry_code': 'test1', 'name': '测试行业1'},
        {'industry_code': 'test2', 'name': '测试行业2'},
    ])

    # Mock行业指数数据
    analyzer.fetcher.get_industry_index_hist = Mock(side_effect=[
        pd.DataFrame({'date': pd.date_range('2024-01-01', periods=60), 'close': [100 + i for i in range(60)]}),
        pd.DataFrame({'date': pd.date_range('2024-01-01', periods=60), 'close': [100 + i*0.5 for i in range(60)]}),
    ])

    analyzer.fetcher.get_benchmark_index_hist = Mock(
        return_value=pd.DataFrame({'date': pd.date_range('2024-01-01', periods=60), 'close': [100 + i*0.3 for i in range(60)]})
    )

    results = analyzer.screen_top_industries(top_n=5)

    assert results is not None
    assert len(results) <= 5
    assert len(results) > 0


def test_medium_term_screen():
    """测试完整的中期量化筛选流程"""
    agent = Mock()
    analyzer = ConvertibleBondMediumTermAnalyzer(agent)

    # 设置返回数据
    analyzer.screen_top_industries = Mock(return_value=[
        Mock(industry_code='test1', industry_name='测试行业1', momentum_60d=20, momentum_120d=18, relative_strength=50, volume_ratio=0.1)
    ])

    analyzer.fetcher.get_convertible_by_industry = Mock(return_value=[
        {'cb_code': '123456', 'cb_name': '测试转债', 'stock_code': '600000', 'stock_name': '测试正股'}
    ])

    # Mock agent.chat
    agent.chat = Mock(return_value="## 投资建议\n建议关注测试行业的优质转债。")

    # Mock fetcher.get_convertible_detail
    analyzer.fetcher.get_convertible_detail = Mock(return_value={
        'premium_rate': 10.0,
        'conversion_value': 110.0,
        'ytm': 1.5
    })

    results = analyzer.medium_term_screen(top_n_industries=3, top_n_bonds=3)

    assert results is not None
    assert hasattr(results, 'bonds')
    assert hasattr(results, 'ai_analysis')
    assert len(results.bonds) > 0


@pytest.mark.integration
def test_full_medium_term_workflow():
    """完整的中期量化集成测试（需要真实API）"""
    from core.agent.glm_agent import GLMAgent
    from analysis.convertible_medium_term import ConvertibleBondMediumTermAnalyzer

    agent = GLMAgent()
    analyzer = ConvertibleBondMediumTermAnalyzer(agent)

    result = analyzer.medium_term_screen(
        top_n_industries=3,
        top_n_bonds=3,
        premium_max=30.0
    )

    assert result is not None
    assert len(result.industries) > 0
    assert len(result.bonds) > 0
