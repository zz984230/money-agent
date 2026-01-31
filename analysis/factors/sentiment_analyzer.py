"""
市场情绪因子分析器
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """市场情绪因子分析器

    提供市场宽度、涨停统计、情绪得分等情绪指标
    """

    CACHE_TTL = 300  # 缓存5分钟

    def __init__(self, fetcher):
        """初始化情绪分析器

        Args:
            fetcher: AKShareFetcher实例
        """
        self.fetcher = fetcher
        self._market_breadth_cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None

    def get_market_breadth(self) -> Dict[str, Any]:
        """获取市场宽度统计数据

        Returns:
            {
                'up_count': 上涨家数,
                'down_count': 下跌家数,
                'flat_count': 平盘家数,
                'total': 总家数,
                'advance_decline_ratio': 涨跌比
            }
        """
        # 检查缓存
        if self._is_cache_valid():
            return self._market_breadth_cache

        try:
            data = self.fetcher.get_market_breadth_data()

            if data is None or data.empty:
                logger.warning("市场宽度数据为空，返回默认值")
                return self._get_default_market_breadth()

            up_count = len(data[data['涨跌幅'] > 0])
            down_count = len(data[data['涨跌幅'] < 0])
            flat_count = len(data[data['涨跌幅'] == 0])
            total = len(data)

            result = {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'total': total,
                'advance_decline_ratio': up_count / total if total > 0 else 0.5
            }

            # 更新缓存
            self._market_breadth_cache = result
            self._cache_time = datetime.now()

            return result

        except Exception as e:
            logger.error(f"获取市场宽度失败: {e}")
            return self._get_default_market_breadth()

    def get_limit_up_stats(self) -> Dict[str, Any]:
        """获取涨停统计数据

        Returns:
            {
                'limit_up_count': 涨停家数,
                'limit_up_ratio': 涨停比例,
                'limit_down_count': 跌停家数,
                'limit_down_ratio': 跌停比例
            }
        """
        try:
            data = self.fetcher.get_limit_up_stats_data()

            if data is None or data.empty:
                return self._get_default_limit_up_stats()

            # 假设数据包含涨停和跌停统计
            result = {
                'limit_up_count': data.get('limit_up_count', 0),
                'limit_up_ratio': data.get('limit_up_count', 0) / data.get('total', 1),
                'limit_down_count': data.get('limit_down_count', 0),
                'limit_down_ratio': data.get('limit_down_count', 0) / data.get('total', 1)
            }

            return result

        except Exception as e:
            logger.error(f"获取涨停统计失败: {e}")
            return self._get_default_limit_up_stats()

    def calculate_sentiment_score(self) -> float:
        """计算综合情绪得分 (0-100)

        考虑因素：
        - 市场宽度 (0-40分)
        - 涨停比例 (0-30分)
        - 涨停vs跌停比率 (0-30分)

        Returns:
            0-100分，>70偏多，<30偏空
        """
        try:
            breadth = self.get_market_breadth()
            limit_stats = self.get_limit_up_stats()

            # 1. 市场宽度得分 (0-40分)
            # 涨跌比 > 0.7 得40分，< 0.3 得0分
            ad_ratio = breadth['advance_decline_ratio']
            breadth_score = min(40, max(0, (ad_ratio - 0.3) / 0.4 * 40))

            # 2. 涨停比例得分 (0-30分)
            # 涨停比例 > 3% 得30分，< 1% 得0分
            limit_up_ratio = limit_stats['limit_up_ratio']
            limit_score = min(30, max(0, (limit_up_ratio - 0.01) / 0.02 * 30))

            # 3. 涨跌停比率得分 (0-30分)
            # 涨停家数 / 跌停家数
            limit_up_count = max(1, limit_stats['limit_up_count'])
            limit_down_count = max(1, limit_stats['limit_down_count'])
            balance_ratio = limit_up_count / limit_down_count
            balance_score = min(30, max(0, (balance_ratio - 0.5) / 1.5 * 30))

            total_score = breadth_score + limit_score + balance_score

            return round(total_score, 2)

        except Exception as e:
            logger.error(f"计算情绪得分失败: {e}")
            return 50.0  # 返回中性得分

    def get_historical_sentiment(self, days: int = 30) -> pd.DataFrame:
        """获取历史情绪数据（用于计算百分位）

        注意：由于市场数据是实时的，这里返回模拟的历史百分位数据

        Args:
            days: 历史天数

        Returns:
            包含历史情绪得分的DataFrame
        """
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        # 返回基于当前得分的历史分布模拟
        current_score = self.calculate_sentiment_score()

        data = []
        for i in range(days):
            # 简单的随机波动模拟
            variation = np.random.randn() * 10
            score = max(0, min(100, current_score + variation))
            data.append({'date': dates[i], 'sentiment_score': score})

        return pd.DataFrame(data).set_index('date')

    def calculate_sentiment_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算情绪因子DataFrame

        Args:
            df: 价格数据DataFrame（用于对齐索引）

        Returns:
            因子DataFrame，包含：
            - market_breadth_ratio: 市场涨跌比
            - market_sentiment_score: 市场情绪得分
        """
        factors = pd.DataFrame(index=df.index)

        try:
            breadth = self.get_market_breadth()
            sentiment_score = self.calculate_sentiment_score()

            # 广播市场级别的指标到所有行
            factors['market_breadth_ratio'] = breadth['advance_decline_ratio']
            factors['market_sentiment_score'] = sentiment_score

        except Exception as e:
            logger.error(f"计算情绪因子失败: {e}")
            factors['market_breadth_ratio'] = 0.5
            factors['market_sentiment_score'] = 50.0

        return factors

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache_time is None:
            return False

        elapsed = (datetime.now() - self._cache_time).total_seconds()
        return elapsed < self.CACHE_TTL

    def _get_default_market_breadth(self) -> Dict[str, Any]:
        """获取默认市场宽度数据"""
        return {
            'up_count': 2000,
            'down_count': 2000,
            'flat_count': 200,
            'total': 4200,
            'advance_decline_ratio': 0.5
        }

    def _get_default_limit_up_stats(self) -> Dict[str, Any]:
        """获取默认涨停统计数据"""
        return {
            'limit_up_count': 30,
            'limit_up_ratio': 0.007,
            'limit_down_count': 20,
            'limit_down_ratio': 0.005
        }
