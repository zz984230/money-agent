import os
from typing import Optional, Dict, Any, Generator
from zhipuai import ZhipuAI
from .base_agent import BaseAgent
from config.settings import settings


class GLMAgent(BaseAgent):
    """GLM-4.7 AI Agent 实现"""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        # 优先使用传入的 model_name，否则使用 settings 中的配置
        model_name = model_name or settings.glm_model
        super().__init__(model_name, temperature, max_tokens)

        # 初始化 ZhipuAI 客户端
        api_key = settings.glm_api_key or os.getenv('GLM_API_KEY')
        api_base = settings.glm_api_base or os.getenv('GLM_API_BASE')

        if not api_key:
            raise ValueError("GLM API key is required. Please set it in config.settings or GLM_API_KEY environment variable.")

        self.client = ZhipuAI(
            api_key=api_key,
            base_url=api_base if api_base else None
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
            print(f"GLM API 调用失败: {e}")
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
            print(f"GLM 流式 API 调用失败: {e}")
            yield f"Error: {e}"