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

    def __init__(self, agent: GLMAgent):
        """
        初始化股票筛选器

        Args:
            agent: GLM AI Agent 实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()

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
        if "没有找到" in response or "无符合条件" in response or not response.strip():
            return stocks

        # 使用正则表达式提取股票信息
        stock_pattern = r'(\d{6})\s+([^\d\n]+)\s+-\s+PE:\s*([\d.]+)\s+-\s+ROE:\s*([\d.]+)%'
        matches = re.findall(stock_pattern, response)

        if matches:
            for match in matches:
                symbol = match[0]
                name = match[1].strip()
                pe = float(match[2])
                roe = float(match[3])

                # 提取理由（如果有）
                reasoning_pattern = rf'{symbol}\s+{name}.*?(?=下一个|\n\n|\Z)'
                reasoning_match = re.search(reasoning_pattern, response, re.DOTALL)
                reasoning = ""
                if reasoning_match:
                    reasoning_text = reasoning_match.group(0)
                    # 提取理由部分
                    reason_start = reasoning_text.find("理由：")
                    if reason_start != -1:
                        reasoning = reasoning_text[reason_start + 3:].strip()

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
            code_pattern = r'(\d{6})\s+[^\d\n]+'
            codes = re.findall(code_pattern, response)
            if codes:
                # 简单的回退方案，创建基本的股票信息
                default_limit = 10  # 默认限制
                for code in codes[:default_limit]:
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