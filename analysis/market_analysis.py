"""
Market Analysis Module
市场分析模块
"""

import logging
import re
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher


# 配置日志
logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """市场分析器，用于分析大盘指数和市场情绪"""

    # 类常量
    SUMMARY_MAX_LENGTH = 200
    INDEX_CODE_PATTERN = r'^\d{6}$'
    DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'

    def __init__(self, agent: BaseAgent):
        """
        初始化市场分析器

        Args:
            agent: AI Agent 实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_index(
        self,
        index_code: str,
        date: str
    ) -> Optional[Dict]:
        """
        分析大盘指数

        Args:
            index_code: 指数代码（如 000001 上证指数）
            date: 分析日期，格式：YYYY-MM-DD

        Returns:
            包含指数分析结果的字典：
            {
                "index_code": str,
                "date": str,
                "data": dict,  # 指数数据
                "analysis": str,  # AI分析文本
                "summary": str  # 分析摘要
            }
            如果分析失败则返回 None
        """
        try:
            # 验证参数
            self._validate_index_code(index_code)
            self._validate_date(date)

            logger.info(f"开始分析指数 {index_code}，日期：{date}")

            # 1. 获取指数数据
            index_data = self.fetcher.get_index_daily(index_code, date)
            if index_data is None or index_data.empty:
                logger.warning(f"未获取到指数 {index_code} 在 {date} 的数据")
                return None

            logger.debug(f"成功获取指数数据，共 {len(index_data)} 条记录")

            # 2. 构建提示词
            data_summary = self._format_index_data(index_data)
            prompt = self.prompt_builder.build_market_analysis_prompt(
                index_code=index_code,
                date=date
            )
            # 添加数据摘要到提示词
            prompt = f"{prompt}\n\n实际数据：\n{data_summary}"

            # 3. AI 分析
            logger.info("调用AI进行分析...")
            analysis = self.agent.chat(prompt)
            if not analysis:
                logger.warning("AI分析失败，返回空响应")
                return None

            logger.debug(f"AI分析完成，分析文本长度：{len(analysis)} 字符")

            # 4. 提取摘要
            summary = self._extract_summary(analysis)

            # 5. 构建返回结果
            result = {
                "index_code": index_code,
                "date": date,
                "data": index_data.to_dict('records')[-1] if len(index_data) > 0 else {},
                "analysis": analysis,
                "summary": summary
            }

            logger.info(f"指数分析完成：{index_code}")
            return result

        except ValueError as e:
            logger.error(f"参数验证失败：{e}")
            raise
        except Exception as e:
            logger.error(f"分析指数时发生错误：{e}", exc_info=True)
            return None

    def analyze_sentiment(self) -> Optional[Dict]:
        """
        分析市场情绪

        Returns:
            包含市场情绪分析的字典：
            {
                "sentiment": str,  # 情绪分析结果
                "timestamp": str  # 分析时间戳
            }
            如果分析失败则返回 None
        """
        try:
            logger.info("开始分析市场情绪")

            # 1. 获取市场涨跌数据
            market_stats = self.fetcher.get_market_stats()
            if market_stats is None:
                logger.warning("未获取到市场统计数据")
                return None

            logger.debug(f"市场统计数据：{market_stats}")

            # 2. 构建情绪分析提示词
            prompt = self._build_sentiment_prompt(market_stats)

            # 3. AI 分析情绪
            logger.info("调用AI进行情绪分析...")
            sentiment_analysis = self.agent.chat(prompt)
            if not sentiment_analysis:
                logger.warning("AI情绪分析失败，返回空响应")
                return None

            logger.debug(f"情绪分析完成，分析文本长度：{len(sentiment_analysis)} 字符")

            # 4. 构建返回结果
            result = {
                "sentiment": sentiment_analysis,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info("市场情绪分析完成")
            return result

        except Exception as e:
            logger.error(f"分析市场情绪时发生错误：{e}", exc_info=True)
            return None

    def _format_index_data(self, df: pd.DataFrame) -> str:
        """
        格式化指数数据用于显示

        Args:
            df: 指数数据DataFrame

        Returns:
            格式化后的数据字符串
        """
        if df.empty:
            return "无数据"

        # 获取最近的数据
        recent = df.tail(5)

        lines = []
        for _, row in recent.iterrows():
            date = row.get('date', 'N/A')
            close = row.get('close', row.get('收盘', 'N/A'))
            volume = row.get('volume', row.get('成交量', 'N/A'))
            lines.append(f"日期: {date}, 收盘: {close}, 成交量: {volume}")

        return "\n".join(lines)

    def _build_sentiment_prompt(self, market_stats: Dict) -> str:
        """
        构建市场情绪分析提示词

        Args:
            market_stats: 市场统计数据

        Returns:
            情绪分析提示词
        """
        prompt = f"""请根据以下市场数据分析当前市场情绪：

市场统计数据：
- 上涨股票数：{market_stats['up_count']}
- 下跌股票数：{market_stats['down_count']}
- 平盘股票数：{market_stats['unchanged_count']}
- 涨停板数量：{market_stats['limit_up_count']}
- 跌停板数量：{market_stats['limit_down_count']}
- 总成交额：{market_stats['total_amount']:.2f}元

请从以下几个方面分析市场情绪：
1. 整体情绪判断（偏多/偏多/中性）
2. 市场活跃度分析
3. 赚钱效应评估
4. 投资者风险偏好
5. 综合建议

请提供简洁、客观的情绪分析。"""

        return prompt

    def _extract_summary(self, analysis: str) -> str:
        """
        提取分析摘要

        Args:
            analysis: 完整的分析文本

        Returns:
            分析摘要（前200字）
        """
        if not analysis:
            return ""

        # 如果文本长度小于等于最大长度，直接返回
        if len(analysis) <= self.SUMMARY_MAX_LENGTH:
            return analysis

        # 返回前200字作为摘要
        summary = analysis[:self.SUMMARY_MAX_LENGTH]

        # 如果摘要不是完整句子，尝试在最后一个句号处截断
        last_period = summary.rfind('。')
        if last_period > self.SUMMARY_MAX_LENGTH // 2:
            summary = summary[:last_period + 1]

        return summary

    def _validate_index_code(self, index_code: str) -> None:
        """
        验证指数代码格式

        Args:
            index_code: 指数代码

        Raises:
            ValueError: 当指数代码格式无效时
        """
        if not index_code:
            raise ValueError("指数代码不能为空")

        if not isinstance(index_code, str):
            raise ValueError("指数代码必须是字符串类型")

        if not re.match(self.INDEX_CODE_PATTERN, index_code):
            raise ValueError(
                f"无效的指数代码格式：{index_code}，"
                f"应为6位数字（如000001）"
            )

    def _validate_date(self, date: str) -> None:
        """
        验证日期格式

        Args:
            date: 日期字符串

        Raises:
            ValueError: 当日期格式无效时
        """
        if not date:
            raise ValueError("日期不能为空")

        if not isinstance(date, str):
            raise ValueError("日期必须是字符串类型")

        if not re.match(self.DATE_PATTERN, date):
            raise ValueError(
                f"无效的日期格式：{date}，"
                f"应为YYYY-MM-DD格式（如2024-01-15）"
            )

        # 验证日期是否有效
        try:
            year, month, day = map(int, date.split('-'))
            if not (1 <= month <= 12):
                raise ValueError(f"无效的月份：{month}")
            if not (1 <= day <= 31):
                raise ValueError(f"无效的日期：{day}")
        except ValueError as e:
            raise ValueError(f"日期值无效：{e}")
