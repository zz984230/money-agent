"""
Stock Screening Module
选股筛选模块
"""

import re
import json
from typing import Dict, List, Any, Optional
from core.agent.glm_agent import GLMAgent
from core.agent.prompts import PromptBuilder


class StockScreener:
    """股票筛选器，基于AI分析的股票推荐系统"""

    # 类常量
    DEFAULT_LIMIT = 10
    NO_STOCK_KEYWORDS = ["没有找到", "无符合条件", "抱歉"]
    STOCK_PATTERN = r'(\d{6})\s+([^\d\n]+)\s+-\s+PE:\s*([\d.]+)\s+-\s+ROE:\s*([\d.]+)%'
    REASONING_PATTERN_TEMPLATE = r'{symbol}\s+{name}.*?(?=下一个|\n\n|\Z)'
    CODE_PATTERN = r'(\d{6})\s+[^\d\n]+'
    REASONING_PREFIX = "理由："

    def __init__(self, agent: GLMAgent):
        """
        初始化股票筛选器

        Args:
            agent: GLM AI Agent 实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()

    def _validate_criteria(self, criteria: Dict[str, Dict[str, float]], top_n: int) -> None:
        """
        验证筛选条件的参数有效性

        Args:
            criteria: 筛选条件字典
            top_n: 返回的股票数量

        Raises:
            ValueError: 当参数无效时抛出异常
        """
        if not isinstance(criteria, dict):
            raise ValueError("筛选条件必须是字典类型")

        if not isinstance(top_n, int) or top_n <= 0:
            raise ValueError("top_n必须是正整数")

        if top_n > 100:
            raise ValueError("top_n不能超过100")

        allowed_keys = {"pe", "roe", "pb", "ps", "dividend_yield"}
        allowed_ops = {"min", "max", "eq"}

        for key, ops in criteria.items():
            if key not in allowed_keys:
                raise ValueError(f"无效的筛选条件键: {key}")

            if not isinstance(ops, dict):
                raise ValueError(f"条件值必须是字典类型: {key}")

            for op, value in ops.items():
                if op not in allowed_ops:
                    raise ValueError(f"无效的操作符: {op}")

                if not isinstance(value, (int, float)):
                    raise ValueError(f"条件值必须是数字类型: {op}: {value}")

    def screen_stocks(self, criteria: Dict[str, Dict[str, float]], top_n: int = 10) -> Dict[str, Any]:
        """
        执行股票筛选

        Args:
            criteria: 筛选条件字典，如 {"pe": {"max": 30}, "roe": {"min": 15}}
            top_n: 返回的股票数量

        Returns:
            包含筛选结果和推理的字典
        """
        # 验证输入参数
        self._validate_criteria(criteria, top_n)

    def screen_stocks(self, criteria: Dict[str, Dict[str, float]], top_n: int = 10) -> Dict[str, Any]:
        """
        执行股票筛选

        Args:
            criteria: 筛选条件字典，如 {"pe": {"max": 30}, "roe": {"min": 15}}
            top_n: 返回的股票数量

        Returns:
            包含筛选结果和推理的字典
        """
        # 构建提示词
        prompt = self.prompt_builder.build_stock_screening_prompt(criteria, top_n)

        # 调用AI进行分析
        response = self.agent.chat(prompt)

        if not response:
            return {
                "stocks": [],
                "reasoning": "AI分析失败，请稍后重试。"
            }

        # 解析AI响应
        stocks = self._parse_stocks_from_response(response)

        # 确保只返回指定数量的股票
        stocks = stocks[:top_n]

        # 构建返回结果
        result = {
            "stocks": stocks,
            "reasoning": response,
            "criteria": criteria,
            "count": len(stocks)
        }

        return result

    def _parse_stocks_from_response(self, response: str) -> List[Dict[str, Any]]:
        """
        从AI响应中解析股票列表

        Args:
            response: AI返回的文本响应

        Returns:
            股票信息列表，每个股票包含symbol, name, pe, roe, reasoning等字段
        """
        stocks = []

        # 如果响应明确表示没有找到股票，返回空列表
        if not response.strip():
            return stocks

        # 检查是否有无股票的关键词
        for keyword in self.NO_STOCK_KEYWORDS:
            if keyword in response:
                return stocks

        # 使用正则表达式提取股票信息
        matches = re.findall(self.STOCK_PATTERN, response)

        if matches:
            for match in matches:
                symbol = match[0]
                name = match[1].strip()
                pe = float(match[2])
                roe = float(match[3])

                # 提取理由（如果有）
                reasoning_pattern = self.REASONING_PATTERN_TEMPLATE.format(symbol=symbol, name=name)
                reasoning_match = re.search(reasoning_pattern, response, re.DOTALL)
                reasoning = ""
                if reasoning_match:
                    reasoning_text = reasoning_match.group(0)
                    # 提取理由部分
                    reason_start = reasoning_text.find(self.REASONING_PREFIX)
                    if reason_start != -1:
                        reasoning = reasoning_text[reason_start + len(self.REASONING_PREFIX):].strip()

                stocks.append({
                    "symbol": symbol,
                    "name": name,
                    "pe": pe,
                    "roe": roe,
                    "reasoning": reasoning
                })

        # 如果没有找到明确的股票信息，尝试其他解析方式
        if not stocks:
            # 尝试提取可能的股票代码
            codes = re.findall(self.CODE_PATTERN, response)
            if codes:
                # 简单的回退方案，创建基本的股票信息
                for code in codes[:self.DEFAULT_LIMIT]:
                    stocks.append({
                        "symbol": code,
                        "name": "待确认",
                        "pe": 0.0,
                        "roe": 0.0,
                        "reasoning": "AI响应格式异常，股票信息不完整"
                    })

        return stocks

    def _format_criteria_for_display(self, criteria: Dict[str, Dict[str, float]]) -> str:
        """
        格式化筛选条件用于显示

        Args:
            criteria: 筛选条件字典

        Returns:
            格式化后的筛选条件字符串
        """
        conditions = []
        for key, value in criteria.items():
            if isinstance(value, dict):
                for op, val in value.items():
                    if op == "max":
                        conditions.append(f"{key} ≤ {val}")
                    elif op == "min":
                        conditions.append(f"{key} ≥ {val}")
                    elif op == "eq":
                        conditions.append(f"{key} = {val}")
        return "，".join(conditions) if conditions else "无"