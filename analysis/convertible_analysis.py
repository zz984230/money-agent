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
from data.fetchers.akshare_financial_fetcher import AKShareFinancialFetcher


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
        self.financial_fetcher = None  # 延迟初始化，按需加载

    def analyze_convertible(
        self,
        cb_code: str,
        cb_name: str,
        use_ai_only: bool = False
    ) -> Optional[Dict]:
        """
        分析单个可转债

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称
            use_ai_only: 是否仅使用AI分析（不依赖实时数据）

        Returns:
            包含可转债分析结果的字典：
            {
                "cb_code": str,
                "cb_name": str,
                "data": dict,  # 可转债数据（如果有）
                "analysis": str,  # AI分析文本
                "summary": str  # 分析摘要
            }
            如果分析失败则返回 None
        """
        try:
            # 验证参数
            if not use_ai_only:
                self._validate_cb_code(cb_code)
            self._validate_cb_name(cb_name)

            logger.info(f"开始分析可转债 {cb_code} - {cb_name}")

            # 1. 尝试从可转债列表中获取该转债的实时数据
            cb_data_dict = None
            data_summary = "暂无实时市场数据"
            financial_summary = ""

            if not use_ai_only:
                cb_list = self.get_convertible_list()
                if cb_list is not None:
                    # 查找对应代码的可转债数据
                    for cb in cb_list:
                        if cb['cb_code'] == cb_code:
                            cb_data_dict = cb
                            break

                    if cb_data_dict is not None:
                        logger.debug(f"获取到可转债数据: {cb_data_dict}")
                        data_summary = self._format_convertible_dict(cb_data_dict)

                        # 2. 获取正股财务数据（通过 AKShare）
                        stock_code = cb_data_dict.get('stock_code', '')
                        if stock_code:
                            try:
                                financial_summary = self._get_stock_financial_data(stock_code)
                            except RuntimeError as e:
                                # 财务数据获取失败，仅记录警告，继续分析
                                logger.warning(f"获取正股财务数据失败: {e}")
                                financial_summary = "（财务数据暂时无法获取）"
                    else:
                        logger.info(f"在列表中未找到可转债 {cb_code}，将使用AI知识库进行分析")
                else:
                    logger.info("未获取到可转债列表，将使用AI知识库进行分析")

            # 3. 构建提示词
            prompt = self.prompt_builder.build_convertible_analysis_prompt(
                cb_code=cb_code,
                cb_name=cb_name
            )
            # 添加数据摘要到提示词
            prompt = f"{prompt}\n\n市场数据：\n{data_summary}"
            if financial_summary:
                prompt = f"{prompt}\n\n正股财务数据：\n{financial_summary}"

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
                "data": cb_data_dict if cb_data_dict else {},
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

    def analyze_convertible_by_name(self, cb_name: str) -> Optional[Dict]:
        """
        根据可转债名称分析可转债

        Args:
            cb_name: 可转债名称（支持模糊匹配）

        Returns:
            包含可转债分析结果的字典，如果分析失败则返回 None
        """
        try:
            # 验证名称
            if not cb_name or not cb_name.strip():
                logger.warning("可转债名称不能为空")
                return None

            cb_name = cb_name.strip()
            logger.info(f"根据名称查找可转债：{cb_name}")

            # 1. 获取可转债列表
            cb_list = self.get_convertible_list()

            # 2. 搜索匹配的可转债（支持模糊匹配）
            matched_cb = None
            if cb_list is not None:
                for cb in cb_list:
                    if cb_name in cb['cb_name'] or cb['cb_name'] in cb_name:
                        matched_cb = cb
                        logger.info(f"找到匹配的可转债：{cb['cb_code']} - {cb['cb_name']}")
                        break

            if matched_cb:
                # 3a. 使用找到的代码进行分析
                return self.analyze_convertible(
                    cb_code=matched_cb['cb_code'],
                    cb_name=matched_cb['cb_name']
                )
            else:
                # 3b. 未找到匹配的可转债，使用纯AI分析
                logger.info(f"未在数据列表中找到'{cb_name}'，使用AI知识库进行分析")
                return self.analyze_convertible(
                    cb_code="未知",
                    cb_name=cb_name,
                    use_ai_only=True
                )

        except Exception as e:
            logger.error(f"根据名称分析可转债时发生错误：{e}", exc_info=True)
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

            # 直接调用 AKShare 获取可转债列表
            import akshare as ak
            df = ak.bond_cb_jsl()

            if df is None or df.empty:
                logger.warning("未获取到可转债列表数据")
                return None

            logger.debug(f"成功获取可转债列表，共 {len(df)} 只")

            # 转换为统一格式，包含更多字段
            cb_list = []
            for _, row in df.iterrows():
                # 使用位置索引来访问列
                # 列顺序: 0:代码, 1:名称, 2:现价, 3:涨跌幅, 4:正股代码, 5:正股名称, 6:正股涨跌, 7:转股溢价率, 8:PB, 9:转股价, 10:转股价值, 11:转股溢价率2, 12:评级, 13:回售价, 14:强赎价, 15:规模, 16:到期日, 17:剩余年限, 18:剩余规模, 22:双低
                cb_data = {
                    "cb_code": str(row.iloc[0]) if len(row) > 0 else '',
                    "cb_name": str(row.iloc[1]) if len(row) > 1 else '',
                    "price": float(row.iloc[2]) if len(row) > 2 else 0.0,
                    "change": float(row.iloc[3]) if len(row) > 3 else 0.0,
                    "stock_code": str(row.iloc[4]) if len(row) > 4 else '',  # 正股代码
                    "stock_name": str(row.iloc[5]) if len(row) > 5 else '',  # 正股名称
                }

                # 添加更多可用字段
                if len(row) > 7 and row.iloc[7] is not None:
                    cb_data["premium_rate"] = float(row.iloc[7])  # 转股溢价率
                if len(row) > 9 and row.iloc[9] is not None:
                    cb_data["conversion_price"] = float(row.iloc[9])  # 转股价
                if len(row) > 10 and row.iloc[10] is not None:
                    cb_data["conversion_value"] = float(row.iloc[10])  # 转股价值
                if len(row) > 12 and row.iloc[12] is not None:
                    cb_data["bond_rating"] = str(row.iloc[12])  # 债券评级
                if len(row) > 13 and row.iloc[13] is not None:
                    cb_data["put_trigger_price"] = float(row.iloc[13])  # 回售触发价
                if len(row) > 14 and row.iloc[14] is not None:
                    cb_data["call_trigger_price"] = float(row.iloc[14])  # 强赎触发价
                if len(row) > 15 and row.iloc[15] is not None:
                    cb_data["balance"] = float(row.iloc[15])  # 转债规模
                if len(row) > 16 and row.iloc[16] is not None:
                    cb_data["maturity_date"] = str(row.iloc[16])  # 到期时间
                if len(row) > 17 and row.iloc[17] is not None:
                    cb_data["remaining_years"] = float(row.iloc[17])  # 剩余年限
                if len(row) > 18 and row.iloc[18] is not None:
                    cb_data["remaining_balance"] = float(row.iloc[18])  # 剩余规模
                if len(row) > 22 and row.iloc[22] is not None:
                    cb_data["double_low"] = float(row.iloc[22])  # 双低

                if cb_data["cb_code"] and cb_data["cb_name"]:
                    cb_list.append(cb_data)

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

    def _ensure_financial_fetcher(self) -> None:
        """确保 AKShareFinancialFetcher 已初始化"""
        if self.financial_fetcher is None:
            try:
                self.financial_fetcher = AKShareFinancialFetcher()
                logger.info("AKShareFinancialFetcher 初始化成功")
            except Exception as e:
                logger.error(f"AKShareFinancialFetcher 初始化失败: {e}")
                raise RuntimeError(f"财务数据获取器初始化失败: {e}")

    def _get_stock_financial_data(self, stock_code: str) -> str:
        """
        获取正股财务数据

        Args:
            stock_code: 正股代码（6位数字，如 688798）

        Returns:
            格式化的财务数据字符串

        Raises:
            RuntimeError: 当 AKShare API 调用失败时
        """
        self._ensure_financial_fetcher()

        logger.debug(f"获取正股财务数据: {stock_code}")

        # 获取最新财务数据
        financials = self.financial_fetcher.get_financial_abstract(stock_code)

        if financials is None:
            raise RuntimeError(f"未能获取 {stock_code} 的财务数据")

        # 格式化财务数据
        return self.financial_fetcher.format_financial_data(financials)

    def _format_convertible_dict(self, cb_dict: Dict) -> str:
        """
        格式化可转债字典数据用于显示

        Args:
            cb_dict: 可转债数据字典

        Returns:
            格式化后的数据字符串
        """
        if not cb_dict:
            return "无数据"

        lines = []
        lines.append(f"可转债代码: {cb_dict.get('cb_code', 'N/A')}")
        lines.append(f"可转债名称: {cb_dict.get('cb_name', 'N/A')}")
        lines.append(f"现价: {cb_dict.get('price', 'N/A')}")
        lines.append(f"涨跌幅: {cb_dict.get('change', 'N/A')}%")

        # 添加正股信息
        if cb_dict.get('stock_code'):
            lines.append(f"正股代码: {cb_dict.get('stock_code')}")
        if cb_dict.get('stock_name'):
            lines.append(f"正股名称: {cb_dict.get('stock_name')}")

        # 添加转股信息
        if cb_dict.get('conversion_price'):
            lines.append(f"转股价: {cb_dict.get('conversion_price')}")
        if cb_dict.get('conversion_value'):
            lines.append(f"转股价值: {cb_dict.get('conversion_value')}")
        if cb_dict.get('premium_rate'):
            lines.append(f"转股溢价率: {cb_dict.get('premium_rate')}%")

        # 添加债券信息
        if cb_dict.get('bond_rating'):
            lines.append(f"债券评级: {cb_dict.get('bond_rating')}")
        if cb_dict.get('balance'):
            lines.append(f"转债规模: {cb_dict.get('balance')} 亿元")
        if cb_dict.get('remaining_balance'):
            lines.append(f"剩余规模: {cb_dict.get('remaining_balance')} 亿元")

        # 添加触发价格
        if cb_dict.get('put_trigger_price'):
            lines.append(f"回售触发价: {cb_dict.get('put_trigger_price')}")
        if cb_dict.get('call_trigger_price'):
            lines.append(f"强赎触发价: {cb_dict.get('call_trigger_price')}")

        # 添加时间信息
        if cb_dict.get('maturity_date'):
            lines.append(f"到期时间: {cb_dict.get('maturity_date')}")
        if cb_dict.get('remaining_years'):
            lines.append(f"剩余年限: {cb_dict.get('remaining_years')} 年")

        # 添加双低值
        if cb_dict.get('double_low'):
            lines.append(f"双低值: {cb_dict.get('double_low')}")

        return "\n".join(lines)

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
