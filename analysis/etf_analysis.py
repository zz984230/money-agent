"""
ETF Analysis Module
ETF分析模块
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher


# 配置日志
logger = logging.getLogger(__name__)


class ETFAnalyzer:
    """ETF 分析器，用于分析ETF基金"""

    # 类常量
    SUMMARY_MAX_LENGTH = 200
    ETF_CODE_PATTERN = r'^\d{6}$'
    MIN_TOP_N = 1
    DEFAULT_DAYS = 30  # 默认获取过去30天的数据

    def __init__(self, agent: BaseAgent):
        """
        初始化ETF分析器

        Args:
            agent: AI Agent 实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_etf(
        self,
        etf_code: str,
        etf_name: str
    ) -> Optional[Dict]:
        """
        分析单个ETF

        Args:
            etf_code: ETF代码（如 510300）
            etf_name: ETF名称（如 沪深300ETF）

        Returns:
            包含ETF分析结果的字典：
            {
                "etf_code": str,
                "etf_name": str,
                "data": dict,  # ETF数据
                "analysis": str,  # AI分析文本
                "summary": str  # 分析摘要
            }
            如果分析失败则返回 None
        """
        try:
            # 验证参数
            self._validate_etf_code(etf_code)
            self._validate_etf_name(etf_name)

            logger.info(f"开始分析ETF {etf_code} - {etf_name}")

            # 1. 获取ETF历史数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=self.DEFAULT_DAYS)).strftime("%Y-%m-%d")

            etf_data = self.fetcher.get_etf_daily(
                symbol=etf_code,
                start_date=start_date,
                end_date=end_date
            )

            if etf_data is None or etf_data.empty:
                logger.warning(f"未获取到ETF {etf_code} 的历史数据")
                return None

            logger.debug(f"成功获取ETF数据，共 {len(etf_data)} 条记录")

            # 2. 构建提示词
            data_summary = self._format_etf_data(etf_data)
            prompt = self.prompt_builder.build_etf_analysis_prompt(
                etf_code=etf_code,
                etf_name=etf_name
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
                "etf_code": etf_code,
                "etf_name": etf_name,
                "data": etf_data.to_dict('records')[-1] if len(etf_data) > 0 else {},
                "analysis": analysis,
                "summary": summary
            }

            logger.info(f"ETF分析完成：{etf_code} - {etf_name}")
            return result

        except ValueError as e:
            logger.error(f"参数验证失败：{e}")
            raise
        except Exception as e:
            logger.error(f"分析ETF时发生错误：{e}", exc_info=True)
            return None

    def get_etf_list(self) -> Optional[List[Dict]]:
        """
        获取ETF列表

        Returns:
            ETF列表，每个元素包含 {"etf_code": ..., "etf_name": ...}
            如果获取失败则返回 None
        """
        try:
            logger.info("开始获取ETF列表")

            # 使用AKShareFetcher获取ETF列表
            etf_list_raw = self.fetcher.get_etf_list()

            if etf_list_raw is None or len(etf_list_raw) == 0:
                logger.warning("未获取到ETF列表数据")
                return None

            logger.debug(f"成功获取ETF列表，共 {len(etf_list_raw)} 只")

            # 转换为统一格式
            etf_list = []
            for item in etf_list_raw:
                # 尝试不同的字段名
                code = item.get('代码') or item.get('code') or item.get('symbol', '')
                name = item.get('名称') or item.get('name') or item.get('etf_name', '')

                if code and name:
                    etf_list.append({
                        "etf_code": str(code),
                        "etf_name": str(name),
                        "category": item.get('类别') or item.get('category', '其他')
                    })

            logger.info(f"ETF列表格式化完成，共 {len(etf_list)} 只")
            return etf_list

        except Exception as e:
            logger.error(f"获取ETF列表时发生错误：{e}", exc_info=True)
            return None

    def recommend_etfs(
        self,
        category: str,
        top_n: int = 5
    ) -> Optional[List[Dict]]:
        """
        推荐ETF

        Args:
            category: ETF类别（如 宽基、行业、债券等）
            top_n: 返回前N个

        Returns:
            推荐的ETF列表
            如果获取失败则返回 None
        """
        try:
            # 验证参数
            if top_n < self.MIN_TOP_N:
                raise ValueError(f"top_n必须大于等于{self.MIN_TOP_N}")

            if not category or not isinstance(category, str):
                raise ValueError("category必须是非空字符串")

            logger.info(f"开始推荐ETF，类别：{category}，数量：{top_n}")

            # 1. 获取ETF列表
            etf_list = self.get_etf_list()
            if etf_list is None:
                logger.warning("未获取到ETF列表")
                return None

            # 2. 按category筛选
            filtered_etfs = [
                etf for etf in etf_list
                if category.lower() in etf.get('category', '').lower() or
                   category in etf.get('etf_name', '')
            ]

            if not filtered_etfs:
                logger.warning(f"未找到类别为 {category} 的ETF")
                return []

            logger.debug(f"筛选到 {len(filtered_etfs)} 只{category}类ETF")

            # 3. AI排序推荐
            # 构建ETF信息字符串
            candidate_count = min(len(filtered_etfs), top_n * 2)
            etf_info = "\n".join([
                f"{i+1}. {etf['etf_name']} ({etf['etf_code']})"
                for i, etf in enumerate(filtered_etfs[:candidate_count])
            ])

            prompt = f"""请从以下{category}类ETF中推荐最合适的{top_n}只：

{etf_info}

请综合考虑：
1. 跟踪标的的代表性和稳定性
2. 基金规模和流动性
3. 费率水平
4. 跟踪误差
5. 市场认可度

请按推荐优先级排序，返回ETF代码和名称，并简要说明推荐理由。"""

            logger.info("调用AI进行ETF推荐...")
            ai_response = self.agent.chat(prompt)

            if ai_response:
                logger.debug(f"AI推荐完成，响应长度：{len(ai_response)} 字符")
                # 从AI响应中提取ETF代码
                recommended_codes = self._extract_etf_codes(ai_response, filtered_etfs)

                if recommended_codes:
                    # 按AI推荐的顺序构建结果
                    result = []
                    for code in recommended_codes[:top_n]:
                        for etf in filtered_etfs:
                            if etf['etf_code'] == code:
                                result.append(etf)
                                break

                    logger.info(f"ETF推荐完成，推荐数量：{len(result)}")
                    return result

            # 如果AI推荐失败，返回前top_n个
            logger.warning("AI推荐失败，返回筛选结果的前{top_n}个")
            return filtered_etfs[:top_n]

        except ValueError as e:
            logger.error(f"参数验证失败：{e}")
            raise
        except Exception as e:
            logger.error(f"推荐ETF时发生错误：{e}", exc_info=True)
            return None

    def _format_etf_data(self, df: pd.DataFrame) -> str:
        """
        格式化ETF数据用于显示

        Args:
            df: ETF数据DataFrame

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
            amount = row.get('amount', row.get('成交额', 'N/A'))
            lines.append(f"日期: {date}, 收盘: {close}, 成交量: {volume}, 成交额: {amount}")

        return "\n".join(lines)

    def _extract_etf_codes(self, ai_response: str, etf_list: List[Dict]) -> List[str]:
        """
        从AI响应中提取ETF代码

        Args:
            ai_response: AI响应文本
            etf_list: ETF列表

        Returns:
            提取的ETF代码列表
        """
        codes = []
        valid_codes = {etf['etf_code'] for etf in etf_list}

        # 查找所有6位数字代码
        pattern = r'\b(\d{6})\b'
        matches = re.findall(pattern, ai_response)

        for code in matches:
            if code in valid_codes and code not in codes:
                codes.append(code)

        # 如果没有找到，按原始顺序返回
        if not codes:
            return [etf['etf_code'] for etf in etf_list]

        return codes

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

    def _validate_etf_code(self, etf_code: str) -> None:
        """
        验证ETF代码格式

        Args:
            etf_code: ETF代码

        Raises:
            ValueError: 当ETF代码格式无效时
        """
        if not etf_code:
            raise ValueError("ETF代码不能为空")

        if not isinstance(etf_code, str):
            raise ValueError("ETF代码必须是字符串类型")

        if not re.match(self.ETF_CODE_PATTERN, etf_code):
            raise ValueError(
                f"无效的ETF代码格式：{etf_code}，"
                f"应为6位数字（如510300）"
            )

    def _validate_etf_name(self, etf_name: str) -> None:
        """
        验证ETF名称

        Args:
            etf_name: ETF名称

        Raises:
            ValueError: 当ETF名称无效时
        """
        if not etf_name:
            raise ValueError("ETF名称不能为空")

        if not isinstance(etf_name, str):
            raise ValueError("ETF名称必须是字符串类型")
