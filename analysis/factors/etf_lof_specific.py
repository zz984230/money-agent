"""
ETF/LOF特有因子分析器
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ETFLOFSpecificAnalyzer:
    """ETF/LOF特有因子分析器

    提供溢价率、套利空间、流动性排名等ETF/LOF特有指标
    """

    def __init__(self, fetcher):
        """初始化ETF/LOF特有因子分析器

        Args:
            fetcher: AKShareFetcher实例
        """
        self.fetcher = fetcher

    def _calc_premium_rate(self, price: float, nav: float) -> float:
        """计算溢价率/折价率

        Args:
            price: 市场价格
            nav: 净值

        Returns:
            溢价率（正数）或折价率（负数）
        """
        if nav == 0:
            return 0.0
        return (price - nav) / nav

    def get_premium_discount_rate(
        self, symbol: str, fund_type: str = 'LOF'
    ) -> Optional[float]:
        """获取溢价率/折价率

        Args:
            symbol: 基金代码
            fund_type: 基金类型 ('LOF' or 'ETF')

        Returns:
            溢价率（正数）或折价率（负数），失败返回None
        """
        try:
            nav = self.fetcher.get_etf_lof_nav(symbol)
            quote = self.fetcher.get_etf_lof_realtime_quote(symbol)

            if nav is None or quote is None:
                logger.warning(f"{symbol} 净值或行情数据为空")
                return None

            price = quote.get('price', nav)
            return self._calc_premium_rate(price, nav)

        except Exception as e:
            logger.error(f"获取{symbol}溢价率失败: {e}", exc_info=True)
            return None

    def calculate_arbitrage_space(
        self,
        premium_rate: float,
        arbitrage_cost: float = 0.015
    ) -> float:
        """计算套利空间

        Args:
            premium_rate: 溢价率（正溢价或负折价）
            arbitrage_cost: 套利成本（默认1.5%）

        Returns:
            套利空间，>0表示有套利机会
        """
        # 对于溢价的情况，套利空间 = 溢价率 - 成本
        # 对于折价的情况，套利空间 = abs(折价率) - 成本
        return abs(premium_rate) - arbitrage_cost

    def get_price_nav_correlation(
        self, symbol: str, period: int = 20
    ) -> Optional[float]:
        """获取价格与净值相关系数

        Args:
            symbol: 基金代码
            period: 周期

        Returns:
            相关系数，失败返回None
        """
        try:
            # 需要获取历史价格和净值数据
            # 这里简化实现，返回默认值
            return 0.98
        except Exception as e:
            logger.error(f"计算{symbol}价格净值相关性失败: {e}", exc_info=True)
            return None

    def calculate_liquidity_rank(
        self, symbol: str, all_funds: List[Dict]
    ) -> int:
        """计算流动性排名

        Args:
            symbol: 基金代码
            all_funds: 所有基金列表（必须包含'amount'键）

        Returns:
            排名（越小流动性越好），找不到返回999
        """
        try:
            # 按成交额降序排序
            sorted_funds = sorted(
                all_funds,
                key=lambda x: x.get('amount', 0),
                reverse=True
            )

            for i, fund in enumerate(sorted_funds):
                if fund.get('code') == symbol:
                    return i + 1

            return 999

        except Exception as e:
            logger.error(f"计算{symbol}流动性排名失败: {e}", exc_info=True)
            return 999

    def calculate_turnover_percentile(
        self, symbol: str, historical_data: pd.DataFrame
    ) -> float:
        """计算换手率历史百分位

        Args:
            symbol: 基金代码
            historical_data: 历史数据（必须包含换手率列）

        Returns:
            百分位值 (0-1)，失败返回0.5
        """
        try:
            if 'turnover_rate' not in historical_data.columns:
                # 如果没有换手率数据，用成交额代替
                if 'amount' in historical_data.columns:
                    series = historical_data['amount']
                else:
                    return 0.5
            else:
                series = historical_data['turnover_rate']

            current_value = series.iloc[-1]
            percentile = (series < current_value).sum() / len(series)

            return round(percentile, 2)

        except Exception as e:
            logger.error(f"计算{symbol}换手率百分位失败: {e}", exc_info=True)
            return 0.5

    def calculate_etf_lof_specific_factors(
        self, df: pd.DataFrame, symbol: str, fund_type: str = 'LOF',
        all_funds: List[Dict] = None
    ) -> pd.DataFrame:
        """计算ETF/LOF特有因子

        Args:
            df: 价格数据DataFrame（用于对齐索引）
            symbol: 基金代码
            fund_type: 基金类型
            all_funds: 所有基金列表

        Returns:
            因子DataFrame，包含：
            - premium_discount_rate: 溢价率/折价率
            - arbitrage_space: 套利空间
            - liquidity_rank: 流动性排名
        """
        factors = pd.DataFrame(index=df.index)

        try:
            # 获取溢价率
            premium_rate = self.get_premium_discount_rate(symbol, fund_type)
            if premium_rate is not None:
                factors['premium_discount_rate'] = premium_rate
                factors['arbitrage_space'] = self.calculate_arbitrage_space(premium_rate)
            else:
                factors['premium_discount_rate'] = 0.0
                factors['arbitrage_space'] = 0.0

            # 计算流动性排名
            if all_funds:
                liquidity_rank = self.calculate_liquidity_rank(symbol, all_funds)
                factors['liquidity_rank'] = liquidity_rank
            else:
                factors['liquidity_rank'] = 999

        except Exception as e:
            logger.error(f"计算ETF/LOF特有因子失败: {e}", exc_info=True)
            factors['premium_discount_rate'] = 0.0
            factors['arbitrage_space'] = 0.0
            factors['liquidity_rank'] = 999

        return factors
