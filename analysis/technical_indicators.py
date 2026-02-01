"""
技术指标计算工具模块
Technical Indicators Calculator

提供通用的技术指标计算函数，支持：
- 均线类：MA5, MA10, MA20
- 动量类：RSI, MACD, KDJ
- 波动率类：布林带, ATR
- 成交量类：OBV, 成交量比率
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""

    @staticmethod
    def calculate_sma(series: pd.Series, period: int) -> pd.Series:
        """
        计算简单移动平均线 (SMA)

        Args:
            series: 价格序列
            period: 周期

        Returns:
            SMA序列
        """
        return series.rolling(window=period).mean()

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        """
        计算指数移动平均线 (EMA)

        Args:
            series: 价格序列
            period: 周期

        Returns:
            EMA序列
        """
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        计算相对强弱指标 (RSI)

        Args:
            series: 价格序列
            period: 周期，默认14

        Returns:
            RSI序列 (0-100)
        """
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD指标

        Args:
            series: 价格序列
            fast: 快线周期，默认12
            slow: 慢线周期，默认26
            signal: 信号线周期，默认9

        Returns:
            (MACD线, 信号线, 柱状图)
        """
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        计算布林带

        Args:
            series: 价格序列
            period: 周期，默认20
            std_dev: 标准差倍数，默认2

        Returns:
            (上轨, 中轨, 下轨, 带宽)
        """
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        bandwidth = (upper_band - lower_band) / sma
        return upper_band, sma, lower_band, bandwidth

    @staticmethod
    def calculate_bollinger_position(series: pd.Series, period: int = 20, std_dev: float = 2) -> pd.Series:
        """
        计算价格在布林带中的位置 (0-1)

        Args:
            series: 价格序列
            period: 周期，默认20
            std_dev: 标准差倍数，默认2

        Returns:
            位置序列，0表示在下轨，1表示在上轨，0.5表示在中轨
        """
        upper_band, _, lower_band, _ = TechnicalIndicators.calculate_bollinger_bands(series, period, std_dev)
        position = (series - lower_band) / (upper_band - lower_band + 1e-10)
        return position

    @staticmethod
    def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算KDJ指标

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期，默认9

        Returns:
            (K值, D值, J值)
        """
        low_min = low.rolling(window=period).min()
        high_max = high.rolling(window=period).max()
        rsv = (close - low_min) / (high_max - low_min + 1e-10) * 100
        k = rsv.ewm(alpha=1/3, adjust=False).mean()
        d = k.ewm(alpha=1/3, adjust=False).mean()
        j = 3 * k - 2 * d
        return k, d, j

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        计算平均真实波幅 (ATR)

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期，默认14

        Returns:
            ATR序列
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        计算能量潮 (OBV)

        Args:
            close: 收盘价序列
            volume: 成交量序列

        Returns:
            OBV序列
        """
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    @staticmethod
    def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """
        计算顺势指标 (CCI)

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期，默认20

        Returns:
            CCI序列
        """
        tp = (high + low + close) / 3
        ma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - np.mean(x)).mean())
        cci = (tp - ma_tp) / (0.015 * mad + 1e-10)
        return cci

    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        计算威廉指标 (Williams %R)

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期，默认14

        Returns:
            Williams %R序列 (-100到0)
        """
        high_max = high.rolling(window=period).max()
        low_min = low.rolling(window=period).min()
        williams_r = -100 * (high_max - close) / (high_max - low_min + 1e-10)
        return williams_r

    @staticmethod
    def calculate_volatility(series: pd.Series, period: int = 20, annualize: bool = True) -> pd.Series:
        """
        计算波动率

        Args:
            series: 价格序列
            period: 周期，默认20
            annualize: 是否年化，默认True

        Returns:
            波动率序列（百分比）
        """
        returns = series.pct_change().dropna()
        volatility = returns.rolling(window=period).std()
        if annualize:
            volatility = volatility * np.sqrt(252) * 100
        else:
            volatility = volatility * 100
        return volatility

    @staticmethod
    def calculate_momentum(series: pd.Series, period: int = 5) -> pd.Series:
        """
        计算动量

        Args:
            series: 价格序列
            period: 周期，默认5

        Returns:
            动量序列（百分比变化）
        """
        return series.pct_change(period)

    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Dict[str, float]:
        """
        获取最新技术指标值

        Args:
            df: DataFrame，必须包含 close, high, low, volume 列

        Returns:
            技术指标字典，包含所有常用指标的最新值
        """
        if df is None or df.empty:
            return {}

        indicators = {}

        # 确保列名统一
        df = df.copy()
        df.columns = [col.lower() for col in df.columns]

        try:
            # 均线
            indicators['ma5'] = TechnicalIndicators.calculate_sma(df['close'], 5).iloc[-1]
            indicators['ma10'] = TechnicalIndicators.calculate_sma(df['close'], 10).iloc[-1]
            indicators['ma20'] = TechnicalIndicators.calculate_sma(df['close'], 20).iloc[-1]

            # RSI
            rsi = TechnicalIndicators.calculate_rsi(df['close'], 14)
            indicators['rsi_14'] = rsi.iloc[-1]

            # MACD
            macd, macd_signal, macd_hist = TechnicalIndicators.calculate_macd(df['close'])
            indicators['macd'] = macd.iloc[-1]
            indicators['macd_signal'] = macd_signal.iloc[-1]
            indicators['macd_hist'] = macd_hist.iloc[-1]

            # 布林带
            upper, middle, lower, bandwidth = TechnicalIndicators.calculate_bollinger_bands(df['close'])
            indicators['bollinger_upper'] = upper.iloc[-1]
            indicators['bollinger_middle'] = middle.iloc[-1]
            indicators['bollinger_lower'] = lower.iloc[-1]
            indicators['bollinger_bandwidth'] = bandwidth.iloc[-1]
            indicators['bollinger_position'] = TechnicalIndicators.calculate_bollinger_position(df['close']).iloc[-1]

            # KDJ
            if 'high' in df.columns and 'low' in df.columns:
                k, d, j = TechnicalIndicators.calculate_kdj(df['high'], df['low'], df['close'])
                indicators['kdj_k'] = k.iloc[-1]
                indicators['kdj_d'] = d.iloc[-1]
                indicators['kdj_j'] = j.iloc[-1]

            # ATR
            if 'high' in df.columns and 'low' in df.columns:
                indicators['atr_14'] = TechnicalIndicators.calculate_atr(df['high'], df['low'], df['close']).iloc[-1]

            # CCI
            if 'high' in df.columns and 'low' in df.columns:
                indicators['cci'] = TechnicalIndicators.calculate_cci(df['high'], df['low'], df['close']).iloc[-1]
                indicators['williams_r'] = TechnicalIndicators.calculate_williams_r(df['high'], df['low'], df['close']).iloc[-1]

            # OBV
            if 'volume' in df.columns:
                obv = TechnicalIndicators.calculate_obv(df['close'], df['volume'])
                indicators['obv'] = obv.iloc[-1]
                indicators['obv_ma'] = obv.rolling(20).mean().iloc[-1]

            # 波动率
            indicators['volatility_20d'] = TechnicalIndicators.calculate_volatility(df['close'], 20).iloc[-1]

            # 动量
            indicators['momentum_5'] = TechnicalIndicators.calculate_momentum(df['close'], 5).iloc[-1]
            indicators['momentum_10'] = TechnicalIndicators.calculate_momentum(df['close'], 10).iloc[-1]

        except Exception as e:
            logger.warning(f"计算技术指标时出错: {e}")

        return indicators
