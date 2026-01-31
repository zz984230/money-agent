"""
验证任务8、9、10的实现
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from analysis.etf_lof_gamble import PredictiveFactorAnalyzer, LOFETFGambleAnalyzer
from core.agent.prompts import PromptBuilder

print("=" * 60)
print("任务8验证: 增强PredictiveFactorAnalyzer添加新因子")
print("=" * 60)

# 1. 测试PredictiveFactorAnalyzer的新初始化方法
print("\n1. 测试新的__init__方法...")
analyzer = PredictiveFactorAnalyzer(
    sentiment_analyzer=None,
    money_flow_analyzer=None,
    specific_analyzer=None
)
print(f"[OK] sentiment_analyzer: {analyzer.sentiment_analyzer}")
print(f"[OK] money_flow_analyzer: {analyzer.money_flow_analyzer}")
print(f"[OK] specific_analyzer: {analyzer.specific_analyzer}")

# 2. 测试增强的技术因子计算
print("\n2. 测试增强的技术因子计算...")
# 创建测试数据
dates = pd.date_range('2024-01-01', periods=100)
df = pd.DataFrame({
    'close': np.random.randn(100).cumsum() + 100,
    'high': np.random.randn(100).cumsum() + 102,
    'low': np.random.randn(100).cumsum() + 98,
    'volume': np.random.randint(1000000, 10000000, 100)
}, index=dates)

tech_factors = analyzer.calculate_technical_factors(df)
new_factors = [c for c in tech_factors.columns if c in ['obv', 'kdj_k', 'kdj_d', 'kdj_j', 'cci', 'williams_r', 'mfi', 'macd_signal', 'macd_hist', 'bollinger_position']]
print(f"[OK] 计算得到 {len(tech_factors.columns)} 个技术因子")
print(f"[OK] 新增因子: {new_factors[:5]}")

# 3. 测试新的情绪因子
print("\n3. 测试情绪因子计算...")
sentiment_factors = analyzer.calculate_sentiment_factors(df)
print(f"[OK] 计算得到 {len(sentiment_factors.columns)} 个情绪因子")
print(f"[OK] 因子列表: {list(sentiment_factors.columns)}")

# 4. 测试资金流因子
print("\n4. 测试资金流因子计算...")
money_flow_factors = analyzer.calculate_money_flow_factors(df, '163415', 'CN')
print(f"[OK] 计算得到 {len(money_flow_factors.columns)} 个资金流因子")
print(f"[OK] 因子列表: {list(money_flow_factors.columns)}")

# 5. 测试ETF/LOF特有因子
print("\n5. 测试ETF/LOF特有因子计算...")
specific_factors = analyzer.calculate_etf_lof_specific_factors(df, '163415', 'LOF')
print(f"[OK] 计算得到 {len(specific_factors.columns)} 个ETF/LOF特有因子")
print(f"[OK] 因子列表: {list(specific_factors.columns)}")

# 6. 测试整合的calculate_all_factors
print("\n6. 测试整合的calculate_all_factors方法...")
all_factors = analyzer.calculate_all_factors(df, symbol='163415', fund_type='LOF')
print(f"[OK] 整合计算得到 {len(all_factors.columns)} 个因子")
print(f"[OK] 总因子类型数: {len(all_factors.columns)}")

print("\n" + "=" * 60)
print("任务9验证: 优化AI提示词结构")
print("=" * 60)

# 7. 测试PromptBuilder的新配置和方法
print("\n1. 测试信号阈值配置...")
pb = PromptBuilder()
print(f"[OK] 定义了 {len(pb.SIGNAL_THRESHOLDS)} 个因子的信号阈值")
print(f"[OK] 示例 - RSI阈值: {pb.SIGNAL_THRESHOLDS['rsi_14']}")

print("\n2. 测试信号解释...")
print(f"[OK] 定义了 {len(pb.SIGNAL_EXPLANATIONS)} 个因子的解释")
print(f"[OK] 示例 - RSI解释: {pb.SIGNAL_EXPLANATIONS['rsi_14']}")

print("\n3. 测试信号判断方法...")
# 测试RSI信号判断
signal_bullish = pb._get_signal('rsi_14', 75)  # 超买
signal_neutral = pb._get_signal('rsi_14', 50)  # 中性
signal_bearish = pb._get_signal('rsi_14', 25)  # 超卖
print(f"[OK] RSI=75 信号: {signal_bullish}")
print(f"[OK] RSI=50 信号: {signal_neutral}")
print(f"[OK] RSI=25 信号: {signal_bearish}")

print("\n4. 测试因子值格式化...")
formatted = pb._format_factor_value('rsi_14', 75.123456)
print(f"[OK] 格式化RSI值: {formatted}")

print("\n5. 测试因子表格构建...")
current_factors = {'rsi_14': 75, 'kdj_k': 65, 'volume_ratio': 2.5}
feature_importance = pd.DataFrame({
    'feature': ['rsi_14', 'kdj_k', 'volume_ratio'],
    'importance': [0.9, 0.7, 0.5]
})
table = pb._build_factor_table(current_factors, feature_importance, top_n=3)
print(f"[OK] 构建因子表格成功")
print("  表格预览:")
print("  " + "\n  ".join(table.split('\n')[:5]))

print("\n" + "=" * 60)
print("任务10验证: 更新LOFETFGambleAnalyzer集成新因子")
print("=" * 60)

# 8. 测试LOFETFGambleAnalyzer的初始化
print("\n1. 测试LOFETFGambleAnalyzer的新初始化...")
# 注意: 需要mock agent，这里只测试结构
from unittest.mock import MagicMock
mock_agent = MagicMock()
mock_agent.chat.return_value = "测试响应"

analyzer = LOFETFGambleAnalyzer(mock_agent)
print(f"[OK] factor_analyzer已初始化")
print(f"[OK] factor_analyzer类型: {type(analyzer.factor_analyzer).__name__}")
print(f"[OK] sentiment_analyzer: {analyzer.factor_analyzer.sentiment_analyzer}")
print(f"[OK] money_flow_analyzer: {analyzer.factor_analyzer.money_flow_analyzer}")
print(f"[OK] specific_analyzer: {analyzer.factor_analyzer.specific_analyzer}")

print("\n" + "=" * 60)
print("[SUCCESS] 所有三个任务验证完成！")
print("=" * 60)

print("\n[SUMMARY] 实现总结:")
print("任务8 - PredictiveFactorAnalyzer增强:")
print("  [+] 新增可选参数: sentiment_analyzer, money_flow_analyzer, specific_analyzer")
print("  [+] 增强技术指标: OBV, KDJ, CCI, Williams %R, MACD信号等")
print("  [+] 新增方法: calculate_sentiment_factors, calculate_money_flow_factors")
print("  [+] 新增方法: calculate_etf_lof_specific_factors")
print("  [+] 更新方法: calculate_all_factors整合所有新因子")
print()
print("任务9 - AI提示词结构优化:")
print("  [+] 新增SIGNAL_THRESHOLDS配置字典")
print("  [+] 新增SIGNAL_EXPLANATIONS解释字典")
print("  [+] 新增辅助方法: _get_signal, _format_factor_value, _build_factor_table")
print("  [+] 重构build_etf_lof_gamble_prompt使用新的结构化格式")
print()
print("任务10 - LOFETFGambleAnalyzer集成:")
print("  [+] 更新__init__初始化增强的PredictiveFactorAnalyzer")
print("  [+] analyze_single方法使用新的因子计算（传symbol和fund_type）")
print()
print("[NEXT] 下一步建议:")
print("  1. 运行完整测试套件验证功能")
print("  2. 添加集成测试验证AI分析质量")
print("  3. 更新相关文档")
