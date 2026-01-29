"""
ETF/LOF投机异常波动分析模块测试
"""
import pytest
import pandas as pd
import numpy as np
from analysis.etf_lof_gamble import (
    VolatilityDetector,
    AbnormalEvent,
    PredictiveFactorAnalyzer,
    LOFETFGambleAnalyzer,
    GambleAnalysisResult
)


def test_detect_sudden_moves_no_abnormal():
    """测试无异常波动的情况"""
    detector = VolatilityDetector()

    # 创建稳定的价格序列（1%的日常波动）
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = pd.Series([100 + i * 0.01 + np.random.randn() * 0.5 for i in range(100)], index=dates)

    abnormal_dates, abnormal_info = detector.detect_sudden_moves(prices, window=3, threshold=0.15)

    assert len(abnormal_dates) == 0
    assert len(abnormal_info) == 0


def test_detect_sudden_moves_with_abnormal():
    """测试有异常波动的情况"""
    detector = VolatilityDetector()

    # 创建价格序列：在第10-12天有20%的涨幅
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    prices = []
    for i in range(50):
        if i < 10:
            prices.append(100.0)
        elif i < 13:
            # 3天内从100涨到120
            prices.append(100.0 + (i - 9) * 10.0)
        else:
            prices.append(120.0)

    price_series = pd.Series(prices, index=dates)

    abnormal_dates, abnormal_info = detector.detect_sudden_moves(price_series, window=3, threshold=0.15)

    # 应该检测到异常
    assert len(abnormal_dates) > 0
    assert len(abnormal_info) > 0

    # 检查异常事件的数据结构
    event = abnormal_info[0]
    assert 'date' in event
    assert 'return_pct' in event
    assert 'volatility' in event
    assert abs(event['return_pct']) > 0.15


def test_multi_timeframe_analysis():
    """测试多时间框架分析"""
    detector = VolatilityDetector()

    # 创建有波动的价格序列
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = pd.Series([100 + np.sin(i / 10) * 10 for i in range(100)], index=dates)

    results = detector.multi_timeframe_analysis(prices)

    # 检查结果结构
    assert 'window_2' in results
    assert 'window_3' in results
    assert 'window_5' in results
    assert 'metrics' in results

    # 检查metrics
    assert 'max_1d_return' in results['metrics']
    assert 'min_1d_return' in results['metrics']
    assert 'sharpe_ratio' in results['metrics']


def test_volatility_detector_initialization():
    """测试VolatilityDetector初始化"""
    detector = VolatilityDetector()
    assert detector.events == []
    assert hasattr(detector, 'detect_sudden_moves')
    assert hasattr(detector, 'multi_timeframe_analysis')


def test_abnormal_event_dataclass():
    """测试AbnormalEvent数据类"""
    date = pd.Timestamp('2024-01-15')
    event = AbnormalEvent(
        date=date,
        return_pct=0.18,
        start_price=100.0,
        end_price=118.0,
        volatility=0.12,
        window=3
    )

    assert event.date == date
    assert event.return_pct == 0.18
    assert event.start_price == 100.0
    assert event.end_price == 118.0
    assert event.volatility == 0.12
    assert event.window == 3


