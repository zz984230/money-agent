"""
Convertible Bond Analysis Module Tests
可转债分析模块测试
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


def test_analyze_convertible(analyzer, mock_agent):
    """测试可转债分析功能"""
    # 模拟可转债列表数据
    mock_cb_data = pd.DataFrame({
        0: ['113527'],  # 代码
        1: ['兴业转债'],  # 名称
        2: [100.5],  # 现价
        3: [0.5],  # 涨跌幅
        4: ['601166'],  # 正股代码
        5: ['兴业银行'],  # 正股名称
        7: [5.0],  # 转股溢价率
        9: [105.0],  # 转股价
        10: [95.0],  # 转股价值
        12: ['AAA'],  # 评级
        15: [500.0],  # 规模
        16: ['2026-12-31'],  # 到期日
        18: [100.5]  # 剩余规模
    })

    # 模拟AI分析响应
    mock_response = """兴业转债分析报告：

1. 可转债基本信息
   - 可转债代码：113527
   - 可转债名称：兴业转债
   - 发行规模：50亿元
   - 转股价：105.00元

2. 正股表现分析
   - 正股：兴业银行
   - 近期走势平稳，略有上涨
   - 股价波动率适中

3. 可转债条款分析
   - 转股条款：标准条款，转股期从发行后6个月开始
   - 回售条款：持有人有权在特定条件下回售
   - 赎回条款：发行人有权在股价持续高于转股价一定比例时赎回

4. 估值分析
   - 纯债价值：约98元
   - 期权价值：约3元
   - 综合估值合理

5. 投资价值评估
   - 双低值适中，具有一定投资价值
   - 债底保护较好，下行风险有限
   - 适合稳健型投资者配置

