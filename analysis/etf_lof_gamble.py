"""
ETF/LOF投机异常波动分析模块

包含:
- VolatilityDetector: 异常波动检测
- PredictiveFactorAnalyzer: 预测因子计算
- LOFETFGambleAnalyzer: 主分析器
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AbnormalEvent:
    """异常波动事件"""
    date: pd.Timestamp
    return_pct: float
    start_price: float
    end_price: float
    volatility: float
    window: int


class VolatilityDetector:
    """异常波动检测器"""

    def __init__(self):
        self.events = []

    def detect_sudden_moves(
        self,
        price_series: pd.Series,
        window: int = 3,
        threshold: float = 0.15
    ) -> tuple[List[pd.Timestamp], List[Dict]]:
        """
        检测突增突降

        Args:
            price_series: 价格序列，必须为pd.Series且有DatetimeIndex
            window: 观察窗口（天），默认3天
            threshold: 阈值，默认15%

        Returns:
            (abnormal_dates, abnormal_info)
            - abnormal_dates: 异常日期列表
            - abnormal_info: 异常事件详情列表
        """
        if len(price_series) < window + 1:
            return [], []

        # 计算累计收益率
        returns = price_series.pct_change(window)

        abnormal_dates = []
        abnormal_info = []

        for i in range(window, len(returns)):
            if pd.isna(returns.iloc[i]):
                continue

            if abs(returns.iloc[i]) > threshold:
                date = returns.index[i]
                start_price = price_series.iloc[i - window]
                end_price = price_series.iloc[i]
                change_pct = returns.iloc[i]

                # 计算波动率
                window_prices = price_series.iloc[i - window:i + 1]
                volatility = window_prices.std() / window_prices.mean()

                abnormal_dates.append(date)
                abnormal_info.append({
                    'date': date,
                    'return_pct': change_pct,
                    'start_price': start_price,
                    'end_price': end_price,
                    'volatility': volatility,
                    'window': window
                })

        logger.info(f"检测到{len(abnormal_dates)}个异常波动事件（窗口={window}天，阈值={threshold*100}%）")
        return abnormal_dates, abnormal_info

    def multi_timeframe_analysis(self, price_series: pd.Series) -> Dict:
        """
        多时间框架分析

        Args:
            price_series: 价格序列

        Returns:
            包含不同时间窗口和综合指标的结果字典
        """
        results = {}

        # 不同时间窗口检测
        for window in [2, 3, 5]:
            dates, info = self.detect_sudden_moves(
                price_series,
                window=window,
                threshold=0.1 if window == 2 else 0.15
            )
            results[f'window_{window}'] = {
                'dates': dates,
                'info': info,
                'count': len(dates)
            }

        # 计算综合波动指标
        returns = price_series.pct_change()
        results['metrics'] = {
            'max_1d_return': returns.max(),
            'min_1d_return': returns.min(),
            'volatility_20d': returns.rolling(20).std().mean() if len(returns) >= 20 else None,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        }

        return results
