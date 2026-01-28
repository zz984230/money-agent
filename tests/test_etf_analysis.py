"""
ETF Analysis Module Tests
ETF分析模块测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from analysis.etf_analysis import ETFAnalyzer
from core.agent.base_agent import BaseAgent
import pandas as pd


@pytest.fixture
def mock_agent():
    """创建模拟的Agent"""
    agent = Mock(spec=BaseAgent)
    return agent


@pytest.fixture
def analyzer(mock_agent):
    """创建ETFAnalyzer实例"""
    with patch('analysis.etf_analysis.AKShareFetcher'):
        return ETFAnalyzer(mock_agent)


def test_analyze_etf(analyzer, mock_agent):
    """测试ETF分析功能"""
    # 模拟ETF历史数据
    mock_df = pd.DataFrame({
        'date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'open': [4.500, 4.520, 4.510],
        'close': [4.520, 4.510, 4.530],
        'high': [4.530, 4.525, 4.540],
        'low': [4.490, 4.505, 4.500],
        'volume': [150000000, 140000000, 160000000],
        'amount': [680000000, 630000000, 720000000]
    })

    # 模拟AI分析响应
    mock_response = """沪深300ETF分析报告：

1. ETF基本信息
   - 基金代码：510300
   - 基金名称：沪深300ETF
   - 跟踪标的：沪深300指数
   - 基金规模：大型

2. 历史业绩表现
   - 近三日净值稳步上涨，从4.500元升至4.530元
   - 整体走势稳健，呈现缓慢上升态势
   - 波动率相对较低，适合长期投资

3. 持仓结构分析
   - 主要配置沪深300指数成分股
   - 行业分布均衡，金融、科技、消费占比较高
   - 权重股集中度适中

4. 流动性分析
   - 日均成交额约7亿元，流动性充裕
   - 买卖价差较小，交易成本低
   - 适合大额资金进出

5. 适合的投资场景
   - 长期资产配置
   - 指数化投资
   - 分散投资风险

6. 风险提示
   - 跟踪指数的系统性风险
   - 市场波动风险
   - 流动性风险（极端市场情况下）"""

    # 设置mock返回值
    with patch.object(analyzer.fetcher, 'get_etf_daily') as mock_get_etf:
        mock_get_etf.return_value = mock_df
        mock_agent.chat.return_value = mock_response

        # 执行分析
        result = analyzer.analyze_etf(etf_code="510300", etf_name="沪深300ETF")

        # 验证结果
        assert result is not None
        assert result["etf_code"] == "510300"
        assert result["etf_name"] == "沪深300ETF"
        assert "data" in result
        assert "analysis" in result
        assert "summary" in result
        assert len(result["summary"]) <= 200
        assert "沪深300ETF" in result["analysis"]
        assert mock_get_etf.called
        assert mock_agent.chat.called


def test_analyze_etf_empty_data(analyzer, mock_agent):
    """测试ETF分析时数据为空的情况"""
    # 模拟空数据
    mock_df = pd.DataFrame()

    # 重置mock以清除之前的调用
    mock_agent.reset_mock()

    with patch.object(analyzer.fetcher, 'get_etf_daily') as mock_get_etf:
        mock_get_etf.return_value = mock_df

        # 执行分析
        result = analyzer.analyze_etf(etf_code="510300", etf_name="沪深300ETF")

        # 验证返回None
        assert result is None
        # 验证agent.chat没有被调用（因为数据为空）
        assert not mock_agent.chat.called


def test_get_etf_list(analyzer):
    """测试获取ETF列表功能"""
    # 模拟ETF列表数据
    mock_etf_list = [
        {"代码": "510300", "名称": "沪深300ETF", "类别": "宽基"},
        {"代码": "510500", "名称": "中证500ETF", "类别": "宽基"},
        {"代码": "159915", "名称": "创业板ETF", "类别": "宽基"},
        {"代码": "512690", "名称": "券商ETF", "类别": "行业"},
        {"代码": "515050", "名称": "科技ETF", "类别": "行业"}
    ]

    # 设置mock返回值
    with patch.object(analyzer.fetcher, 'get_etf_list') as mock_get_list:
        mock_get_list.return_value = mock_etf_list

        # 执行获取
        result = analyzer.get_etf_list()

        # 验证结果
        assert result is not None
        assert len(result) == 5
        assert result[0]["etf_code"] == "510300"
        assert result[0]["etf_name"] == "沪深300ETF"
        assert mock_get_list.called


def test_get_etf_list_empty(analyzer):
    """测试获取ETF列表为空的情况"""
    # 模拟空列表
    with patch.object(analyzer.fetcher, 'get_etf_list') as mock_get_list:
        mock_get_list.return_value = []

        # 执行获取
        result = analyzer.get_etf_list()

        # 验证返回None
        assert result is None
        assert mock_get_list.called


def test_recommend_etfs(analyzer, mock_agent):
    """测试ETF推荐功能"""
    # 模拟ETF列表数据
    mock_etf_list = [
        {"代码": "510300", "名称": "沪深300ETF", "类别": "宽基"},
        {"代码": "510500", "名称": "中证500ETF", "类别": "宽基"},
        {"代码": "159915", "名称": "创业板ETF", "类别": "宽基"},
        {"代码": "512690", "名称": "券商ETF", "类别": "行业"},
        {"代码": "515050", "名称": "科技ETF", "类别": "行业"}
    ]

    # 模拟AI推荐响应
    mock_response = """根据宽基类别的ETF，推荐以下产品：

