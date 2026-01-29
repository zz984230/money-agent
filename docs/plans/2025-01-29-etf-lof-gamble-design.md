# ETF/LOF投机异常波动筛选器设计文档

**日期**: 2025-01-29
**功能**: 识别波动异常的LOF/ETF并寻找预测因子，提供AI分析和操作建议

---

## 1. 需求概述

### 1.1 功能目标
- 识别大宗商品LOF和海外ETF在2-3天内的突增突降现象
- 计算多类预测因子，发现异常波动前的信号
- AI分析因子并给出具体的买入时机、点位、止盈止损建议

### 1.2 使用场景
- **日内/短线交易**：用户希望在1-3天内快速进出，捕捉波动机会
- **主动触发**：用户点击按钮触发分析，查看结果列表
- **两者结合**：支持历史回测分析和实时预测预警

---

## 2. 模块架构

### 2.1 新增模块

```
analysis/
├── etf_lof_gamble.py          # 核心分析器
│   ├── VolatilityDetector     # 异常波动检测
│   ├── PredictiveFactorAnalyzer # 预测因子计算
│   └── LOFETFGambleAnalyzer   # 主分析器（含AI集成）

data/fetchers/
└── akshare_fetcher.py         # 扩展：添加LOF/ETF数据获取

core/agent/
└── prompts.py                 # 扩展：添加build_etf_lof_gamble_prompt()

ui/
└── dashboard.py               # 扩展：添加ETF/LOF投机菜单和页面
```

### 2.2 数据流

```
用户点击筛选
    ↓
LOFETFGambleAnalyzer.screen_and_analyze()
    ↓
AKShareFetcher: 获取LOF/ETF列表和历史数据
    ↓
对每个标的:
    ├─ VolatilityDetector: 检测异常事件
    ├─ PredictiveFactorAnalyzer: 计算因子
    └─ build_prediction_model: 训练模型
    ↓
汇总结果 + AI分析
    ↓
UI展示结果
```

---

## 3. 异常波动检测

### 3.1 VolatilityDetector类

**核心方法**: `detect_sudden_moves(price_series, window=3, threshold=0.15)`

- **参数**:
  - `window`: 观察窗口天数（默认3天）
  - `threshold`: 变化阈值（默认15%）

- **检测逻辑**:
  ```python
  returns = price_series.pct_change(window)
  abnormal = abs(returns) > threshold
  ```

- **返回**:
  - 异常波动日期列表
  - 事件详情: 日期、收益率、起始/结束价格、波动率

### 3.2 多时间框架分析

**方法**: `multi_timeframe_analysis(price_series)`

- 同时检测2天、3天、5天窗口
- 计算综合指标:
  - 最大/最小单日收益率
  - 20日波动率
  - 夏普比率

---

## 4. 预测因子系统

### 4.1 PredictiveFactorAnalyzer类

计算三类预测因子：

**技术因子**:
- 价格动量: 5日/10日/20日收益率
- 波动率: 20日标准差、ATR(14)
- 成交量: 量比、5日/20日成交量比
- 技术指标: RSI(14)、MACD、布林带带宽
- 价量背离: 价格变化 - 成交量变化

**流动性因子**:
- 换手率（估算）
- 买卖价差百分比
- 流动性冲击

**大宗商品特有因子**:
- 价格趋势（20日）
- 波动聚集性（5日/20日波动率比）

### 4.2 预测模型

**方法**: `build_prediction_model(factors, target_events, lookback_days=10)`

- 使用RandomForestClassifier
- 标记事件前1天为正样本
- 处理类别不平衡（stratify采样）
- 输出特征重要性排序

---

## 5. 完整分析流程

### 5.1 LOFETFGambleAnalyzer类

**方法**: `run_analysis(criteria, top_n)`

1. **获取目标列表**
   - 筛选大宗商品LOF（关键词: 商品、黄金、原油、白银等）
   - 筛选海外ETF（关键词: 美股、港股、德国、日本等）

2. **逐个分析**
   - 获取历史数据（默认365天）
   - 检测异常事件
   - 计算预测因子
   - 训练预测模型

3. **生成结果**
   - 异常事件统计
   - 因子重要性
   - AI分析和操作建议

4. **因子汇总**
   - 跨标的因子排名
   - Top关键因子推荐

---

## 6. AI智能体分析

### 6.1 Prompt构建

**方法**: `PromptBuilder.build_etf_lof_gamble_prompt(...)`

**输入数据**:
- 标的概况（代码、名称、类型）
- 当前行情（价格、涨跌幅、成交量、波动率）
- 历史异常事件（最近5个）
- Top 5关键因子及当前值