6. 风险提示
   - 正股波动风险
   - 利率风险
   - 提前赎回风险"""

    # 设置mock返回值
    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_cb_data
        mock_agent.chat.return_value = mock_response

        # 执行分析
        result = analyzer.analyze_convertible(cb_code="113527", cb_name="兴业转债")

        # 验证结果
        assert result is not None
        assert result["cb_code"] == "113527"
        assert result["cb_name"] == "兴业转债"
        assert "data" in result
        assert "analysis" in result
        assert "summary" in result
        assert len(result["summary"]) <= 200
        assert "兴业转债" in result["analysis"]
        assert mock_agent.chat.called


def test_analyze_convertible_empty_list(analyzer, mock_agent):
    """测试可转债列表为空的情况"""
    # 模拟空数据
    mock_df = pd.DataFrame()

    # 设置AI响应
    mock_agent.chat.return_value = "兴业转债分析报告（无市场数据）..."

    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_df

        # 执行分析 - 应该返回结果但没有市场数据
        result = analyzer.analyze_convertible(cb_code="113527", cb_name="兴业转债")

        # 验证返回结果（即使列表为空也会调用AI）
        assert result is not None
        # AI应该被调用（即使没有市场数据）
        assert mock_agent.chat.called


def test_get_convertible_list(analyzer):
    """测试获取可转债列表功能"""
    # 模拟可转债列表数据
    mock_data = pd.DataFrame({
        0: ['113527', '113528', '113529', '113530', '113531'],
        1: ['兴业转债', '国君转债', '中信转债', '招路转债', '平银转债'],
        2: [100.5, 101.2, 99.8, 102.3, 100.1],
        3: [0.5, 1.2, -0.2, 1.5, 0.1]
    })

    # 设置mock返回值
    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_data

        # 执行获取
        result = analyzer.get_convertible_list()

        # 验证结果
        assert result is not None
        assert len(result) == 5
        assert result[0]["cb_code"] == "113527"
        assert result[0]["cb_name"] == "兴业转债"


def test_get_convertible_list_empty(analyzer):
    """测试获取可转债列表为空的情况"""
    # 模拟空列表
    mock_df = pd.DataFrame()

    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_df

        # 执行获取
        result = analyzer.get_convertible_list()

        # 验证返回None
        assert result is None


def test_screen_double_low(analyzer):
    """测试双低策略筛选功能"""
    # 模拟可转债列表数据
    mock_data = pd.DataFrame({
        0: ['113527', '113528', '113529', '113530', '113531'],
        1: ['兴业转债', '国君转债', '中信转债', '招路转债', '平银转债'],
        2: [105.0, 108.0, 102.0, 109.0, 95.0],  # 现价
        3: [0.5, 1.2, -0.2, 1.5, 0.1]  # 涨跌幅
    })

    # 设置mock返回值
    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_data

        # 执行筛选（价格<=110，溢价率<=30%）
        result = analyzer.screen_double_low(max_price=110.0, max_premium=30.0, top_n=3)

        # 验证结果
        assert result is not None
        assert len(result) == 3
        # 验证结果是按双低值升序排列的
        assert "double_low" in result[0]
        assert result[0]["double_low"] <= result[1]["double_low"]
        assert result[1]["double_low"] <= result[2]["double_low"]


def test_screen_double_low_no_matches(analyzer):
    """测试双低策略筛选时没有匹配项的情况"""
    # 模拟可转债列表数据（所有可转债价格都超过限制）
    mock_data = pd.DataFrame({
        0: ['113527', '113528'],
        1: ['兴业转债', '国君转债'],
        2: [120.0, 125.0],  # 现价超过限制
        3: [0.5, 1.2]
    })

    # 设置mock返回值
    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_data

        # 执行筛选（价格<=110，但没有符合条件的）
        result = analyzer.screen_double_low(max_price=110.0, max_premium=30.0, top_n=3)

        # 验证返回空列表
        assert result is not None
        assert len(result) == 0


def test_screen_double_low_invalid_params(analyzer):
    """测试双低策略筛选时无效的参数"""
    with pytest.raises(ValueError):
        analyzer.screen_double_low(max_price=-1.0)

    with pytest.raises(ValueError):
        analyzer.screen_double_low(max_premium=-1.0)

    with pytest.raises(ValueError):
        analyzer.screen_double_low(top_n=0)


def test_validate_cb_code(analyzer):
    """测试可转债代码验证"""
    # 测试有效的可转债代码
    valid_codes = ["113527", "113528", "123456"]
    for code in valid_codes:
        # 应该不抛出异常
        analyzer._validate_cb_code(code)

    # 测试无效的可转债代码
    invalid_codes = ["123", "abcdef", "510300a", ""]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            analyzer._validate_cb_code(code)


def test_validate_cb_name(analyzer):
    """测试可转债名称验证"""
    # 测试有效的可转债名称
    valid_names = ["兴业转债", "国君转债", "中信转债"]
    for name in valid_names:
        # 应该不抛出异常
        analyzer._validate_cb_name(name)

    # 测试无效的可转债名称
    invalid_names = ["", None]
    for name in invalid_names:
        with pytest.raises(ValueError):
            analyzer._validate_cb_name(name)


def test_analyze_convertible_invalid_params(analyzer):
    """测试无效参数的情况"""
    # 测试无效的可转债代码
    with pytest.raises(ValueError):
        analyzer.analyze_convertible(cb_code="invalid", cb_name="兴业转债")

    # 测试无效的可转债名称
    with pytest.raises(ValueError):
        analyzer.analyze_convertible(cb_code="113527", cb_name="")

    # 测试None名称
    with pytest.raises(ValueError):
        analyzer.analyze_convertible(cb_code="113527", cb_name=None)


def test_analyze_convertible_by_name(analyzer, mock_agent):
    """测试根据名称分析可转债"""
    # 模拟可转债列表数据
    mock_data = pd.DataFrame({
        0: ['113527', '113528'],
        1: ['兴业转债', '国君转债'],
        2: [100.5, 101.2],
        3: [0.5, 1.2],
        4: ['601166', '601211'],
        5: ['兴业银行', '国泰君安']
    })

    mock_agent.chat.return_value = "兴业转债分析报告..."

    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_data

        # 执行分析（通过名称）
        result = analyzer.analyze_convertible_by_name("兴业转债")

        # 验证结果
        assert result is not None
        assert result["cb_code"] == "113527"
        assert result["cb_name"] == "兴业转债"


def test_analyze_convertible_by_name_not_found(analyzer, mock_agent):
    """测试根据名称分析但未找到可转债"""
    # 模拟可转债列表数据（不包含集智转债）
    mock_data = pd.DataFrame({
        0: ['113527'],
        1: ['兴业转债'],
        2: [100.5],
        3: [0.5]
    })

    mock_agent.chat.return_value = "集智转债分析报告..."

    with patch('akshare.bond_cb_jsl') as mock_bond_cb_jsl:
        mock_bond_cb_jsl.return_value = mock_data

        # 执行分析（通过名称，但不在列表中）
        result = analyzer.analyze_convertible_by_name("集智转债")

        # 验证结果（应该使用AI知识库进行分析）
        assert result is not None
        assert result["cb_code"] == "未知"
        assert result["cb_name"] == "集智转债"
        assert mock_agent.chat.called


def test_analyze_convertible_ai_only(analyzer, mock_agent):
    """测试仅使用AI分析模式"""
    mock_agent.chat.return_value = "集智转债分析报告..."

    # 执行分析（仅使用AI）
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
