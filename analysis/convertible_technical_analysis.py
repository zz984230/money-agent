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
        cb_code: str,
        cb_name: str
    ) -> Optional[TechnicalAnalysisResult]:
        """
        分析可转债技术面

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称

        Returns:
            TechnicalAnalysisResult对象，如果分析失败则返回None
        """
        try:
            # 验证参数
            if not cb_code or not cb_code.strip():
                logger.warning("可转债代码不能为空")
                return None

            if not cb_name or not cb_name.strip():
                logger.warning("可转债名称不能为空")
                return None

            cb_code = cb_code.strip()
            cb_name = cb_name.strip()

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
            # 获取历史数据用于计算技术指标
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
            latest_price = 0.0
            change_percent = 0.0
            volume = 0.0
            amount = 0.0

            if history_df is not None and not history_df.empty and 'close' in history_df.columns:
                closes = history_df['close'].values
                latest_price = float(closes[-1]) if len(closes) > 0 else 0.0

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

                # 获取成交量和成交额
                if 'volume' in history_df.columns:
                    volume = float(history_df['volume'].iloc[-1]) if len(history_df) > 0 else 0.0
                if 'amount' in history_df.columns:
                    amount = float(history_df['amount'].iloc[-1]) if len(history_df) > 0 else 0.0

                # 计算涨跌幅
                if len(closes) >= 2:
                    change_percent = (closes[-1] - closes[-2]) / closes[-2] * 100

            # 构建技术数据对象
            # 注意：部分字段使用默认值，因为fetcher暂不提供
            technical_data = ConvertibleTechnicalData(
                cb_code=cb_code,
                cb_name=cb_name,
                price=latest_price,
                change_percent=change_percent,
                volume=volume,
                amount=amount,
                conversion_price=0.0,      # 需要从detail接口获取
                conversion_value=0.0,      # 需要从realtime接口获取
                premium_rate=0.0,          # 需要从realtime接口获取
                bond_rating="",            # 需要从detail接口获取
                pure_bond_value=0.0,       # 需要计算
                ytm=0.0,                   # 需要计算
                call_trigger_price=0.0,    # 需要从detail接口获取
                put_trigger_price=0.0,     # 需要从detail接口获取
                conversion_trigger_price=0.0,  # 需要从detail接口获取
                bid_price=[],              # 需要从realtime接口获取
                ask_price=[],              # 需要从realtime接口获取
                bid_volume=[],             # 需要从realtime接口获取
                ask_volume=[],             # 需要从realtime接口获取
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
            # 构建数据摘要
            data_summary = self._format_technical_data(technical_data)

            # 构建提示词
            # 注意：build_convertible_technical_prompt方法将在Task 10中实现
            # 这里使用placeholder或直接构建简单提示词
            prompt = f"""请分析以下可转债的技术面：

可转债代码：{technical_data.cb_code}
可转债名称：{technical_data.cb_name}

{data_summary}

请从以下方面进行分析：
1. 价格走势和技术指标分析
2. 成交量和资金流向
3. 技术形态和支撑/阻力位
4. 交易信号和操作建议

请按以下格式输出：
## 技术面分析
[详细分析内容]

**交易信号**：信号1, 信号2, 信号3

**建议**：[买入/持有/卖出/观望]

**摘要**：[简短总结]
"""

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
            # 注意：build_convertible_terms_prompt 将在任务 10 中实现
            # 这里先使用简单的提示词
            prompt = f"""请分析以下可转债的条款博弈情况：

【转债信息】
{detail.get('cb_name', '')} ({cb_code})

【正股信息】
{stock_name}
当前股价：{stock_price}元

【条款触发分析】
强赎条款：
  - 触发价：{call_price}元
  - 当前距离：{call_distance:.2f}%
  - 状态：{'已触发' if stock_price >= call_price else '未触发'}

回售条款：
  - 触发价：{put_price}元
  - 当前距离：{put_distance:.2f}%
  - 状态：{'已触发' if stock_price <= put_price else '未触发'}

下修条款：
  - 转股价：{conversion_price}元
  - 当前距离转股价：{conversion_distance:.2f}%

请分析：
1. 各条款的触发可能性和时间窗口
2. 发行人可能的应对策略（强赎、下修、不行使权利）
3. 投资者的应对策略和风险收益分析
4. 给出具体的操作建议"""

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