def test_calculate_technical_factors():
    """测试技术因子计算"""
    analyzer = PredictiveFactorAnalyzer()

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    df = pd.DataFrame({
        'close': [100 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'high': [102 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'low': [98 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'volume': [1000000 + np.random.randn() * 100000 for i in range(100)]
    }, index=dates)

    factors = analyzer.calculate_technical_factors(df)

    # 检查因子是否存在
    expected_factors = [
        'momentum_5', 'momentum_10', 'momentum_20',
        'volatility_20', 'atr_14', 'volume_ratio',
        'volume_ma_5', 'rsi_14', 'macd', 'bollinger_bandwidth',
        'pv_divergence'
    ]

    for factor in expected_factors:
        assert factor in factors.columns

    # 检查索引一致
    assert len(factors) == len(df)

    # 检查RSI范围（0-100）
    rsi_values = factors['rsi_14'].dropna()
    if len(rsi_values) > 0:
        assert rsi_values.max() <= 100
        assert rsi_values.min() >= 0


def test_calculate_all_factors():
    """测试所有因子计算"""
    analyzer = PredictiveFactorAnalyzer()

    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    df = pd.DataFrame({
        'close': [100 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'high': [102 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'low': [98 + i * 0.1 + np.random.randn() * 2 for i in range(100)],
        'volume': [1000000 + np.random.randn() * 100000 for i in range(100)]
    }, index=dates)

    factors = analyzer.calculate_all_factors(df)

    # 检查是否有因子
    assert len(factors.columns) > 0

    # 检查一些关键因子
    assert 'momentum_5' in factors.columns
    assert 'spread_pct' in factors.columns
    assert 'price_trend' in factors.columns
    assert 'vol_clustering' in factors.columns


def test_predictive_factor_analyzer_initialization():
    """测试PredictiveFactorAnalyzer初始化"""
    analyzer = PredictiveFactorAnalyzer()
    assert analyzer.factors == {}
    assert hasattr(analyzer, 'calculate_technical_factors')
    assert hasattr(analyzer, 'calculate_liquidity_factors')
    assert hasattr(analyzer, 'calculate_commodity_specific_factors')
    assert hasattr(analyzer, 'calculate_all_factors')


def test_build_prediction_model():
    """测试预测模型构建"""
    analyzer = PredictiveFactorAnalyzer()

    # 创建模拟因子数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    factors = pd.DataFrame({
        'factor1': np.random.randn(100),
        'factor2': np.random.randn(100),
        'factor3': np.random.randn(100),
    }, index=dates)

    # 创建一些目标事件
    target_events = [dates[50], dates[70], dates[90]]

    model, importance = analyzer.build_prediction_model(factors, target_events)

    if model is not None:
        assert importance is not None
        assert len(importance) == 3
        assert 'feature' in importance.columns
        assert 'importance' in importance.columns
    else:
        pytest.skip("无法构建模型（可能正样本不足）")


def test_build_prediction_model_no_events():
    """测试无事件时返回None"""
    analyzer = PredictiveFactorAnalyzer()

    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    factors = pd.DataFrame({
        'factor1': np.random.randn(50),
    }, index=dates)

    model, importance = analyzer.build_prediction_model(factors, [])

    assert model is None
    assert importance is None


def test_gamble_analysis_result_dataclass():
    """测试GambleAnalysisResult数据类"""
    result = GambleAnalysisResult(
        symbol="163415",
        name="白银LOF",
        fund_type="LOF",
        abnormal_events_count=5,
        abnormal_events=[],
        current_factors={'momentum_5': 0.05},
        feature_importance=None,
        ai_summary="测试AI分析"
    )

    assert result.symbol == "163415"
    assert result.name == "白银LOF"
    assert result.abnormal_events_count == 5
    assert result.ai_summary == "测试AI分析"


@pytest.mark.integration
def test_analyze_single_with_mock_agent():
    """测试单个标的分析（使用Mock Agent）"""
    from unittest.mock import Mock
    from core.agent.base_agent import BaseAgent

    # 创建Mock Agent
    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="""
### 1. 因子解读
当前动量因子显示上升趋势...

### 2. 历史规律
该标的异常波动通常持续2-3天...

### 3. 时机判断
⏸️ **观望** - 信号不明确，建议继续观察

### 4. 操作建议
暂不建议买入，建议关注成交量和波动率变化...

### 5. 风险提示
主要风险在于...
    """)

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # 使用一个真实的LOF代码进行测试
    result = analyzer.analyze_single("163415", "白银LOF", "LOF")

    if result is not None:
        assert result.symbol == "163415"
        assert result.name == "白银LOF"
        assert result.abnormal_events_count >= 0
        assert result.ai_summary != ""
    else:
        pytest.skip("无法获取测试数据或无异常事件")


def test_analyze_single_with_insufficient_data():
    """测试数据不足的情况"""
    from unittest.mock import Mock
    from core.agent.base_agent import BaseAgent

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    # Mock fetcher返回不足数据
    analyzer.fetcher.get_lof_etf_history = Mock(return_value=None)

    result = analyzer.analyze_single("000000", "Test", "LOF")

    assert result is None


def test_lof_etf_gamble_analyzer_initialization():
    """测试LOFETFGambleAnalyzer初始化"""
    from unittest.mock import Mock
    from core.agent.base_agent import BaseAgent

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    assert analyzer.agent == mock_agent
    assert hasattr(analyzer, 'fetcher')
    assert hasattr(analyzer, 'detector')
    assert hasattr(analyzer, 'factor_analyzer')
    assert hasattr(analyzer, 'analyze_single')
    assert hasattr(analyzer, 'screen_and_analyze')
    assert hasattr(analyzer, 'get_top_factors_across_funds')


@pytest.mark.integration
def test_screen_and_analyze():
    """测试批量筛选分析"""
    from unittest.mock import Mock
    from core.agent.base_agent import BaseAgent

    mock_agent = Mock(spec=BaseAgent)
    mock_agent.chat = Mock(return_value="测试AI分析结果...")

    analyzer = LOFETFGambleAnalyzer(mock_agent)

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    results = analyzer.screen_and_analyze(criteria, top_n=5)

    # 验证结果
    assert isinstance(results, list)
    # 注意：实际数量取决于数据可用性
    if len(results) > 0:
        assert all(isinstance(r, GambleAnalysisResult) for r in results)


def test_get_top_factors_across_funds():
    """测试跨标的因子汇总"""
    from core.agent.base_agent import BaseAgent
    from unittest.mock import Mock

    # 创建模拟结果
    importance1 = pd.DataFrame({
        'feature': ['momentum_5', 'volume_ratio', 'rsi_14'],
        'importance': [0.4, 0.3, 0.2]
    })

    importance2 = pd.DataFrame({
        'feature': ['volume_ratio', 'momentum_5', 'macd'],
        'importance': [0.35, 0.25, 0.15]
    })

    result1 = GambleAnalysisResult(
        symbol="001", name="Fund1", fund_type="LOF",
        abnormal_events_count=5, abnormal_events=[],
        current_factors={}, feature_importance=importance1
    )

    result2 = GambleAnalysisResult(
        symbol="002", name="Fund2", fund_type="ETF",
        abnormal_events_count=3, abnormal_events=[],
        current_factors={}, feature_importance=importance2
    )

    # 需要一个analyzer实例来调用方法
    from core.agent.base_agent import BaseAgent
    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    factor_ranking = analyzer.get_top_factors_across_funds([result1, result2])

    assert len(factor_ranking) > 0
    assert 'momentum_5' in factor_ranking['feature'].values
    assert 'volume_ratio' in factor_ranking['feature'].values

    # momentum_5应该出现2次
    momentum_row = factor_ranking[factor_ranking['feature'] == 'momentum_5']
    assert momentum_row['occurrence_count'].values[0] == 2


def test_get_top_factors_across_funds_empty():
    """测试空结果列表"""
    from core.agent.base_agent import BaseAgent
    from unittest.mock import Mock

    mock_agent = Mock(spec=BaseAgent)
    analyzer = LOFETFGambleAnalyzer(mock_agent)

    factor_ranking = analyzer.get_top_factors_across_funds([])

    assert len(factor_ranking) == 0
    assert 'feature' in factor_ranking.columns
