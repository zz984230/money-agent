"""
ETF/LOF投机异常波动分析模块

包含:
- VolatilityDetector: 异常波动检测
- PredictiveFactorAnalyzer: 预测因子计算
- LOFETFGambleAnalyzer: 主分析器
"""

import logging
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field

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

    def detect_sudden_moves_multi_window(
        self,
        price_series: pd.Series,
        windows: List[int] = None,
        threshold: float = 0.15
    ) -> tuple[List[pd.Timestamp], List[Dict]]:
        """
        多时间窗口检测突增突降（任意窗口满足即触发）

        Args:
            price_series: 价格序列，必须为pd.Series且有DatetimeIndex
            windows: 观察窗口列表（天），默认[2, 3, 5]
            threshold: 阈值，默认15%

        Returns:
            (abnormal_dates, abnormal_info)
            - abnormal_dates: 异常日期列表（去重）
            - abnormal_info: 异常事件详情列表
        """
        if windows is None:
            windows = [2, 3, 5]

        all_abnormal_dates = set()
        all_abnormal_info = []

        for window in windows:
            abnormal_dates, abnormal_info = self.detect_sudden_moves(
                price_series, window=window, threshold=threshold
            )

            # 合并结果
            for date in abnormal_dates:
                if date not in all_abnormal_dates:
                    all_abnormal_dates.add(date)
                    # 找到对应的事件详情
                    for info in abnormal_info:
                        if info['date'] == date:
                            all_abnormal_info.append(info)
                            break

        # 按日期排序
        all_abnormal_info.sort(key=lambda x: x['date'])
        all_abnormal_dates = sorted(list(all_abnormal_dates))

        logger.info(f"多窗口检测完成，共发现{len(all_abnormal_dates)}个异常波动事件（窗口={windows}，阈值={threshold*100}%）")
        return all_abnormal_dates, all_abnormal_info

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

    def build_prediction_model(
        self,
        factors: pd.DataFrame,
        target_events: List[pd.Timestamp],
        lookback_days: int = 1
    ) -> tuple:
        """
        构建预测模型

        Args:
            factors: 因子DataFrame
            target_events: 突增突降事件日期列表
            lookback_days: 事件前观察天数

        Returns:
            (model, feature_importance) 或 (None, None)
        """
        if len(factors) == 0 or len(target_events) == 0:
            return None, None

        # 创建标签
        labels = pd.Series(0, index=factors.index)
        for event_date in target_events:
            if event_date in factors.index:
                # 找到事件前N天的索引
                event_idx = factors.index.get_loc(event_date)
                if event_idx >= lookback_days:
                    pred_idx = event_idx - lookback_days
                    labels.iloc[pred_idx] = 1

        # 对齐数据，删除NaN
        aligned_data = pd.concat([factors, labels], axis=1)
        aligned_data.columns = list(factors.columns) + ['label']
        aligned_data = aligned_data.dropna()

        if len(aligned_data) == 0 or aligned_data['label'].sum() == 0:
            logger.warning("没有足够的正样本构建模型")
            return None, None

        # 特征和标签
        X = aligned_data.iloc[:, :-1]
        y = aligned_data['label']

        # 检查正负样本比例
        pos_count = y.sum()
        neg_count = len(y) - pos_count
        logger.info(f"正样本: {pos_count}, 负样本: {neg_count}")

        try:
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestClassifier

            # 划分训练测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )

            # 训练模型
            clf = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            clf.fit(X_train, y_train)

            # 计算特征重要性
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': clf.feature_importances_
            }).sort_values('importance', ascending=False)

            # 记录模型性能
            train_score = clf.score(X_train, y_train)
            test_score = clf.score(X_test, y_test)
            logger.info(f"模型训练准确率: {train_score:.3f}, 测试准确率: {test_score:.3f}")

            return clf, feature_importance

        except Exception as e:
            logger.error(f"构建预测模型失败: {e}")
            return None, None


