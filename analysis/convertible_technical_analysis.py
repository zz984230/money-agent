"""
可转债技术面与条款分析模块
Convertible Bond Technical and Terms Analysis Module
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher


logger = logging.getLogger(__name__)


@dataclass
class ConvertibleTechnicalData:
    """可转债技术面数据"""

    # 基础信息
    cb_code: str
    cb_name: str

    # 基础行情
    price: float
    change_percent: float
    volume: float
    amount: float

    # 转股相关
    conversion_price: float      # 转股价
    conversion_value: float      # 转股价值
    premium_rate: float          # 转股溢价率

    # 债券属性
    bond_rating: str             # 评级
    pure_bond_value: float       # 纯债价值
    ytm: float                   # 到期收益率

    # 条款信息
    call_trigger_price: float    # 强赎触发价
    put_trigger_price: float     # 回售触发价
    conversion_trigger_price: float  # 下修触发价

    # 市场深度
    bid_price: List[float]       # 买一到买五
    ask_price: List[float]       # 卖一到卖五
    bid_volume: List[float]      # 买量
    ask_volume: List[float]      # 卖量

    # 技术指标
    ma5: float                   # 5日均线
    ma20: float                  # 20日均线
    volatility_20d: float        # 20日波动率


@dataclass
class TechnicalAnalysisResult:
    """技术分析结果"""
    technical_data: ConvertibleTechnicalData
    analysis: str                # AI分析文本
    signals: List[str]           # 交易信号列表
    summary: str                 # 分析摘要
    recommendation: str          # 投资建议


class ConvertibleBondTechnicalAnalyzer:
    """可转债技术面分析器"""

    # 类常量
    SUMMARY_MAX_LENGTH = 200
    CB_CODE_PATTERN = r'^\d{6}$'
    DEFAULT_HISTORY_DAYS = 30  # 默认获取过去30天的历史数据

    def __init__(self, agent: BaseAgent):
        """
        初始化技术面分析器

        Args:
            agent: AI Agent实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()

    def analyze_technical(
        self,
        cb_input: str,
        cb_name: Optional[str] = None
    ) -> Optional[TechnicalAnalysisResult]:
        """
        分析可转债技术面

        Args:
            cb_input: 可转债代码或名称
            cb_name: 可转债名称（可选，如果cb_input是代码时可省略，将自动查找）

        Returns:
            TechnicalAnalysisResult对象，如果分析失败则返回None
        """
        try:
            # 验证参数
            if not cb_input or not cb_input.strip():
                logger.warning("可转债代码或名称不能为空")
                return None

            cb_input = cb_input.strip()

            # 判断输入是代码还是名称
            # 如果是6位数字，视为代码；否则视为名称
            if re.match(self.CB_CODE_PATTERN, cb_input):
                cb_code = cb_input
                # 如果没有提供名称，自动查找
                if not cb_name or not cb_name.strip():
                    cb_name = self.fetcher.get_convertible_name_by_code(cb_code)
                    if not cb_name:
                        logger.warning(f"未找到代码为 {cb_code} 的可转债")
                        return None
                else:
                    cb_name = cb_name.strip()
            else:
                # 通过名称查找代码
                cb_name = cb_input
                cb_code = self.fetcher.get_convertible_by_name(cb_name)
                if not cb_code:
                    logger.warning(f"未找到可转债: {cb_name}")
                    return None

            logger.info(f"开始技术分析：{cb_code} - {cb_name}")

            # 1. 构建技术数据
            technical_data = self._build_technical_data(cb_code, cb_name)

            # 2. 调用AI分析
            analysis = self._ai_only_analysis(technical_data)

            if not analysis:
                logger.warning("AI分析失败，返回空响应")
                return None

            # 3. 提取结构化信息
            signals = self._extract_signals(analysis)
            summary = self._extract_summary(analysis)
            recommendation = self._extract_recommendation(analysis)

            # 4. 构建结果
            result = TechnicalAnalysisResult(
                technical_data=technical_data,
                analysis=analysis,
                signals=signals,
                summary=summary,
                recommendation=recommendation
            )

            logger.info(f"技术分析完成：{cb_code} - {cb_name}")
            return result

        except Exception as e:
            logger.error(f"技术分析时发生错误：{e}", exc_info=True)
            return None

    def _build_technical_data(
        self,
        cb_code: str,
        cb_name: str
    ) -> ConvertibleTechnicalData:
        """
        构建技术面数据

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称

        Returns:
            ConvertibleTechnicalData对象
        """
        try:
            # 获取详细信息（包含转股价值、溢价值等）
            detail = self.fetcher.get_convertible_detail(cb_code)

            # 优先获取实时数据
            realtime_data = self.fetcher.get_convertible_realtime(cb_code)

            # 从实时数据获取最新价格、涨跌幅、成交量等
            latest_price = 0.0
            change_percent = 0.0
            volume = 0.0
            amount = 0.0

            if realtime_data:
                latest_price = float(realtime_data.get('price', 0))
                change_percent = float(realtime_data.get('change_percent', 0))
                if change_percent == 0 and realtime_data.get('change'):
                    # 如果没有涨跌幅百分比，尝试用涨跌额计算
                    change = float(realtime_data.get('change', 0))
                    if latest_price > 0:
                        change_percent = (change / (latest_price - change)) * 100 if (latest_price - change) != 0 else 0
                volume = float(realtime_data.get('volume', 0))
                amount = float(realtime_data.get('amount', 0))

            # 从详细信息获取转股相关数据
            conversion_price = 0.0
            conversion_value = 0.0
            premium_rate = 0.0
            pure_bond_value = 0.0
            call_trigger_price = 0.0
            put_trigger_price = 0.0

            if detail:
                conversion_price = float(detail.get('conversion_price', 0))
                stock_price = float(detail.get('stock_price', 0))

                # 使用 detail 中的转股价值，或者根据正股价计算
                conversion_value = float(detail.get('conversion_value', 0))
                if conversion_value == 0 and conversion_price > 0 and stock_price > 0:
                    conversion_value = (stock_price / conversion_price) * 100

                # 使用 detail 中的溢价值，或者根据实时价格和转股价值计算
                premium_rate = float(detail.get('premium_rate', 0))
                if premium_rate == 0 and conversion_value > 0 and latest_price > 0:
                    premium_rate = (latest_price / conversion_value - 1) * 100

                call_trigger_price = conversion_price * 1.3 if conversion_price > 0 else 0.0
                put_trigger_price = conversion_price * 0.7 if conversion_price > 0 else 0.0

            # 获取历史数据用于计算技术指标（均线、波动率等）
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.Timedelta(days=self.DEFAULT_HISTORY_DAYS)

            history_df = self.fetcher.get_convertible_daily(
                symbol=cb_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )

            # 计算技术指标
            ma5 = 0.0
            ma20 = 0.0
            volatility_20d = 0.0

            if history_df is not None and not history_df.empty and 'close' in history_df.columns:
                closes = history_df['close'].values

                # 计算MA5和MA20
                if len(closes) >= 5:
                    ma5 = float(np.mean(closes[-5:]))
                if len(closes) >= 20:
                    ma20 = float(np.mean(closes[-20:]))

                # 计算20日波动率
                if len(closes) >= 20:
                    returns = pd.Series(closes).pct_change().dropna()
                    if len(returns) > 0:
                        volatility_20d = float(returns.std() * np.sqrt(252) * 100)  # 年化波动率

                # 如果实时数据获取失败，从历史数据获取价格
                if latest_price == 0 and len(closes) > 0:
                    latest_price = float(closes[-1])

                # 如果实时数据获取失败，从历史数据获取成交量
                if volume == 0 and 'volume' in history_df.columns and len(history_df) > 0:
                    volume = float(history_df['volume'].iloc[-1])

                # 计算涨跌幅（如果实时数据没有）
                if change_percent == 0 and len(closes) >= 2:
                    change_percent = (closes[-1] - closes[-2]) / closes[-2] * 100

            # 构建技术数据对象
            technical_data = ConvertibleTechnicalData(
                cb_code=cb_code,
                cb_name=cb_name,
                price=latest_price,
                change_percent=change_percent,
                volume=volume,
                amount=amount,
                conversion_price=conversion_price,
                conversion_value=conversion_value,
                premium_rate=premium_rate,
                bond_rating="",            # 暂不支持
                pure_bond_value=pure_bond_value,
                ytm=0.0,                   # 暂不支持
                call_trigger_price=call_trigger_price,
                put_trigger_price=put_trigger_price,
                conversion_trigger_price=0.0,  # 暂不支持
                bid_price=[],              # 暂不支持
                ask_price=[],              # 暂不支持
                bid_volume=[],             # 暂不支持
                ask_volume=[],             # 暂不支持
                ma5=ma5,
                ma20=ma20,
                volatility_20d=volatility_20d
            )

            return technical_data

        except Exception as e:
            logger.warning(f"构建技术数据时发生错误：{e}，使用默认值")

            # 返回默认值的数据对象
            return ConvertibleTechnicalData(
                cb_code=cb_code,
                cb_name=cb_name,
                price=0.0,
                change_percent=0.0,
                volume=0.0,
                amount=0.0,
                conversion_price=0.0,
                conversion_value=0.0,
                premium_rate=0.0,
                bond_rating="",
                pure_bond_value=0.0,
                ytm=0.0,
                call_trigger_price=0.0,
                put_trigger_price=0.0,
                conversion_trigger_price=0.0,
                bid_price=[],
                ask_price=[],
                bid_volume=[],
                ask_volume=[],
                ma5=0.0,
                ma20=0.0,
                volatility_20d=0.0
            )

    def _ai_only_analysis(self, technical_data: ConvertibleTechnicalData) -> Optional[str]:
        """
        仅使用AI进行分析（不依赖实时数据）

        Args:
            technical_data: 技术面数据

        Returns:
            AI分析文本，如果分析失败则返回None
        """
        try:
            # 构建提示词
            prompt = self.prompt_builder.build_convertible_technical_prompt(technical_data)

            logger.info("调用AI进行技术分析...")
            analysis = self.agent.chat(prompt)

            if not analysis:
                logger.warning("AI分析返回空响应")
                return None

            logger.debug(f"AI分析完成，分析文本长度：{len(analysis)} 字符")
            return analysis

        except Exception as e:
            logger.error(f"AI分析时发生错误：{e}", exc_info=True)
            return None

    def _extract_signals(self, analysis: str) -> List[str]:
        """
        从分析文本中提取交易信号

        Args:
            analysis: AI分析文本

        Returns:
            信号列表
        """
        try:
            signals = []

            # 尝试提取**交易信号**后的内容
            pattern = r'\*?\*?交易信号\*?\*?[:：]\s*(.+?)(?:\n|\*\*|$)'
            match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)

            if match:
                signals_text = match.group(1).strip()
                # 按逗号分隔
                signals = [s.strip() for s in signals_text.split(',') if s.strip()]

            # 如果没有找到交易信号，尝试提取其他可能的信号标识
            if not signals:
                # 查找包含"信号"的关键词
                for line in analysis.split('\n'):
                    if '信号' in line and '：' in line:
                        signal_text = line.split('：')[-1].strip()
                        if signal_text:
                            signals = [s.strip() for s in signal_text.split(',') if s.strip()]
                            break

            # 如果仍然没有找到，返回空列表
            if not signals:
                logger.debug("未找到明确的交易信号")
                signals = []

            return signals

        except Exception as e:
            logger.warning(f"提取信号时发生错误：{e}")
            return []

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

        # 尝试提取**摘要**后的内容
        pattern = r'\*?\*?摘要\*?\*?[:：]\s*(.+?)(?:\n|$)'
        match = re.search(pattern, analysis, re.IGNORECASE)

        if match:
            summary = match.group(1).strip()
            # 限制长度
            if len(summary) > self.SUMMARY_MAX_LENGTH:
                summary = summary[:self.SUMMARY_MAX_LENGTH]
            return summary

        # 如果没有找到摘要，返回前200字
        if len(analysis) <= self.SUMMARY_MAX_LENGTH:
            return analysis

        summary = analysis[:self.SUMMARY_MAX_LENGTH]

        # 如果摘要不是完整句子，尝试在最后一个句号处截断
        last_period = summary.rfind('。')
        if last_period > self.SUMMARY_MAX_LENGTH // 2:
            summary = summary[:last_period + 1]

        return summary

    def _extract_recommendation(self, analysis: str) -> str:
        """
        提取投资建议

        Args:
            analysis: AI分析文本

        Returns:
            投资建议
        """
        try:
            # 尝试提取**建议**后的内容
            pattern = r'\*?\*?建议\*?\*?[:：]\s*(.+?)(?:\n|\*\*|$)'
            match = re.search(pattern, analysis, re.IGNORECASE)

            if match:
                recommendation = match.group(1).strip()
                # 清理可能的markdown标记
                recommendation = re.sub(r'\*+', '', recommendation)
                return recommendation

            # 如果没有找到建议，尝试查找常见建议关键词
            keywords = ['买入', '持有', '卖出', '观望', '增持', '减持', '推荐']
            for keyword in keywords:
                if keyword in analysis:
                    return keyword

            # 默认返回待定
            return "待定"

        except Exception as e:
            logger.warning(f"提取建议时发生错误：{e}")
            return "待定"

    def _format_technical_data(self, data: ConvertibleTechnicalData) -> str:
        """
        格式化技术数据用于显示

        Args:
            data: 技术面数据

        Returns:
            格式化后的数据字符串
        """
        lines = []

        # 基础行情
        if data.price > 0:
            lines.append(f"最新价格: {data.price:.2f} 元")
        if data.change_percent != 0:
            lines.append(f"涨跌幅: {data.change_percent:+.2f}%")
        if data.volume > 0:
            lines.append(f"成交量: {data.volume:,.0f}")
        if data.amount > 0:
            lines.append(f"成交额: {data.amount:,.0f} 元")

        # 技术指标
        if data.ma5 > 0:
            lines.append(f"5日均线: {data.ma5:.2f} 元")
        if data.ma20 > 0:
            lines.append(f"20日均线: {data.ma20:.2f} 元")
        if data.volatility_20d > 0:
            lines.append(f"20日波动率: {data.volatility_20d:.2f}%")

        # 转股相关
        if data.conversion_price > 0:
            lines.append(f"转股价: {data.conversion_price:.2f} 元")
        if data.conversion_value > 0:
            lines.append(f"转股价值: {data.conversion_value:.2f} 元")
        if data.premium_rate != 0:
            lines.append(f"转股溢价率: {data.premium_rate:.2f}%")

        # 债券属性
        if data.bond_rating:
            lines.append(f"债券评级: {data.bond_rating}")
        if data.pure_bond_value > 0:
            lines.append(f"纯债价值: {data.pure_bond_value:.2f} 元")
        if data.ytm != 0:
            lines.append(f"到期收益率: {data.ytm:.2f}%")

        # 条款信息
        if data.call_trigger_price > 0:
            lines.append(f"强赎触发价: {data.call_trigger_price:.2f} 元")
        if data.put_trigger_price > 0:
            lines.append(f"回售触发价: {data.put_trigger_price:.2f} 元")
        if data.conversion_trigger_price > 0:
            lines.append(f"下修触发价: {data.conversion_trigger_price:.2f} 元")

        # 市场深度
        if data.bid_price:
            lines.append(f"买一价: {data.bid_price[0]:.2f}" if len(data.bid_price) > 0 else "")
        if data.ask_price:
            lines.append(f"卖一价: {data.ask_price[0]:.2f}" if len(data.ask_price) > 0 else "")

        return "\n".join(lines) if lines else "暂无技术数据"

    def analyze_terms(
        self,
        cb_code: str,
        stock_price: float,
        stock_name: str = ""
    ) -> Optional[Dict]:
        """
        条款博弈分析

        Args:
            cb_code: 可转债代码
            stock_price: 正股当前价格
            stock_name: 正股名称

        Returns:
            包含条款分析结果的字典：
            {
                "cb_code": str,
                "cb_name": str,
                "stock_price": float,
                "stock_name": str,
                "call_trigger_price": float,
                "put_trigger_price": float,
                "conversion_price": float,
                "call_distance": float,    # 距强赎触发的距离（百分比）
                "put_distance": float,     # 距回售触发的距离（百分比）
                "conversion_distance": float,  # 距转股价的距离（百分比）
                "full_analysis": str,      # AI完整分析
            }
            如果获取失败返回 None
        """
        try:
            logger.info(f"开始条款博弈分析: {cb_code}")

            # 1. 获取转债详情
            detail = self.fetcher.get_convertible_detail(cb_code)

            if not detail:
                logger.warning(f"无法获取转债 {cb_code} 详情")
                return None

            # 2. 提取条款价格
            call_price = detail.get('call_trigger_price', 0)
            put_price = detail.get('put_trigger_price', 0)
            conversion_price = detail.get('conversion_price', 0)

            # 3. 计算距离各条款触发的距离（百分比）
            call_distance = (stock_price / call_price - 1) * 100 if call_price > 0 else 0
            put_distance = (stock_price / put_price - 1) * 100 if put_price > 0 else 0
            conversion_distance = (stock_price / conversion_price - 1) * 100 if conversion_price > 0 else 0

            # 4. 构建AI分析提示词
            prompt = self.prompt_builder.build_convertible_terms_prompt(
                cb_code=cb_code,
                cb_name=detail.get('cb_name', ''),
                stock_price=stock_price,
                stock_name=stock_name,
                call_trigger_price=call_price,
                put_trigger_price=put_price,
                conversion_price=conversion_price
            )

            # 5. AI分析
            analysis = self.agent.chat(prompt)

            if not analysis:
                logger.warning("AI条款分析失败")
                return None

            # 6. 构建返回结果
            result = {
                "cb_code": cb_code,
                "cb_name": detail.get('cb_name', ''),
                "stock_price": stock_price,
                "stock_name": stock_name,
                "call_trigger_price": call_price,
                "put_trigger_price": put_price,
                "conversion_price": conversion_price,
                "call_distance": call_distance,
                "put_distance": put_distance,
                "conversion_distance": conversion_distance,
                "full_analysis": analysis,
            }

            logger.info(f"条款博弈分析完成: {cb_code}")
            return result

        except Exception as e:
            logger.error(f"条款博弈分析失败 {cb_code}: {e}", exc_info=True)
            return None

    def screen_by_technical(
        self,
        criteria: Dict[str, Any],
        top_n: int = 20
    ) -> Optional[List[Dict]]:
        """
        批量技术面筛选

        Args:
            criteria: 筛选条件
                {
                    "price_range": (90, 110),      # 价格区间
                    "premium_max": 30,             # 最大溢价率（使用涨跌幅代替）
                    "liquidity_min": 1000000,      # 最小流动性（成交额）
                }
            top_n: 返回前N个结果

        Returns:
            筛选结果列表，按综合评分排序，每个元素包含：
            {
                "cb_code": str,
                "cb_name": str,
                "price": float,
                "premium": float,  # 溢价率（用涨跌幅代替）
                "amount": float,
                "score": float,
            }
        """
        try:
            logger.info(f"开始技术面筛选: {criteria}")

            # 1. 获取可转债列表
            cb_list = self.fetcher.get_convertible_list()

            if not cb_list:
                logger.warning("获取可转债列表为空")
                return []

            # 2. 应用筛选条件
            filtered = []

            for cb in cb_list:
                # 提取数据
                price = cb.get('price', 0)
                premium = abs(cb.get('change', 0))  # 使用涨跌幅的绝对值作为溢价率代理
                amount = cb.get('amount', 0)

                # 筛选条件检查
                if "price_range" in criteria:
                    min_p, max_p = criteria["price_range"]
                    if not (min_p <= price <= max_p):
                        continue

                if "premium_max" in criteria:
                    if premium > criteria["premium_max"]:
                        continue

                if "liquidity_min" in criteria:
                    if amount < criteria["liquidity_min"]:
                        continue

                # 计算综合评分
                score = self._calculate_screen_score(cb, criteria)

                filtered.append({
                    "cb_code": cb.get('cb_code'),
                    "cb_name": cb.get('cb_name'),
                    "price": price,
                    "premium": premium,
                    "amount": amount,
                    "score": score,
                })

            # 3. 按评分排序（降序）
            filtered.sort(key=lambda x: x['score'], reverse=True)

            # 4. 返回前N个
            result = filtered[:top_n]

            logger.info(f"技术面筛选完成，找到 {len(result)} 只转债")
            return result

        except Exception as e:
            logger.error(f"技术面筛选失败: {e}", exc_info=True)
            return None

    def _calculate_screen_score(self, cb: Dict, criteria: Dict) -> float:
        """
        计算筛选评分

        Args:
            cb: 可转债数据字典
            criteria: 筛选条件（用于判断价格是否在目标范围内）

        Returns:
            综合评分（越高越好）
        """
        score = 0.0

        # 价格在目标范围内加分
        price = cb.get('price', 100)
        if "price_range" in criteria:
            min_p, max_p = criteria["price_range"]
            if min_p <= price <= max_p:
                score += 50  # 价格符合条件，基础分50

        # 溢价率越低越好（扣分）
        premium = abs(cb.get('change', 0))
        score -= premium

        # 流动性加分
        amount = cb.get('amount', 0)
        if amount > 100000000:  # 1亿成交额
            score += 20
        elif amount > 50000000:  # 5000万
            score += 10

        return score