**AI输出结构**:
1. **因子解读**: 当前因子说明了什么
2. **历史规律**: 该标的异常波动的特点
3. **时机判断**: ✅适合买入 / ⏸️观望 / ❌不适合
4. **操作建议**:
   - 买入点位（具体价格）
   - 止盈位（1-2个目标价格）
   - 止损位
   - 建议仓位（轻/中/重）
   - 持有周期（天数）
5. **风险提示**: 主要风险点

### 6.2 结果数据结构

```python
@dataclass
class GambleAnalysisResult:
    symbol: str
    name: str
    fund_type: str

    # 异常波动数据
    abnormal_events_count: int
    abnormal_events: list[dict]

    # 因子数据
    current_factors: dict
    feature_importance: pd.DataFrame

    # AI分析
    ai_summary: str        # 因子解读和历史规律
    timing_advice: str     # 时机判断
    action_advice: str     # 操作建议

    # 具体操作
    entry_price: float | None
    stop_loss: float | None
    take_profit: list[float] | None
    position_size: str | None
    hold_period: str | None
```

---

## 7. UI界面设计

### 7.1 侧边栏菜单

添加"ETF/LOF投机"选项

### 7.2 页面结构

**Tab1 - 异常波动筛选**:
- 筛选表单:
  - 时间窗口: 2天/3天/5天（默认3天）
  - 波动阈值: 5%-30%（默认15%）
  - 标的类型: 大宗商品LOF / 海外ETF / 全部
  - 返回数量: 5-50个（默认20个）
- 结果表格: 代码、名称、异常事件数、AI判断
- 点击展开查看详细分析

**Tab2 - AI深度分析**:
- 输入代码+名称或从筛选结果选择
- 卡片式展示:
  - 当前行情概览
  - 因子解读
  - 历史规律
  - 时机判断（醒目显示）
  - 操作建议（买入点位、止盈止损）
  - 风险提示

---

## 8. 数据获取扩展

### 8.1 AKShareFetcher新增方法

```python
def get_lof_list() -> pd.DataFrame:
    """获取所有LOF基金列表"""

def get_commodity_lof_list() -> list[dict]:
    """筛选大宗商品LOF"""

def get_overseas_etf_list() -> list[dict]:
    """筛选海外相关ETF"""

def get_lof_etf_history(symbol: str, period: int = 365) -> pd.DataFrame:
    """获取LOF/ETF历史行情"""
```

---

## 9. 错误处理

1. **数据获取失败**: 单个标的失败时跳过，继续处理其他标的
2. **数据不足**: 历史数据少于100天时跳过
3. **无异常事件**: 跳过因子分析，返回空结果
4. **模型训练失败**: 捕获异常，返回部分结果
5. **UI异常**: 使用try-catch，显示友好错误提示

---

## 10. 测试策略

### 10.1 单元测试

`tests/test_etf_lof_gamble.py`:
- `test_detect_sudden_moves()`: 测试异常检测
- `test_calculate_factors()`: 测试因子计算
- `test_no_abnormal_events()`: 测试无异常情况
- 使用Mock数据，不依赖实时API

### 10.2 集成测试

标记为 `@pytest.mark.integration`（默认跳过）:
- 使用真实AKShare API
- 测试完整分析流程

---

## 11. 实现优先级

**Phase 1 - 核心功能**:
1. 扩展数据获取器
2. 实现VolatilityDetector
3. 基础UI筛选功能

**Phase 2 - 因子系统**:
4. 实现PredictiveFactorAnalyzer
5. 实现预测模型
6. 因子分析Tab

**Phase 3 - AI集成**:
7. 实现Prompt构建
8. 实现AI分析调用
9. 完善UI展示

**Phase 4 - 测试与优化**:
10. 单元测试
11. 集成测试
12. 性能优化（缓存）

---

## 12. 依赖

**新增Python依赖**:
- `scikit-learn`: RandomForest模型
- `talib`: 技术指标计算（若已有可复用）

**AKShare限制**:
- LOF/ETF数据API可用性需验证
- 海外ETF数据可能不完整

---

## 13. 总结

本设计为Money-Agent添加了ETF/LOF投机分析功能，包括：
- 异常波动检测（2-3天突增突降）
- 多因子预测系统（技术、流动性、大宗商品特有）
- AI智能分析和操作建议（买入时机、点位、止盈止损）
- 完整的UI界面（筛选 + 深度分析）

核心特点：
- 用户主动触发，按需分析
- 历史回测 + 实时分析结合
- AI给出具体可执行的操作建议
