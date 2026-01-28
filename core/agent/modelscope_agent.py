"""
ModelScope Agent Module
ModelScope AI Agent 实现 (支持 Qwen 等模型)
"""

import os
import logging
from typing import Optional, Dict, Any, Generator
from openai import OpenAI

from .base_agent import BaseAgent
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelScopeAgent(BaseAgent):
    """ModelScope AI Agent 实现，使用 OpenAI 兼容接口"""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        # 优先使用传入的 model_name，否则使用 settings 中的配置
        model_name = model_name or settings.modelscope_model
        super().__init__(model_name, temperature, max_tokens)

        # 初始化 OpenAI 客户端 (ModelScope API 兼容 OpenAI 格式)
        api_key = settings.modelscope_api_key or os.getenv('MODELSCOPE_API_KEY')
        api_base = settings.modelscope_api_base or os.getenv('MODELSCOPE_API_BASE')

        if not api_key:
            raise ValueError("MODELSCOPE_API_KEY is required. Please set it in config.settings or MODELSCOPE_API_KEY environment variable.")

        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )

    def chat(self, prompt: str, **kwargs) -> Optional[str]:
        """发送对话请求"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"ModelScope API 调用失败: {e}")
            return None

    def stream_chat(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """流式对话"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"ModelScope 流式 API 调用失败: {e}")
            yield f"Error: {e}"
