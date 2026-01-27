import pytest
import os
from unittest.mock import patch, MagicMock
from core.agent.glm_agent import GLMAgent
from config.settings import settings

@patch('core.agent.glm_agent.ZhipuAI')
def test_glm_agent_init(mock_zhipu):
    """测试 GLM Agent 初始化"""
    # 设置模拟的 API key
    with patch.object(settings, 'glm_api_key', 'test_key'):
        agent = GLMAgent()
        assert agent.model_name == settings.glm_model
        assert mock_zhipu.called

@patch('core.agent.glm_agent.ZhipuAI')
def test_glm_agent_chat(mock_zhipu):
    """测试 AI 对话功能"""
    # 模拟 API 响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好！我是一个GLM AI助手。"
    mock_zhipu.return_value.chat.completions.create.return_value = mock_response

    # 设置模拟的 API key
    with patch.object(settings, 'glm_api_key', 'test_key'):
        agent = GLMAgent()
        response = agent.chat("你好，请用一句话介绍你自己")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "GLM" in response

@patch('core.agent.glm_agent.ZhipuAI')
def test_glm_agent_stock_analysis(mock_zhipu):
    """测试股票分析功能"""
    # 模拟 API 响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "贵州茅台作为中国白酒行业的龙头企业，具有强大的品牌优势。从财务状况来看，公司营收稳健增长。从估值水平来看，当前估值相对合理。"
    mock_zhipu.return_value.chat.completions.create.return_value = mock_response

    # 设置模拟的 API key
    with patch.object(settings, 'glm_api_key', 'test_key'):
        agent = GLMAgent()
        prompt = "请分析贵州茅台(600519)的投资价值，从行业地位、财务状况、估值水平三个方面进行简要分析"
        response = agent.chat(prompt)
        assert response is not None
        assert isinstance(response, str)
        # 检查是否包含关键词
        assert any(keyword in response for keyword in ['茅台', '贵州茅台', '白酒', '行业'])