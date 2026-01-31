"""
资金流因子分析器
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MoneyFlowAnalyzer:
    """资金流因子分析器

    提供主力净流入、大单动能等资金流指标
    """

    def __init__(self, fetcher):
        """初始化资金流分析器

        Args:
            fetcher: AKShareFetcher实例
        """
        self.fetcher = fetcher

    def get_individual_fund_flow(
        self, symbol: str, market: str = 'sz'
    ) -> Optional[pd.DataFrame]:
        """获取个股资金流数据

        Args:
            symbol: 基金代码
            market: 市场代码 ('sh', 'sz', 'bj')

        Returns:
            资金流数据DataFrame，失败返回None
        """
        try:
            data = self.fetcher.get_individual_fund_flow_data(symbol, market)
            if data is None or data.empty:
                logger.warning(f"{symbol} 资金流数据为空")
                return None
            return data
        except Exception as e:
            logger.error(f"获取{symbol}资金流数据失败: {e}")
            return None

    def calculate_capital_accumulation(
        self, flow_df: pd.DataFrame
    ) -> pd.Series:
        """计算资金累积程度

        累计主力净流入 / 当前流通市值
        这里简化为累计主力净流入的归一化值

        Args:
            flow_df: 资金流数据，必须包含'主力净流入-净额'列

        Returns:
            资金累积度序列
        """
        if '主力净流入-净额' not in flow_df.columns:
            logger.warning("资金流数据缺少'主力净流入-净额'列")
            return pd.Series([0] * len(flow_df), index=flow_df.index)

        # 累计主力净流入
        cumulative_flow = flow_df['主力净流入-净额'].cumsum()

        # 归一化到 -1 到 1 之间
        max_abs = cumulative_flow.abs().max()
        if max_abs > 0:
            normalized = cumulative_flow / max_abs
        else:
            normalized = cumulative_flow

        return normalized

    def calculate_order_momentum(
        self, flow_df: pd.DataFrame, period: int = 5
    ) -> pd.Series:
        """计算大单动能

        大单净流入占比的变化率

        Args:
            flow_df: 资金流数据，必须包含'大单净流入-净占比'列
            period: 周期，默认5日

        Returns:
            动能序列
        """
        if '大单净流入-净占比' not in flow_df.columns:
            logger.warning("资金流数据缺少'大单净流入-净占比'列")
            return pd.Series([0] * len(flow_df), index=flow_df.index)

        # 计算变化率
        momentum = flow_df['大单净流入-净占比'].diff(period)

        return momentum

    def get_northbound_flow(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """获取北向资金流向数据

        Args:
            symbol: 个股代码（可选，None表示全市场）

        Returns:
            北向资金数据DataFrame，失败返回None
        """
        try:
            data = self.fetcher.get_northbound_capital_data(symbol)
            if data is None or data.empty:
                logger.warning("北向资金数据为空")
                return None
            return data
        except Exception as e:
            logger.error(f"获取北向资金数据失败: {e}")
            return None

    def calculate_money_flow_factors(
        self, df: pd.DataFrame, symbol: str, market: str = 'sz'
    ) -> pd.DataFrame:
        """计算资金流因子DataFrame

        Args:
            df: 价格数据DataFrame（用于对齐索引）
            symbol: 基金代码
            market: 市场代码

        Returns:
            因子DataFrame，包含：
            - main_force_net_inflow_ratio: 主力净流入占比
            - large_order_momentum: 大单动能
            - capital_accumulation: 资金累积度
        """
        factors = pd.DataFrame(index=df.index)

        try:
            flow_data = self.get_individual_fund_flow(symbol, market)

            if flow_data is None:
                # 返回默认值
                factors['main_force_net_inflow_ratio'] = 0.0
                factors['large_order_momentum'] = 0.0
                factors['capital_accumulation'] = 0.0
                return factors

            # 获取最新的资金流数据并广播到所有行
            latest_ratio = flow_data['主力净流入-净占比'].iloc[-1]
            factors['main_force_net_inflow_ratio'] = latest_ratio

            # 计算大单动能
            momentum = self.calculate_order_momentum(flow_data)
            latest_momentum = momentum.iloc[-1] if not pd.isna(momentum.iloc[-1]) else 0.0
            factors['large_order_momentum'] = latest_momentum

            # 计算资金累积度
            accumulation = self.calculate_capital_accumulation(flow_data)
            latest_accumulation = accumulation.iloc[-1]
            factors['capital_accumulation'] = latest_accumulation

        except Exception as e:
            logger.error(f"计算资金流因子失败: {e}")
            factors['main_force_net_inflow_ratio'] = 0.0
            factors['large_order_momentum'] = 0.0
            factors['capital_accumulation'] = 0.0

        return factors
