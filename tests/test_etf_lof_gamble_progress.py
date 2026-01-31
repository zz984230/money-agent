"""
ETF/LOF投机异常波动分析模块 - 进度回调测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from core.agent.base_agent import BaseAgent
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer


@pytest.fixture
def gamble_analyzer():
    """LOFETFGambleAnalyzer fixture"""
    mock_agent = Mock(spec=BaseAgent)
    return LOFETFGambleAnalyzer(mock_agent)


def test_progress_callback_signature(gamble_analyzer, mocker):
    """测试进度回调函数接收正确的参数"""
    # 收集回调参数
    callback_calls = []

    def mock_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append({
            'progress': progress,
            'message': message,
            'detail': detail,
            'current': current,
            'total': total
        })

    # Mock 数据
    mock_df = pd.DataFrame({
        'close': [1.0, 1.05, 1.10, 0.95, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40] * 10,
    })
    mock_df.index = pd.date_range('2025-01-01', periods=100)

    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_commodity_lof_list',
        return_value=[
            {'code': '163415', 'name': '白银LOF', 'type': 'LOF'},
            {'code': '163416', 'name': '黄金LOF', 'type': 'LOF'}
        ]
    )
    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_lof_etf_history',
        return_value=mock_df
    )
    mocker.patch.object(gamble_analyzer, 'analyze_single', return_value=None)

    # 执行筛选
    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    results = gamble_analyzer.screen_and_analyze(
        criteria=criteria,
        top_n=2,
        progress_callback=mock_callback
    )

    # 验证回调被正确调用
    assert len(callback_calls) > 0, "进度回调应该被调用"

    # 验证最后一次回调是完成状态
    final_call = callback_calls[-1]
    assert final_call['progress'] == 1.0, f"最终进度应为1.0，实际为{final_call['progress']}"
    assert '完成' in final_call['message'], f"最终消息应包含'完成'，实际为{final_call['message']}"


def test_progress_callback_with_detailed_info(gamble_analyzer, mocker):
    """测试进度回调传递详细标的信息"""
    # 收集回调参数
    callback_calls = []

    def mock_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append({
            'progress': progress,
            'message': message,
            'detail': detail,
            'current': current,
            'total': total
        })

    # Mock 数据
    mock_df = pd.DataFrame({
        'close': [1.0, 1.05, 1.10, 0.95, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40] * 10,
    })
    mock_df.index = pd.date_range('2025-01-01', periods=100)

    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_commodity_lof_list',
        return_value=[
            {'code': '163415', 'name': '白银LOF', 'type': 'LOF'},
            {'code': '163416', 'name': '黄金LOF', 'type': 'LOF'},
            {'code': '163417', 'name': '原油LOF', 'type': 'LOF'}
        ]
    )
    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_lof_etf_history',
        return_value=mock_df
    )
    mocker.patch.object(gamble_analyzer, 'analyze_single', return_value=None)

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    results = gamble_analyzer.screen_and_analyze(
        criteria=criteria,
        top_n=3,
        progress_callback=mock_callback
    )

    # 验证详细信息的参数结构
    # 检查是否有包含详细信息的回调
    detailed_calls = [c for c in callback_calls if c['detail'] is not None]

    # 至少应该有一些回调包含详细信息
    assert len(detailed_calls) > 0, "应该有回调包含详细信息"

    # 验证详细信息的数据类型
    for call in detailed_calls:
        assert isinstance(call['progress'], (int, float)), "进度应为数字"
        assert isinstance(call['message'], str), "消息应为字符串"
        assert isinstance(call['detail'], str), "详细信息应为字符串"
        assert isinstance(call['current'], int), "当前索引应为整数"
        assert isinstance(call['total'], int), "总数应为整数"

    # 验证当前索引和总数的合理性
    for call in detailed_calls:
        assert 0 <= call['current'] <= call['total'], "当前索引应在合理范围内"
        assert call['total'] > 0, "总数应大于0"


def test_progress_callback_without_optional_params(gamble_analyzer):
    """测试进度回调可以只传必需参数"""
    callback_calls = []

    def minimal_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append({
            'progress': progress,
            'message': message,
            'detail': detail,
            'current': current,
            'total': total
        })

    # 测试只传必需参数
    minimal_callback(0.5, "测试消息")

    assert callback_calls[0]['progress'] == 0.5
    assert callback_calls[0]['message'] == "测试消息"
    assert callback_calls[0]['detail'] is None
    assert callback_calls[0]['current'] is None
    assert callback_calls[0]['total'] is None

    # 测试完成状态
    minimal_callback(1.0, "完成")

    assert callback_calls[1]['progress'] == 1.0
    assert callback_calls[1]['message'] == "完成"
    assert callback_calls[1]['detail'] is None
    assert callback_calls[1]['current'] is None
    assert callback_calls[1]['total'] is None


def test_progress_callback_phases(gamble_analyzer, mocker):
    """测试进度回调的不同阶段"""
    callback_calls = []

    def mock_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append({
            'progress': progress,
            'message': message,
            'detail': detail,
            'current': current,
            'total': total
        })

    # Mock 数据
    mock_df = pd.DataFrame({
        'close': [1.0, 1.05, 1.10, 0.95, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40] * 10,
    })
    mock_df.index = pd.date_range('2025-01-01', periods=100)

    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_commodity_lof_list',
        return_value=[
            {'code': '163415', 'name': '白银LOF', 'type': 'LOF'},
            {'code': '163416', 'name': '黄金LOF', 'type': 'LOF'}
        ]
    )
    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_lof_etf_history',
        return_value=mock_df
    )
    mocker.patch.object(gamble_analyzer, 'analyze_single', return_value=None)

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    results = gamble_analyzer.screen_and_analyze(
        criteria=criteria,
        top_n=2,
        progress_callback=mock_callback
    )

    # 验证不同阶段
    # 筛选阶段 (0-40%)
    screening_calls = [c for c in callback_calls if '筛选' in c['message']]
    assert len(screening_calls) > 0, "应该有筛选阶段的回调"

    # 分析阶段 (40-100%)
    analysis_calls = [c for c in callback_calls if '分析' in c['message']]
    assert len(analysis_calls) > 0, "应该有分析阶段的回调"

    # 完成阶段 (100%)
    complete_calls = [c for c in callback_calls if c['progress'] == 1.0]
    assert len(complete_calls) > 0, "应该有完成阶段的回调"

    # 验证进度是递增的
    progresses = [c['progress'] for c in callback_calls]
    assert progresses == sorted(progresses), "进度应该是递增的"


def test_progress_callback_no_callback(gamble_analyzer, mocker):
    """测试不提供进度回调时也能正常工作"""
    # Mock 数据
    mock_df = pd.DataFrame({
        'close': [1.0, 1.05, 1.10, 0.95, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40] * 10,
    })
    mock_df.index = pd.date_range('2025-01-01', periods=100)

    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_commodity_lof_list',
        return_value=[
            {'code': '163415', 'name': '白银LOF', 'type': 'LOF'}
        ]
    )
    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_lof_etf_history',
        return_value=mock_df
    )
    mocker.patch.object(gamble_analyzer, 'analyze_single', return_value=None)

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    # 不提供进度回调
    results = gamble_analyzer.screen_and_analyze(
        criteria=criteria,
        top_n=1,
        progress_callback=None
    )

    # 应该正常完成，不抛出异常
    assert isinstance(results, list)


def test_progress_callback_progress_range(gamble_analyzer, mocker):
    """测试进度值在合理范围内"""
    callback_calls = []

    def mock_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append(progress)

    # Mock 数据
    mock_df = pd.DataFrame({
        'close': [1.0, 1.05, 1.10, 0.95, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40] * 10,
    })
    mock_df.index = pd.date_range('2025-01-01', periods=100)

    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_commodity_lof_list',
        return_value=[
            {'code': '163415', 'name': '白银LOF', 'type': 'LOF'}
        ]
    )
    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_lof_etf_history',
        return_value=mock_df
    )
    mocker.patch.object(gamble_analyzer, 'analyze_single', return_value=None)

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    results = gamble_analyzer.screen_and_analyze(
        criteria=criteria,
        top_n=1,
        progress_callback=mock_callback
    )

    # 验证所有进度值都在 0-1 范围内
    for progress in callback_calls:
        assert 0 <= progress <= 1.0, f"进度值应在0-1范围内，实际为{progress}"

    # 验证起始和结束进度
    assert callback_calls[0] >= 0, "起始进度应大于等于0"
    assert callback_calls[-1] == 1.0, "结束进度应为1.0"
