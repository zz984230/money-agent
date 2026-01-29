"""
可转债中期量化因子计算器
Convertible Bond Medium-Term Quantitative Factor Calculator
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndustryFactorResult:
    """行业因子计算结果"""
    industry_code: str
    industry_name: str
    momentum_60d: float  # 60日动量
    momentum_120d: float  # 120日动量
    relative_strength: float  # 相对沪深300强弱
    volume_ratio: float  # 成交额占比


@dataclass
class BondFactorResult:
    """个券因子计算结果"""
    cb_code: str
    cb_name: str
    stock_excess_return: float  # 正股超额收益
    premium_rate: float  # 转股溢价率
    bond_type: str  # 转债类型：偏股型/平衡型/偏债型
    liquidity_score: float  # 流动性评分
    drawdown_from_high: float  # 距高点回撤
    stop_loss_signal: bool  # 止损信号
    stop_profit_signal: bool  # 止盈信号


class MediumTermFactorCalculator:
    """中期量化因子计算器"""

    def calculate_industry_momentum(
        self,
        price_df: pd.DataFrame,
        days: int = 60
    ) -> Optional[float]:
        """
        计算行业指数动量（N日涨跌幅）

        Args:
            price_df: 包含日期和收盘价的DataFrame
            days: 计算周期

        Returns:
            涨跌幅百分比，如 20.5 表示上涨20.5%
        """
        try:
            if price_df is None or price_df.empty or len(price_df) < 2:
                logger.warning("价格数据不足，无法计算动量")
                return 0.0

            # 确保按日期排序
            df = price_df.sort_values('date').tail(days)

            if len(df) < 2:
                return 0.0

            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]

            momentum = (end_price / start_price - 1) * 100

            logger.debug(f"行业{days}日动量: {momentum:.2f}%")
            return momentum

        except Exception as e:
            logger.error(f"计算行业动量失败: {e}", exc_info=True)
            return 0.0

    def calculate_industry_relative_strength(
        self,
        industry_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        days: int = 60
    ) -> Optional[float]:
        """
        计算行业相对强弱（相对沪深300）

        公式: (行业涨幅 / 基准涨幅 - 1) * 100%

        Args:
            industry_df: 行业指数数据
            benchmark_df: 基准指数数据
            days: 计算周期

        Returns:
            相对强弱百分比
        """
        try:
            industry_momentum = self.calculate_industry_momentum(industry_df, days)
            benchmark_momentum = self.calculate_industry_momentum(benchmark_df, days)

            if benchmark_momentum == 0:
                logger.warning("基准指数动量为0，无法计算相对强弱")
                return 0.0

            relative_strength = (industry_momentum / benchmark_momentum - 1) * 100

            logger.debug(f"行业相对强弱: {relative_strength:.2f}%")
            return relative_strength

        except Exception as e:
            logger.error(f"计算相对强弱失败: {e}", exc_info=True)
            return 0.0

    def calculate_stock_excess_return(
        self,
        stock_df: pd.DataFrame,
        industry_df: pd.DataFrame,
        days: int = 60
    ) -> Optional[float]:
        """
        计算正股超额收益（正股涨幅 - 行业涨幅）

        Args:
            stock_df: 正股价格数据
            industry_df: 行业指数数据
            days: 计算周期

        Returns:
            超额收益百分比
        """
        try:
            stock_momentum = self.calculate_industry_momentum(stock_df, days)
            industry_momentum = self.calculate_industry_momentum(industry_df, days)

            excess_return = stock_momentum - industry_momentum

            logger.debug(f"正股超额收益: {excess_return:.2f}%")
            return excess_return

        except Exception as e:
            logger.error(f"计算正股超额收益失败: {e}", exc_info=True)
            return 0.0

    def determine_bond_type(
        self,
        conversion_value: float,
        pure_bond_value: float
    ) -> str:
        """
        判断转债类型

        Args:
            conversion_value: 转股价值
            pure_bond_value: 纯债价值

        Returns:
            "偏股型" / "平衡型" / "偏债型"
        """
        if pure_bond_value == 0:
            return "平衡型"

        ratio = conversion_value / pure_bond_value

        if ratio > 2:
            return "偏股型"
        elif ratio > 1:
            return "平衡型"
        else:
            return "偏债型"

    def calculate_drawdown_from_high(
        self,
        price_df: pd.DataFrame,
        current_price: float,
        days: int = 20
    ) -> float:
        """
        计算距N日高点的回撤

        Args:
            price_df: 历史价格数据
            current_price: 当前价格
            days: 回溯周期

        Returns:
            回撤百分比（负数表示回撤）
        """
        try:
            if price_df is None or price_df.empty:
                return 0.0

            high_df = price_df.tail(days)
            if high_df.empty:
                return 0.0

            highest_price = high_df['close'].max()

            if highest_price == 0:
                return 0.0

            drawdown = (current_price / highest_price - 1) * 100

            logger.debug(f"距{days}日高点回撤: {drawdown:.2f}%")
            return drawdown

        except Exception as e:
            logger.error(f"计算回撤失败: {e}", exc_info=True)
            return 0.0

    def check_stop_loss_signal(
        self,
        drawdown: float,
        threshold: float = -15.0
    ) -> bool:
        """
        检查止损信号

        Args:
            drawdown: 回撤百分比
            threshold: 止损阈值

        Returns:
            是否触发止损
        """
        return drawdown <= threshold

    def check_stop_profit_signal(
        self,
        premium_rate: float,
        premium_history: pd.Series,
        percentile: float = 0.8
    ) -> bool:
        """
        检查止盈信号（溢价率扩张）

        Args:
            premium_rate: 当前溢价率
            premium_history: 历史溢价率序列
            percentile: 分位数阈值

        Returns:
            是否触发止盈
        """
        try:
            if premium_history is None or len(premium_history) < 10:
                return False

            threshold = premium_history.quantile(percentile)
            return premium_rate >= threshold

        except Exception as e:
            logger.error(f"检查止盈信号失败: {e}", exc_info=True)
            return False
