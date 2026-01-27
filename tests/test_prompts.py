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