@dataclass
class GambleAnalysisResult:
    """ETF/LOF投机分析结果"""
    symbol: str
    name: str
    fund_type: str

    # 异常波动数据
    abnormal_events_count: int
    abnormal_events: List[Dict] = field(default_factory=list)

    # 因子数据
    current_factors: Dict = field(default_factory=dict)
    feature_importance: Optional[pd.DataFrame] = None

    # AI分析
    ai_summary: str = ""
    timing_advice: str = ""
    action_advice: str = ""

    # 具体操作
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[List[float]] = None
    position_size: Optional[str] = None
    hold_period: Optional[str] = None


class LOFETFGambleAnalyzer:
    """ETF/LOF投机主分析器"""

    def __init__(self, agent):
        """
        初始化分析器

        Args:
            agent: AI Agent实例
        """
        self.agent = agent
        from data.fetchers.akshare_fetcher import AKShareFetcher
        self.fetcher = AKShareFetcher()
        self.detector = VolatilityDetector()
        self.factor_analyzer = PredictiveFactorAnalyzer()

    def analyze_single(self, symbol: str, name: str, fund_type: str = "LOF") -> Optional[GambleAnalysisResult]:
        """
        分析单个LOF/ETF

        Args:
            symbol: 基金代码
            name: 基金名称
            fund_type: 基金类型

        Returns:
            GambleAnalysisResult 或 None
        """
        logger.info(f"开始分析 {name} ({symbol})")

        # 1. 获取历史数据
        df = self.fetcher.get_lof_etf_history(symbol, period=100)
        if df is None or len(df) < 50:
            logger.warning(f"{symbol} 数据不足，跳过")
            return None

        # 2. 检测异常波动
        abnormal_dates, abnormal_info = self.detector.detect_sudden_moves(
            df['close'], window=3, threshold=0.15
        )

        if len(abnormal_info) == 0:
            logger.info(f"{symbol} 未发现异常波动事件")
            return None

        logger.info(f"{symbol} 发现 {len(abnormal_info)} 个异常波动事件")

        # 3. 计算所有因子
        all_factors = self.factor_analyzer.calculate_all_factors(df)

        # 4. 构建预测模型
        model, feature_importance = self.factor_analyzer.build_prediction_model(
            all_factors, abnormal_dates
        )

        if feature_importance is None:
            logger.warning(f"{symbol} 无法构建预测模型")
            feature_importance = pd.DataFrame(columns=['feature', 'importance'])

        # 5. 准备当前数据
        current_factors = all_factors.iloc[-1].dropna().to_dict()

        current_data = {
            'price': df['close'].iloc[-1],
            'change_pct': df['close'].pct_change().iloc[-1] * 100 if len(df) > 1 else 0,
            'volume': df['volume'].iloc[-1] if 'volume' in df.columns else 0,
            'volatility_20d': df['close'].pct_change().rolling(20).std().iloc[-1] if len(df) >= 20 else None
        }

        # 6. AI分析
        try:
            from core.agent.prompts import PromptBuilder

            prompt = PromptBuilder.build_etf_lof_gamble_prompt(
                symbol, name, fund_type, abnormal_info,
                current_factors, feature_importance, current_data
            )

            ai_response = self.agent.chat(prompt)

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            ai_response = f"AI分析失败: {str(e)}"

        # 7. 构建结果
        result = GambleAnalysisResult(
            symbol=symbol,
            name=name,
            fund_type=fund_type,
            abnormal_events_count=len(abnormal_info),
            abnormal_events=abnormal_info,
            current_factors=current_factors,
            feature_importance=feature_importance,
            ai_summary=ai_response
        )

        return result

    def screen_and_analyze(
        self,
        criteria: Optional[Dict] = None,
        top_n: int = 20
    ) -> List[GambleAnalysisResult]:
        """
        筛选并对多个标的进行AI分析

        Args:
            criteria: 筛选条件，可包含:
                - window: 单个时间窗口（默认3），与windows二选一
                - windows: 多时间窗口列表（默认[2,3,5]），优先级高于window
                - threshold: 波动阈值（默认0.15）
                - fund_types: 基金类型列表 ['LOF', 'ETF'] 或 ['commodity', 'overseas']
            top_n: 返回数量

        Returns:
            分析结果列表
        """
        if criteria is None:
            criteria = {}

        # 支持多窗口检测
        windows = criteria.get('windows', None)
        if windows is None:
            window = criteria.get('window', 3)
            windows = [window]

        threshold = criteria.get('threshold', 0.15)
        fund_types = criteria.get('fund_types', ['commodity', 'overseas'])

        use_multi_window = len(windows) > 1
        window_desc = f"{windows}天(多窗口)" if use_multi_window else f"{windows[0]}天"
        logger.info(f"开始筛选分析，窗口={window_desc}，阈值={threshold*100}%")

        # 1. 获取目标列表
        target_list = []
        if 'commodity' in fund_types:
            commodity_lof = self.fetcher.get_commodity_lof_list()
            target_list.extend(commodity_lof)

        if 'overseas' in fund_types:
            overseas_etf = self.fetcher.get_overseas_etf_list()
            target_list.extend(overseas_etf)

        logger.info(f"获取到 {len(target_list)} 个目标标的")

        # 2. 快速筛选：检测异常波动
        screened = []
        for item in target_list[:top_n * 3]:  # 多取一些用于筛选
            symbol = item['code']
            name = item['name']
            fund_type = item['type']

            try:
                # 使用100天历史数据
                df = self.fetcher.get_lof_etf_history(symbol, period=100)
                if df is None or len(df) < 50:
                    continue

                # 使用多窗口检测
                if use_multi_window:
                    abnormal_dates, _ = self.detector.detect_sudden_moves_multi_window(
                        df['close'], windows=windows, threshold=threshold
                    )
                else:
                    abnormal_dates, _ = self.detector.detect_sudden_moves(
                        df['close'], window=windows[0], threshold=threshold
                    )

                if len(abnormal_dates) > 0:
                    screened.append({
                        'symbol': symbol,
                        'name': name,
                        'fund_type': fund_type,
                        'events_count': len(abnormal_dates),
                        'recent_change': df['close'].pct_change(windows[0]).iloc[-1]
                    })

            except Exception as e:
                logger.error(f"筛选 {symbol} 失败: {e}")
                continue

        # 3. 按异常事件数量排序，取前top_n个
        screened.sort(key=lambda x: x['events_count'], reverse=True)
        top_targets = screened[:top_n]

        logger.info(f"筛选出 {len(top_targets)} 个目标进行深度分析")

        # 4. 深度分析
        results = []
        for target in top_targets:
            try:
                result = self.analyze_single(
                    target['symbol'],
                    target['name'],
                    target['fund_type']
                )
                if result is not None:
                    results.append(result)

            except Exception as e:
                logger.error(f"分析 {target['symbol']} 失败: {e}")
                continue

        logger.info(f"完成 {len(results)} 个标的的分析")
        return results

    def get_top_factors_across_funds(self, results: List[GambleAnalysisResult]) -> pd.DataFrame:
        """
        获取所有标的中的重要因子

        Args:
            results: 分析结果列表

        Returns:
            因子重要性排序DataFrame
        """
        all_importances = []
        for result in results:
            if result.feature_importance is not None and len(result.feature_importance) > 0:
                importance_df = result.feature_importance.copy()
                importance_df['fund'] = result.symbol
                importance_df['fund_name'] = result.name
                all_importances.append(importance_df)

        if not all_importances:
            return pd.DataFrame(columns=['feature', 'mean_importance', 'occurrence_count'])

        combined = pd.concat(all_importances, ignore_index=True)

        # 计算因子在所有基金中的平均重要性
        factor_ranking = combined.groupby('feature')['importance'].agg(['mean', 'count']).reset_index()
        factor_ranking = factor_ranking.sort_values('mean', ascending=False)
        factor_ranking.columns = ['feature', 'mean_importance', 'occurrence_count']

        return factor_ranking
