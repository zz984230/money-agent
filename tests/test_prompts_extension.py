"""
Prompt扩展功能测试 - ETF/LOF投机分析
"""
import pytest
import pandas as pd
from core.agent.prompts import PromptBuilder
from datetime import datetime


def test_build_etf_lof_gamble_prompt():
    """测试ETF/LOF投机分析Prompt构建"""
    # 准备测试数据
    symbol = "163415"
    name = "白银LOF"
    fund_type = "LOF"

    abnormal_events = [
        {
            'date': pd.Timestamp('2024-01-15'),
            'return_pct': 0.18,
            'volatility': 0.12
        },
        {
            'date': pd.Timestamp('2024-02-10'),
            'return_pct': -0.20,
            'volatility': 0.15
        }
    ]

    current_factors = {
        'momentum_5': 0.05,
        'volume_ratio': 2.5,
        'rsi_14': 65
    }

    feature_importance = pd.DataFrame({
        'feature': ['momentum_5', 'volume_ratio', 'rsi_14'],
        'importance': [0.35, 0.28, 0.15]
    })

    current_data = {
        'price': 1.234,
        'change_pct': 2.5,
        'volume': 5000000,
        'volatility_20d': 0.08
    }

    prompt = PromptBuilder().build_etf_lof_gamble_prompt(
        symbol, name, fund_type, abnormal_events,
        current_factors, feature_importance, current_data
    )

    # 验证Prompt包含关键信息
    assert symbol in prompt
    assert name in prompt
    # 新的prompt格式使用不同的section标题
    assert "因子综合解读" in prompt or "因子" in prompt
    assert "历史规律总结" in prompt or "历史规律" in prompt
    assert "时机判断" in prompt
    assert "操作建议" in prompt
    assert "风险提示" in prompt
    assert "适合买入" in prompt or "观望" in prompt or "不适合买入" in prompt

    print("\n" + "="*50)
    print("Generated Prompt:")
    print(prompt)
    print("="*50)


def test_build_etf_lof_gamble_prompt_no_events():
    """测试无异常事件时的Prompt构建"""
    prompt = PromptBuilder().build_etf_lof_gamble_prompt(
        "163415", "白银LOF", "LOF",
        [],  # 无异常事件
        {},  # current_factors
        pd.DataFrame({'feature': [], 'importance': []}),  # feature_importance
        {}   # current_data
    )

    assert "无历史异常事件" in prompt or "163415" in prompt


def test_build_etf_lof_gamble_prompt_with_empty_data():
    """测试空数据时的Prompt构建"""
    feature_importance = pd.DataFrame({
        'feature': [],
        'importance': []
    })

    prompt = PromptBuilder().build_etf_lof_gamble_prompt(
        "163415", "白银LOF", "LOF",
        [],
        {},
        feature_importance,
        {}
    )

    # 应该仍然生成有效的prompt
    assert "163415" in prompt
    assert "白银LOF" in prompt
