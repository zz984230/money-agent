import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import pandas as pd

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent.prompts import PromptBuilder

def test_build_stock_screening_prompt():
    """测试生成选股提示词"""
    builder = PromptBuilder()
    prompt = builder.build_stock_screening_prompt(
        criteria={"pe": {"max": 30}, "roe": {"min": 15}},
        stock_count=10
    )
    assert "选股" in prompt or "筛选" in prompt
    assert "PE" in prompt or "市盈率" in prompt
    assert "10只优质股票" in prompt

def test_build_market_analysis_prompt():
    """测试生成市场分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_market_analysis_prompt(
        index_code="000001",
        date="2024-01-15"
    )
    assert "分析" in prompt
    assert "000001" in prompt
    assert "2024-01-15" in prompt

def test_build_stock_analysis_prompt():
    """测试生成个股分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_stock_analysis_prompt(
        symbol="600519",
        company_name="贵州茅台"
    )
    assert "600519" in prompt or "贵州茅台" in prompt
    assert "分析" in prompt
    assert "全面分析" in prompt

def test_build_stock_analysis_prompt_technical():
    """测试生成技术分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_stock_analysis_prompt(
        symbol="000001",
        company_name="平安银行",
        analysis_type="technical"
    )
    assert "技术分析" in prompt
    assert "MACD" in prompt
    assert "RSI" in prompt

def test_build_stock_analysis_prompt_fundamental():
    """测试生成基本面分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_stock_analysis_prompt(
        symbol="000858",
        company_name="五粮液",
        analysis_type="fundamental"
    )
    assert "基本面分析" in prompt
    assert "财务状况" in prompt

def test_build_etf_analysis_prompt():
    """测试生成ETF分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_etf_analysis_prompt(
        etf_code="510300",
        etf_name="沪深ETF"
    )
    assert "ETF分析" in prompt
    assert "510300" in prompt
    assert "沪深ETF" in prompt

def test_build_convertible_analysis_prompt():
    """测试生成可转债分析提示词"""
    builder = PromptBuilder()
    prompt = builder.build_convertible_analysis_prompt(
        cb_code="113527",
        cb_name="隆基转债"
    )
    assert "可转债分析" in prompt
    assert "113527" in prompt
    assert "隆基转债" in prompt
    assert "转股条款" in prompt

def test_format_criteria():
    """测试筛选条件格式化"""
    builder = PromptBuilder()
    criteria = {"pe": {"max": 30}, "roe": {"min": 15}, "pb": {"eq": 2.5}}
    formatted = builder._format_criteria(criteria)
    assert "pe ≤ 30" in formatted
    assert "roe ≥ 15" in formatted
    assert "pb = 2.5" in formatted
    assert "30" in formatted
    assert "15" in formatted
    assert "2.5" in formatted


class TestConvertibleTechnicalPrompts:
    """测试可转债技术面提示词"""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    def test_build_convertible_technical_prompt(self, builder):
        """测试技术面分析提示词"""
        from analysis.convertible_technical_analysis import ConvertibleTechnicalData

        tech_data = ConvertibleTechnicalData(
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
            ma5=104.5,
            ma20=103.0,
            volatility_20d=2.5,
        )

        prompt = builder.build_convertible_technical_prompt(tech_data)

        assert '113527' in prompt
        assert '利民转债' in prompt
        assert '105.5' in prompt
        assert '技术分析师' in prompt
        assert '定位判断' in prompt
        assert '估值分析' in prompt
        assert '投资建议' in prompt

    def test_build_convertible_terms_prompt(self, builder):
        """测试条款博弈提示词"""
        prompt = builder.build_convertible_terms_prompt(
            cb_code="113527",
            cb_name="利民转债",
            stock_price=125.0,
            stock_name="利民股份",
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_price=100.0,
        )

        assert '113527' in prompt
        assert '125.0' in prompt
        assert '强赎' in prompt
        assert '回售' in prompt
        assert '下修' in prompt