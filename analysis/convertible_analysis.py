"""
Convertible Bond Analysis Module
可转债分析模块
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


class ConvertibleBondAnalyzer:
    """可转债分析器，用于分析可转债"""

    # 类常量
    SUMMARY_MAX_LENGTH = 200
    CB_CODE_PATTERN = r'^\d{6}$'
    MIN_TOP_N = 1
    DEFAULT_DAYS = 30  # 默认获取过去30天的数据
    DEFAULT_MAX_PRICE = 110.0  # 默认最大价格
    DEFAULT_MAX_PREMIUM = 30.0  # 默认最大溢价率
    DEFAULT_TOP_N = 10  # 默认返回前N个

    def __init__(self, agent: BaseAgent):
        """
        初始化可转债分析器

        Args:
            agent: AI Agent 实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_convertible(
        self,
        cb_code: str,
        cb_name: str
    ) -> Optional[Dict]:
        """
        分析单个可转债

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称

        Returns:
            包含可转债分析结果的字典：
            {
                "cb_code": str,
                "cb_name": str,
                "data": dict,  # 可转债数据
                "analysis": str,  # AI分析文本
                "summary": str  # 分析摘要
            }
            如果分析失败则返回 None
        """
        try:
            # 验证参数
            self._validate_cb_code(cb_code)
            self._validate_cb_name(cb_name)

            logger.info(f"开始分析可转债 {cb_code} - {cb_name}")

            # 1. 获取可转债历史数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=self.DEFAULT_DAYS)).strftime("%Y-%m-%d")

            cb_data = self.fetcher.get_convertible_daily(
                symbol=cb_code,
                start_date=start_date,
                end_date=end_date
            )

            if cb_data is None or cb_data.empty:
                logger.warning(f"未获取到可转债 {cb_code} 的历史数据")
                return None

            logger.debug(f"成功获取可转债数据，共 {len(cb_data)} 条记录")

            # 2. 构建提示词
            data_summary = self._format_convertible_data(cb_data)
            prompt = self.prompt_builder.build_convertible_analysis_prompt(
                cb_code=cb_code,
                cb_name=cb_name
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
                "cb_code": cb_code,
                "cb_name": cb_name,
                "data": cb_data.to_dict('records')[-1] if len(cb_data) > 0 else {},
                "analysis": analysis,
                "summary": summary
            }

            logger.info(f"可转债分析完成：{cb_code} - {cb_name}")
            return result

        except ValueError as e:
            logger.error(f"参数验证失败：{e}")
            raise
        except Exception as e:
            logger.error(f"分析可转债时发生错误：{e}", exc_info=True)
            return None

    def get_convertible_list(self) -> Optional[List[Dict]]:
        """
        获取可转债列表

        Returns:
            可转债列表，每个元素包含 {"cb_code": ..., "cb_name": ...}
            如果获取失败则返回 None
        """
        try:
            logger.info("开始获取可转债列表")

            # 使用AKShareFetcher获取可转债列表
            cb_list_raw = self.fetcher.get_convertible_list()

            if cb_list_raw is None or len(cb_list_raw) == 0:
                logger.warning("未获取到可转债列表数据")
                return None

            logger.debug(f"成功获取可转债列表，共 {len(cb_list_raw)} 只")

            # 转换为统一格式
            cb_list = []
            for item in cb_list_raw:
                # 尝试不同的字段名
                code = item.get('代码') or item.get('code') or item.get('symbol', '')
                name = item.get('名称') or item.get('name') or item.get('cb_name', '')

                if code and name:
                    cb_list.append({
                        "cb_code": str(code),
                        "cb_name": str(name),
                        "price": float(item.get('现价', 0)),
                        "change": float(item.get('涨跌幅', 0))
                    })

            logger.info(f"可转债列表格式化完成，共 {len(cb_list)} 只")
            return cb_list

        except Exception as e:
            logger.error(f"获取可转债列表时发生错误：{e}", exc_info=True)
            return None

    def screen_double_low(
        self,
        max_price: float = DEFAULT_MAX_PRICE,
        max_premium: float = DEFAULT_MAX_PREMIUM,
        top_n: int = DEFAULT_TOP_N
    ) -> Optional[List[Dict]]:
        """
        双低策略筛选

        双低策略：选择价格低、溢价率低的可转债
        价格 = 可转债当前价格
        溢价率 = (转股价 - 正股价) / 正股价 * 100%

        Args:
            max_price: 最大价格（默认 110）
            max_premium: 最大溢价率（默认 30%）
            top_n: 返回前 N 个（默认 10）

        Returns:
            筛选出的可转债列表，按（价格 + 溢价率）升序排列
        """
        try:
            # 验证参数
            self._validate_screen_params(max_price, max_premium, top_n)

            logger.info(f"开始双低策略筛选，max_price={max_price}, max_premium={max_premium}%, top_n={top_n}")

            # 1. 获取可转债列表
            cb_list = self.get_convertible_list()
            if cb_list is None:
                logger.warning("未获取到可转债列表")
                return None

            # 2. 计算每个可转债的双低值并筛选
            filtered_cbs = []
            for cb in cb_list:
                # 获取可转债价格
                cb_price = cb.get('price', 0)

                # 计算溢价率（简化计算，实际应获取转股价和正股价）
                # 这里使用涨跌幅作为代理指标
                premium = abs(cb.get('change', 0))

                # 筛选符合条件的可转债
                if cb_price <= max_price and premium <= max_premium:
                    double_low = cb_price + premium
                    filtered_cbs.append({
                        "cb_code": cb["cb_code"],
                        "cb_name": cb["cb_name"],
                        "price": cb_price,
                        "premium": premium,
                        "double_low": double_low
                    })

            if not filtered_cbs:
                logger.warning("没有符合条件的可转债")
                return []

            logger.debug(f"筛选到 {len(filtered_cbs)} 只符合条件的可转债")

            # 3. 按双低值升序排序
            filtered_cbs.sort(key=lambda x: x["double_low"])

            # 4. 返回前 N 个
            result = filtered_cbs[:top_n]

            logger.info(f"双低策略筛选完成，返回 {len(result)} 只可转债")
            return result

        except ValueError as e:
            logger.error(f"参数验证失败：{e}")
            raise
        except Exception as e:
            logger.error(f"双低策略筛选时发生错误：{e}", exc_info=True)
            return None

    def _format_convertible_data(self, df: pd.DataFrame) -> str:
        """
        格式化可转债数据用于显示

        Args:
            df: 可转债数据DataFrame

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

    def _validate_cb_code(self, cb_code: str) -> None:
        """
        验证可转债代码格式

        Args:
            cb_code: 可转债代码

        Raises:
            ValueError: 当可转债代码格式无效时
        """
        if not cb_code:
            raise ValueError("可转债代码不能为空")

        if not isinstance(cb_code, str):
            raise ValueError("可转债代码必须是字符串类型")

        if not re.match(self.CB_CODE_PATTERN, cb_code):
            raise ValueError(
                f"无效的可转债代码格式：{cb_code}，"
                f"应为6位数字（如113527）"
            )

    def _validate_cb_name(self, cb_name: str) -> None:
        """
        验证可转债名称

        Args:
            cb_name: 可转债名称

        Raises:
            ValueError: 当可转债名称无效时
        """
        if not cb_name:
            raise ValueError("可转债名称不能为空")

        if not isinstance(cb_name, str):
            raise ValueError("可转债名称必须是字符串类型")

    def _validate_screen_params(
        self,
        max_price: float,
        max_premium: float,
        top_n: int
    ) -> None:
        """
        验证双低策略筛选参数

        Args:
            max_price: 最大价格
            max_premium: 最大溢价率
            top_n: 返回前N个

        Raises:
            ValueError: 当参数无效时
        """
        if max_price <= 0:
            raise ValueError("max_price必须大于0")

        if max_premium <= 0:
            raise ValueError("max_premium必须大于0")

        if top_n < self.MIN_TOP_N:
            raise ValueError(f"top_n必须大于等于{self.MIN_TOP_N}")
