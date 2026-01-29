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


class PredictiveFactorAnalyzer:
    """预测因子分析器"""

    def __init__(self):
        self.factors = {}

    def calculate_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术因子

        Args:
            df: DataFrame，必须包含 close, high, low, volume 列

        Returns:
            因子DataFrame，索引与df相同
        """
        factors = pd.DataFrame(index=df.index)

        # 价格动量因子
        factors['momentum_5'] = df['close'].pct_change(5)
        factors['momentum_10'] = df['close'].pct_change(10)
        factors['momentum_20'] = df['close'].pct_change(20)

        # 波动率因子
        factors['volatility_20'] = df['close'].pct_change().rolling(20).std()

        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        factors['atr_14'] = true_range.rolling(14).mean()

        # 成交量因子
        if 'volume' in df.columns:
            factors['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            factors['volume_ma_5'] = df['volume'].rolling(5).mean() / df['volume'].rolling(20).mean()

        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        factors['rsi_14'] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        factors['macd'] = ema_12 - ema_26

        # 布林带带宽
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        upper_band = sma_20 + 2 * std_20
        lower_band = sma_20 - 2 * std_20
        factors['bollinger_bandwidth'] = (upper_band - lower_band) / sma_20

        # 价量背离
        price_change = df['close'].pct_change(5)
        if 'volume' in df.columns:
            volume_change = df['volume'].pct_change(5)
            factors['pv_divergence'] = price_change - volume_change
        else:
            factors['pv_divergence'] = price_change

        return factors

    def calculate_liquidity_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算流动性因子

        Args:
            df: DataFrame，必须包含 close, high, low, volume 列

        Returns:
            因子DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        # 价差指标
        factors['spread_pct'] = (df['high'] - df['low']) / df['close']

        # 流动性冲击
        daily_return = df['close'].pct_change()
        if 'volume' in df.columns:
            factors['liquidity_impact'] = daily_return.abs() / (df['volume'] + 1e-6)
        else:
            factors['liquidity_impact'] = daily_return.abs()

        return factors

    def calculate_commodity_specific_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算大宗商品特有因子

        Args:
            df: DataFrame，必须包含 close 列

        Returns:
            因子DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        # 价格趋势
        def trend_func(x):
            if len(x) < 2:
                return 0
            return 1 if x.iloc[-1] > x.iloc[0] else -1

        factors['price_trend'] = df['close'].rolling(20).apply(trend_func)

        # 波动聚集性
        returns = df['close'].pct_change()
        volatility_5 = returns.rolling(5).std()
        volatility_20 = returns.rolling(20).std()
        factors['vol_clustering'] = volatility_5 / (volatility_20 + 1e-6)

        return factors

    def calculate_all_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有因子

        Args:
            df: 历史数据DataFrame

        Returns:
            合并后的因子DataFrame
        """
        tech_factors = self.calculate_technical_factors(df)
        liq_factors = self.calculate_liquidity_factors(df)
        commodity_factors = self.calculate_commodity_specific_factors(df)

        # 合并所有因子
        all_factors = pd.concat([tech_factors, liq_factors, commodity_factors], axis=1)

        return all_factors
