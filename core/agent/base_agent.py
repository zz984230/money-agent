from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseAgent(ABC):
    """AI Agent 基类"""

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> Optional[str]:
        """发送对话请求"""
        pass

    @abstractmethod
    def stream_chat(self, prompt: str, **kwargs):
        """流式对话"""
        pass