"""
Stock Screening Module Tests
选股筛选模块测试
"""

import pytest
from unittest.mock import Mock, patch
from analysis.screening import StockScreener
from core.agent.glm_agent import GLMAgent


@pytest.fixture
def mock_agent():
    """创建模拟的GLM Agent"""
    agent = Mock(spec=GLMAgent)
    agent.chat.return_value = """根据筛选条件，推荐以下股票：

1. 600519 贵州茅台
   - PE: 25.6
   - ROE: 28.5%
   - 理由：行业龙头，品牌价值高，盈利能力强

2. 000858 五粮液
   - PE: 28.3
   - ROE: 22.1%
   - 理由：白酒行业第二品牌，业绩稳定增长

3. 000333 美的集团
   - PE: 18.7
   - ROE: 18.9%
   - 理由：家电龙头，多元化布局良好

4. 002415 海康威视
   - PE: 22.1
   - ROE: 26.3%
   - 理由：安防行业龙头，技术实力强

5. 000651 格力电器
   - PE: 12.3
   - ROE: 19.8%
   - 理由：空调龙头，估值相对合理"""
    return agent


@pytest.fixture
def screener(mock_agent):
    """创建StockScreener实例"""
    return StockScreener(mock_agent)


def test_stock_screening_with_mock(screener, mock_agent):
    """测试选股功能 - 使用mock"""
    criteria = {
        "pe": {"max": 30},
        "roe": {"min": 15}
    }
    result = screener.screen_stocks(criteria, top_n=5)

    # 验证结果不为空
    assert result is not None
    assert "stocks" in result
    assert "reasoning" in result

    # 验证股票列表
    assert len(result["stocks"]) == 5
    assert result["stocks"][0]["symbol"] == "600519"
    assert result["stocks"][0]["name"] == "贵州茅台"

    # 验证AI被正确调用
    mock_agent.chat.assert_called_once()

    # 验证调用参数
    call_args = mock_agent.chat.call_args[0][0]
    assert "筛选条件" in call_args
    assert "pe ≤ 30" in call_args
    assert "roe ≥ 15" in call_args


def test_parse_stocks_from_response():
    """测试从AI响应中解析股票列表"""
    from analysis.screening import StockScreener

    # 创建一个带有mock agent的screener
    mock_agent = Mock(spec=GLMAgent)
    screener = StockScreener(mock_agent)

    # 测试响应
    response = """根据筛选条件，推荐以下股票：

1. 600519 贵州茅台
   - PE: 25.6
   - ROE: 28.5%
   - 理由：行业龙头，品牌价值高，盈利能力强

2. 000858 五粮液
   - PE: 28.3
   - ROE: 22.1%
   - 理由：白酒行业第二品牌，业绩稳定增长

3. 000333 美的集团
   - PE: 18.7
   - ROE: 18.9%
   - 理由：家电龙头，多元化布局良好

4. 002415 海康威视
   - PE: 22.1
   - ROE: 26.3%
   - 理由：安防行业龙头，技术实力强

5. 000651 格力电器
   - PE: 12.3
   - ROE: 19.8%
   - 理由：空调龙头，估值相对合理"""

    # 解析股票列表
    stocks = screener._parse_stocks_from_response(response)

    # 验证结果
    assert len(stocks) == 5
    assert stocks[0]["symbol"] == "600519"
    assert stocks[0]["name"] == "贵州茅台"
    assert stocks[0]["pe"] == 25.6
    assert stocks[0]["roe"] == 28.5
    assert "行业龙头" in stocks[0]["reasoning"]


def test_stock_screening_empty_response(screener):
    """测试空响应的情况"""
    # 修改mock返回空响应
    screener.agent.chat.return_value = "没有找到符合条件的股票。"

    criteria = {
        "pe": {"max": 10},
        "roe": {"min": 30}
    }
    result = screener.screen_stocks(criteria, top_n=5)

    # 验证返回空结果
    assert result is not None
    assert len(result["stocks"]) == 0
    assert result["reasoning"] == "没有找到符合条件的股票。"


def test_stock_screening_invalid_criteria(screener):
    """测试无效的筛选条件"""
    # 测试无效格式 - 应该抛出ValueError
    criteria = {"invalid_key": {"invalid_op": 10}}
    with pytest.raises(ValueError, match="无效的筛选条件键"):
        screener.screen_stocks(criteria, top_n=5)