1. 沪深300ETF (510300)
   - 理由：跟踪沪深300指数，代表A股核心资产
   - 适合：长期资产配置、指数化投资
   - 风险收益：中等风险、稳健收益

2. 中证500ETF (510500)
   - 理由：跟踪中证500指数，代表中盘成长股
   - 适合：成长性投资、分散配置
   - 风险收益：中高风险、成长性收益

3. 创业板ETF (159915)
   - 理由：跟踪创业板指数，代表创新型成长企业
   - 适合：激进型投资者、长期成长投资
   - 风险收益：高风险、高成长潜力"""

    # 设置mock返回值
    with patch.object(analyzer.fetcher, 'get_etf_list') as mock_get_list:
        mock_get_list.return_value = mock_etf_list
        mock_agent.chat.return_value = mock_response

        # 执行推荐
        result = analyzer.recommend_etfs(category="宽基", top_n=3)

        # 验证结果
        assert result is not None
        assert len(result) == 3
        assert result[0]["etf_code"] == "510300"
        assert result[0]["etf_name"] == "沪深300ETF"
        assert mock_get_list.called
        assert mock_agent.chat.called


def test_recommend_etfs_no_matches(analyzer, mock_agent):
    """测试ETF推荐时没有匹配项的情况"""
    # 模拟ETF列表数据（没有"跨境"类别）
    mock_etf_list = [
        {"代码": "510300", "名称": "沪深300ETF", "类别": "宽基"},
        {"代码": "510500", "名称": "中证500ETF", "类别": "宽基"},
        {"代码": "512690", "名称": "券商ETF", "类别": "行业"}
    ]

    # 设置mock返回值
    with patch.object(analyzer.fetcher, 'get_etf_list') as mock_get_list:
        mock_get_list.return_value = mock_etf_list

        # 执行推荐（查询不存在的类别）
        result = analyzer.recommend_etfs(category="跨境", top_n=3)

        # 验证返回空列表
        assert result is not None
        assert len(result) == 0
        assert mock_get_list.called
        # 验证agent.chat没有被调用（因为没有匹配项）
        assert not mock_agent.chat.called


def test_recommend_etfs_invalid_top_n(analyzer):
    """测试ETF推荐时无效的top_n参数"""
    with pytest.raises(ValueError):
        analyzer.recommend_etfs(category="宽基", top_n=0)

    with pytest.raises(ValueError):
        analyzer.recommend_etfs(category="宽基", top_n=-1)


def test_extract_summary(analyzer):
    """测试提取分析摘要功能"""
    # 测试长文本
    long_text = "这是一段很长的ETF分析文本。" * 50  # 创建超过200字的文本
    summary = analyzer._extract_summary(long_text)

    # 验证摘要长度不超过200字
    assert len(summary) <= 200
    # 验证摘要在最后一个句号处截断（如果存在）
    if len(long_text) > 200:
        assert '。' in summary or len(summary) == 200

    # 测试短文本
    short_text = "这是一段简短的ETF分析文本。"
    summary = analyzer._extract_summary(short_text)

    # 验证短文本完整返回
    assert summary == short_text

    # 测试空文本
    empty_text = ""
    summary = analyzer._extract_summary(empty_text)

    # 验证空文本处理
    assert summary == empty_text


def test_validate_etf_code(analyzer):
    """测试ETF代码验证"""
    # 测试有效的ETF代码
    valid_codes = ["510300", "510500", "159915", "512690"]
    for code in valid_codes:
        # 应该不抛出异常
        analyzer._validate_etf_code(code)

    # 测试无效的ETF代码
    invalid_codes = ["123", "abcdef", "510300a", ""]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            analyzer._validate_etf_code(code)


def test_validate_etf_name(analyzer):
    """测试ETF名称验证"""
    # 测试有效的ETF名称
    valid_names = ["沪深300ETF", "中证500ETF", "创业板ETF"]
    for name in valid_names:
        # 应该不抛出异常
        analyzer._validate_etf_name(name)

    # 测试无效的ETF名称
    invalid_names = ["", None]
    for name in invalid_names:
        with pytest.raises(ValueError):
            analyzer._validate_etf_name(name)


def test_analyze_etf_invalid_params(analyzer):
    """测试无效参数的情况"""
    # 测试无效的ETF代码
    with pytest.raises(ValueError):
        analyzer.analyze_etf(etf_code="invalid", etf_name="沪深300ETF")

    # 测试无效的ETF名称
    with pytest.raises(ValueError):
        analyzer.analyze_etf(etf_code="510300", etf_name="")

    # 测试None名称
    with pytest.raises(ValueError):
        analyzer.analyze_etf(etf_code="510300", etf_name=None)
