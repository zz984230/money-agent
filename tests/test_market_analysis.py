"""
Market Analysis Module Tests
市场分析模块测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from analysis.market_analysis import MarketAnalyzer
from core.agent.base_agent import BaseAgent
import pandas as pd


@pytest.fixture
def mock_agent():
    """创建模拟的Agent"""
    agent = Mock(spec=BaseAgent)
    return agent


@pytest.fixture
def mock_fetcher():
    """创建模拟的AKShareFetcher"""
    with patch('analysis.market_analysis.AKShareFetcher') as mock:
        fetcher = Mock()
        mock.return_value = fetcher
        yield fetcher


@pytest.fixture
def analyzer(mock_agent):
    """创建MarketAnalyzer实例"""
    with patch('analysis.market_analysis.AKShareFetcher'):
        return MarketAnalyzer(mock_agent)


def test_market_index_analysis(analyzer, mock_agent):
    """测试大盘指数分析"""
    # 模拟fetcher返回的指数数据
    mock_df = pd.DataFrame({
        'date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'open': [3200.5, 3210.2, 3205.8],
        'close': [3210.2, 3205.8, 3215.3],
        'high': [3215.0, 3212.5, 3220.1],
        'low': [3198.5, 3203.2, 3200.5],
        'volume': [250000000, 240000000, 260000000],
        'amount': [3000000000, 2900000000, 3100000000]
    })

    # 模拟AI分析响应
    mock_response = """上证指数分析：

1. 指数走势分析
   - 短期：近三日呈现震荡上行趋势，从3200点附近回升至3215点
   - 技术形态：指数在3200点附近获得支撑，呈现企稳回升态势

2. 成交量分析
   - 近三日成交量维持在240-260亿之间，显示市场交投活跃度适中
   - 成交额约为2900-3100亿，资金面相对平稳

3. 市场情绪指标
   - 市场整体情绪偏谨慎乐观
   - 投资者信心逐步恢复

4. 主要影响因素
   - 宏观经济数据向好
   - 政策面支持力度加大
   - 外部市场环境相对稳定

5. 后市展望
   - 短期预计维持区间震荡
   - 中期关注3200点支撑位和3250点压力位
   - 建议关注政策动向和成交量变化"""

    # 设置mock返回值
    with patch.object(analyzer.fetcher, 'get_index_daily') as mock_get_index:
        mock_get_index.return_value = mock_df
        mock_agent.chat.return_value = mock_response

        # 执行分析
        result = analyzer.analyze_index(index_code="000001", date="2024-01-17")

        # 验证结果
        assert result is not None
        assert result["index_code"] == "000001"
        assert result["date"] == "2024-01-17"
        assert "data" in result
        assert "analysis" in result
        assert "summary" in result
        assert len(result["summary"]) <= 200
        assert "上证指数分析" in result["analysis"]
        assert mock_get_index.called
        assert mock_agent.chat.called


def test_market_sentiment_analysis(analyzer, mock_agent):
    """测试市场情绪分析"""
    # 模拟市场涨跌数据
    mock_market_data = {
        "up_count": 2500,
        "down_count": 1500,
        "unchanged_count": 300,
        "limit_up_count": 50,
        "limit_down_count": 10,
        "total_amount": 800000000000
    }

    # 模拟AI情绪分析响应
    mock_response = """市场情绪分析：

今日市场整体情绪：偏多

主要特征：
1. 涨跌比：2500:1500，显示多方占据优势
2. 涨停板数量50家，跌停板仅10家，市场赚钱效应明显
3. 总成交额8000亿，成交量保持活跃
4. 市场信心指数回升，投资者风险偏好提升

综合判断：当前市场情绪积极，建议适度参与，注意风险控制。"""

    # 设置mock返回值
    with patch.object(analyzer.fetcher, 'get_market_stats') as mock_get_stats:
        mock_get_stats.return_value = mock_market_data
        mock_agent.chat.return_value = mock_response

        # 执行情绪分析
        result = analyzer.analyze_sentiment()

        # 验证结果
        assert result is not None
        assert "sentiment" in result
        assert "timestamp" in result
        assert "偏多" in result["sentiment"]
        assert mock_get_stats.called
        assert mock_agent.chat.called


def test_market_index_analysis_empty_data(analyzer, mock_agent):
    """测试指数分析时数据为空的情况"""
    # 模拟空数据
    mock_df = pd.DataFrame()

    # 重置mock以清除之前的调用
    mock_agent.reset_mock()

    with patch.object(analyzer.fetcher, 'get_index_daily') as mock_get_index:
        mock_get_index.return_value = mock_df

        # 执行分析
        result = analyzer.analyze_index(index_code="000001", date="2024-01-17")

        # 验证返回None
        assert result is None
        # 验证agent.chat没有被调用（因为数据为空）
        assert not mock_agent.chat.called


def test_market_sentiment_analysis_failure(analyzer, mock_agent):
    """测试市场情绪分析失败的情况"""
    # 模拟fetcher返回None
    with patch.object(analyzer.fetcher, 'get_market_stats') as mock_get_stats:
        mock_get_stats.return_value = None

        # 执行情绪分析
        result = analyzer.analyze_sentiment()

        # 验证返回None
        assert result is None
        assert not mock_agent.chat.called


def test_extract_summary(analyzer):
    """测试提取分析摘要功能"""
    # 测试长文本
    long_text = "这是一段很长的分析文本。" * 50  # 创建超过200字的文本
    summary = analyzer._extract_summary(long_text)

    # 验证摘要长度不超过200字
    assert len(summary) <= 200
    # 验证摘要在最后一个句号处截断（如果存在）
    if len(long_text) > 200:
        assert '。' in summary or len(summary) == 200

    # 测试短文本
    short_text = "这是一段简短的文本。"
    summary = analyzer._extract_summary(short_text)

    # 验证短文本完整返回
    assert summary == short_text

    # 测试空文本
    empty_text = ""
    summary = analyzer._extract_summary(empty_text)

    # 验证空文本处理
    assert summary == empty_text


def test_validate_index_code(analyzer):
    """测试指数代码验证"""
    # 测试有效的指数代码
    valid_codes = ["000001", "399001", "000300", "000905"]
    for code in valid_codes:
        # 应该不抛出异常
        analyzer._validate_index_code(code)

    # 测试无效的指数代码
    invalid_codes = ["123", "abcdef", "000001a", ""]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            analyzer._validate_index_code(code)


def test_validate_date(analyzer):
    """测试日期验证"""
    # 测试有效的日期格式
    valid_dates = ["2024-01-15", "2024-12-31", "2023-01-01"]
    for date in valid_dates:
        # 应该不抛出异常
        analyzer._validate_date(date)

    # 测试无效的日期格式
    invalid_dates = ["2024/01/15", "01-15-2024", "2024-13-01", "invalid", ""]
    for date in invalid_dates:
        with pytest.raises(ValueError):
            analyzer._validate_date(date)


def test_market_index_analysis_invalid_params(analyzer):
    """测试无效参数的情况"""
    # 测试无效的指数代码
    with pytest.raises(ValueError):
        analyzer.analyze_index(index_code="invalid", date="2024-01-15")

    # 测试无效的日期
    with pytest.raises(ValueError):
        analyzer.analyze_index(index_code="000001", date="invalid-date")
