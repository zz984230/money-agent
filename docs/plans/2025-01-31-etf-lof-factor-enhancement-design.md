# ETF/LOF投机分析因子增强设计方案

**日期**: 2025-01-31
**作者**: Claude
**状态**: 设计阶段

## 1. 概述

### 1.1 问题背景

当前ETF/LOF投机分析模块存在以下问题：

1. AI分析结果提示"未提供关键因子的具体数值或来源"
2. 缺少情绪指标、资金流指标等市场维度
3. 因子数据已计算但AI提示词呈现不够清晰
4. 缺少ETF/LOF特有因子（如溢价率）

### 1.2 设计目标

1. **新增情绪指标**：市场宽度、涨停比例、赚钱效应等
2. **新增资金流指标**：主力净流入、大单动能、北向资金等
3. **新增ETF/LOF特有因子**：溢价率、套利空间、流动性排名等
4. **增强技术指标**：OBV、KDJ、CCI、Williams %R等
5. **优化AI提示词**：结构化呈现因子，增加阈值解释

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    LOFETFGambleAnalyzer                     │
│                       (主分析器)                              │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ VolatilityDetector│  │PredictiveFactor│  │  SentimentAnalyzer │
│  (现有组件)       │  │Analyzer         │  │  (新增组件)       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ TechnicalFactors│  │MoneyFlowAnalyzer│  │ ETFLOFSpecific   │
│  (增强现有)      │  │    (新增)        │  │    (新增)        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 文件结构

```
analysis/
├── etf_lof_gamble.py              # 现有文件（增强）
├── factors/
│   ├── __init__.py
│   ├── sentiment_analyzer.py      # 新增：情绪因子分析器
│   ├── money_flow_analyzer.py     # 新增：资金流因子分析器
│   ├── etf_lof_specific.py        # 新增：ETF/LOF特有因子
│   └── technical_indicators.py    # 新增：增强的技术指标
│
data/fetchers/
└── akshare_fetcher.py             # 增强：新增数据获取方法
```

## 3. 新增因子定义

### 3.1 情绪指标 (Sentiment Factors)

| 因子名称 | 计算公式 | 数据来源 | 含义 |
|---------|---------|---------|------|
| `market_breadth_ratio` | 上涨家数 / 总家数 | `stock_zh_a_spot_em()` | 市场宽度，>0.6表示市场强势 |
| `limit_up_ratio` | 涨停家数 / 总家数 | `stock_market_activity_legu()` | 涨停比例，反映做多热情 |
| `advance_decline_line` | 累计(上涨家数-下跌家数) | 计算自市场宽度数据 | AD线，反映市场趋势 |
| `new_high_ratio` | 创新高家数 / 总家数 | 市场数据 | 创新高比例 |
| `market_sentiment_score` | 综合得分(多个情绪指标加权) | 自定义计算 | 0-100分的市场情绪得分 |

### 3.2 资金流指标 (Money Flow Factors)

| 因子名称 | 计算公式 | 数据来源 | 含义 |
|---------|---------|---------|------|
| `main_force_net_inflow` | 主力净流入净额 | `stock_individual_fund_flow()` | 主力资金流向 |
| `main_force_net_inflow_ratio` | 主力净流入净占比 | `stock_individual_fund_flow()` | 主力资金占比 |
| `super_large_order_ratio` | 超大单净流入占比 | `stock_individual_fund_flow()` | 超大单资金态度 |
| `large_order_momentum` | 大单净流入5日变化率 | 计算自资金流数据 | 大单资金动能 |
| `capital_accumulation` | 累计主力净流入/流通市值 | 计算自资金流数据 | 资金累积程度 |
| `northbound_capital_change` | 北向资金持仓变化 | `stock_hsgt_individual_em()` | 外资动向 |

### 3.3 ETF/LOF特有因子 (ETF/LOF Specific Factors)

| 因子名称 | 计算公式 | 数据来源 | 含义 |
|---------|---------|---------|------|
| `premium_discount_rate` | (交易价-净值)/净值 | 场内价格 & 基金净值 | 溢价率(+)或折价率(-) |
| `arbitrage_space` | abs(溢价率) - 套利成本 | 计算自溢价率 | 套利空间，>2%有意义 |
| `price_nav_correlation` | 价格与净值相关系数(20日) | 计算历史数据 | 跟踪偏差度 |
| `liquidity_rank` | 成交额在同类基金中排名 | 计算自成交额 | 流动性相对排名 |
| `turnover_rate_percentile` | 换手率百分位 | 计算自换手率历史 | 换手率相对位置 |

### 3.4 增强的技术指标 (Enhanced Technical Indicators)

| 因子名称 | 计算公式 | 含义 |
|---------|---------|------|
| `obv` | 累计(成交量×价格方向符号) | 能量潮，反映资金进出 |
| `kdj_k` | RSV的3日移动平均 | 随机指标K值 |
| `kdj_d` | K值的3日移动平均 | 随机指标D值 |
| `kdj_j` | 3K - 2D | 随机指标J值 |
| `cci` | (TP-MA_TP)/(0.015×MD) | 顺势指标 |
| `williams_r` | (最高价-收盘价)/(最高价-最低价) | 威廉指标 |
| `force_index` | 收盘价变化 × 成交量 | 强力指数 |
| `money_flow_index` | 100 - 100/(1+资金流比率) | 资金流量指数 |

## 4. 新增类设计

### 4.1 SentimentAnalyzer (情绪因子分析器)

```python
# analysis/factors/sentiment_analyzer.py

class SentimentAnalyzer:
    """市场情绪因子分析器"""

    def __init__(self, fetcher: AKShareFetcher):
        self.fetcher = fetcher
        self._market_breadth_cache = None
        self._cache_time = None

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

    def get_limit_up_stats(self) -> Dict[str, Any]:
        """获取涨停统计数据

        Returns:
            {
                'limit_up_count': 涨停家数,
                'limit_up_ratio': 涨停比例,
                'limit_down_count': 跌停家数,
                'first_limit_up_time': 首次涨停时间
            }
        """

    def calculate_sentiment_score(self) -> float:
        """计算综合情绪得分 (0-100)

        考虑因素：
        - 市场宽度
        - 涨停比例
        - 成交额
        - 新高新低比例

        Returns:
            0-100分，>70偏多，<30偏空
        """

    def get_historical_sentiment(self, days: int = 30) -> pd.DataFrame:
        """获取历史情绪数据（用于计算百分位）

        Args:
            days: 历史天数

        Returns:
            包含历史情绪得分的DataFrame
        """

    def calculate_sentiment_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算情绪因子DataFrame

        Args:
            df: 价格数据DataFrame（用于对齐索引）

        Returns:
            因子DataFrame
            """
```

### 4.2 MoneyFlowAnalyzer (资金流因子分析器)

```python
# analysis/factors/money_flow_analyzer.py

class MoneyFlowAnalyzer:
    """资金流因子分析器"""

    def __init__(self, fetcher: AKShareFetcher):
        self.fetcher = fetcher

    def get_individual_fund_flow(
        self, symbol: str, market: str = 'sz'
    ) -> pd.DataFrame:
        """获取个股资金流数据

        Args:
            symbol: 基金代码
            market: 市场代码 ('sh', 'sz', 'bj')

        Returns:
            资金流数据DataFrame
        """

    def calculate_capital_accumulation(
        self, flow_df: pd.DataFrame
    ) -> pd.Series:
        """计算资金累积程度

        累计主力净流入 / 当前流通市值

        Args:
            flow_df: 资金流数据

        Returns:
            资金累积度序列
        """

    def calculate_order_momentum(
        self, flow_df: pd.DataFrame, period: int = 5
    ) -> pd.Series:
        """计算大单动能

        大单净流入占比的变化率

        Args:
            flow_df: 资金流数据
            period: 周期

        Returns:
            动能序列
        """

    def get_northbound_flow(self, symbol: str = None) -> pd.DataFrame:
        """获取北向资金流向数据

        Args:
            symbol: 个股代码（可选，None表示全市场）

        Returns:
            北向资金数据
        """

    def calculate_money_flow_factors(
        self, df: pd.DataFrame, symbol: str, market: str = 'sz'
    ) -> pd.DataFrame:
        """计算资金流因子DataFrame

        Args:
            df: 价格数据DataFrame
            symbol: 基金代码
            market: 市场代码

        Returns:
            因子DataFrame
        """
```

### 4.3 ETFLOFSpecificAnalyzer (ETF/LOF特有因子分析器)

```python
# analysis/factors/etf_lof_specific.py

class ETFLOFSpecificAnalyzer:
    """ETF/LOF特有因子分析器"""

    def __init__(self, fetcher: AKShareFetcher):
        self.fetcher = fetcher

    def get_premium_discount_rate(
        self, symbol: str, fund_type: str = 'LOF'
    ) -> float:
        """获取溢价率/折价率

        Args:
            symbol: 基金代码
            fund_type: 基金类型

        Returns:
            溢价率（正数）或折价率（负数）
        """

    def calculate_arbitrage_space(
        self,
        premium_rate: float,
        arbitrage_cost: float = 0.015
    ) -> float:
        """计算套利空间

        Args:
            premium_rate: 溢价率
            arbitrage_cost: 套利成本（默认1.5%）

        Returns:
            套利空间，>0表示有套利机会
        """

    def get_price_nav_correlation(
        self, symbol: str, period: int = 20
    ) -> float:
        """获取价格与净值相关系数

        Args:
            symbol: 基金代码
            period: 周期

        Returns:
            相关系数
        """

    def calculate_liquidity_rank(
        self, symbol: str, all_funds: List[Dict]
    ) -> int:
        """计算流动性排名

        Args:
            symbol: 基金代码
            all_funds: 所有基金列表（含成交额）

        Returns:
            排名（越小流动性越好）
        """

    def calculate_turnover_percentile(
        self, symbol: str, historical_data: pd.DataFrame
    ) -> float:
        """计算换手率历史百分位

        Args:
            symbol: 基金代码
            historical_data: 历史数据

        Returns:
            百分位值 (0-1)
        """

    def calculate_etf_lof_specific_factors(
        self, df: pd.DataFrame, symbol: str, fund_type: str,
        all_funds: List[Dict] = None
    ) -> pd.DataFrame:
        """计算ETF/LOF特有因子

        Args:
            df: 价格数据DataFrame
            symbol: 基金代码
            fund_type: 基金类型
            all_funds: 所有基金列表

        Returns:
            因子DataFrame
        """
```

### 4.4 增强的PredictiveFactorAnalyzer

```python
# analysis/etf_lof_gamble.py

class PredictiveFactorAnalyzer:
    """预测因子分析器（增强版）"""

    def __init__(
        self,
        sentiment_analyzer: SentimentAnalyzer = None,
        money_flow_analyzer: MoneyFlowAnalyzer = None,
        specific_analyzer: ETFLOFSpecificAnalyzer = None
    ):
        self.sentiment_analyzer = sentiment_analyzer
        self.money_flow_analyzer = money_flow_analyzer
        self.specific_analyzer = specific_analyzer

    def calculate_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术因子（增强版）

        新增指标：
        - OBV (能量潮)
        - KDJ (随机指标)
        - CCI (顺势指标)
        - Williams %R
        - Force Index
        - Money Flow Index
        """

    def calculate_sentiment_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算情绪因子（新增）"""

    def calculate_money_flow_factors(
        self, df: pd.DataFrame, symbol: str
    ) -> pd.DataFrame:
        """计算资金流因子（新增）"""

    def calculate_etf_lof_specific_factors(
        self, df: pd.DataFrame, symbol: str, fund_type: str
    ) -> pd.DataFrame:
        """计算ETF/LOF特有因子（新增）"""

    def calculate_all_factors(
        self,
        df: pd.DataFrame,
        symbol: str,
        fund_type: str = 'LOF'
    ) -> pd.DataFrame:
        """计算所有因子（整合版）"""
```

## 5. AKShareFetcher增强

### 5.1 新增数据获取方法

```python
# data/fetchers/akshare_fetcher.py

class AKShareFetcher:

    # ... 现有方法 ...

    def get_market_breadth(self) -> Dict[str, Any]:
        """获取市场宽度统计数据

        Returns:
            {
                'up_count': int,
                'down_count': int,
                'flat_count': int,
                'total': int,
                'advance_decline_ratio': float
            }
        """

    def get_limit_up_stats(self) -> pd.DataFrame:
        """获取涨停统计数据

        使用接口：stock_market_activity_legu()
        """

    def get_market_activity(self) -> pd.DataFrame:
        """获取市场赚钱效应分析

        使用接口：stock_market_activity_legu()
        """

    def get_individual_fund_flow(
        self, symbol: str, market: str = 'sz'
    ) -> pd.DataFrame:
        """获取个股资金流数据

        使用接口：stock_individual_fund_flow()

        Args:
            symbol: 6位股票代码
            market: 市场代码 ('sh', 'sz', 'bj')

        Returns:
            包含主力净流入、大单、中单、小单数据的DataFrame
        """

    def get_dragon_tiger_list(self, date: str = None) -> pd.DataFrame:
        """获取龙虎榜数据

        使用接口：stock_lhb_detail_em()

        Args:
            date: 日期字符串 (YYYYMMDD)，None为最新

        Returns:
            龙虎榜详情
        """

    def get_northbound_capital(self, symbol: str = None) -> pd.DataFrame:
        """获取北向资金数据

        使用接口：stock_hsgt_individual_em() 或 stock_hsgt_hist_em()

        Args:
            symbol: 个股代码，None表示全市场

        Returns:
            北向资金持仓或流向数据
        """

    def get_etf_lof_nav(self, symbol: str) -> float:
        """获取ETF/LOF净值

        需要调用相应接口获取最新净值

        Args:
            symbol: 基金代码

        Returns:
            最新净值
        """

    def get_etf_lof_realtime_quote(self, symbol: str) -> Dict:
        """获取ETF/LOF实时行情

        Args:
            symbol: 基金代码

        Returns:
            实时行情字典
        """
```

## 6. AI提示词优化

### 6.1 新的提示词结构

```markdown
你是一位专业的ETF/LOF短线交易分析师。请基于以下数据进行分析：

## 标的概况
- 代码: {symbol}
- 名称: {name}
- 类型: {fund_type}

## 当前行情
- 价格: {price}
- 涨跌幅: {change_pct}%
- 成交量: {volume}
- 波动率(20日): {volatility_20d}

## 技术指标分析

### 趋势类因子
| 指标 | 当前值 | 信号 | 说明 |
|------|--------|------|------|
| MACD | {macd_value} | {signal} | {interpretation} |
| RSI(14) | {rsi_value} | {signal} | {interpretation} |
| DIF/DEA | {dif}/{dea} | {signal} | {interpretation} |

### 动量类因子
| 指标 | 当前值 | 历史分位 | 信号 | 说明 |
|------|--------|----------|------|------|
| 动量5日 | {momentum_5} | {percentile} | {signal} | {interpretation} |
| 动量20日 | {momentum_20} | {percentile} | {signal} | {interpretation} |
| ATR(14) | {atr_value} | {percentile} | {signal} | {interpretation} |

### 资金流因子
| 指标 | 当前值 | 信号 | 说明 |
|------|--------|------|------|
| 主力净流入占比 | {main_force_ratio}% | {signal} | {interpretation} |
| 大单动能 | {large_order_momentum} | {signal} | {interpretation} |
| 资金累积度 | {capital_accumulation} | {signal} | {interpretation} |

### 情绪指标
| 指标 | 当前值 | 市场状态 | 说明 |
|------|--------|----------|------|
| 市场涨跌比 | {breadth_ratio} | {status} | {interpretation} |
| 涨停比例 | {limit_up_ratio} | {status} | {interpretation} |
| 市场情绪得分 | {sentiment_score}/100 | {status} | {interpretation} |

### ETF/LOF特有因子
| 指标 | 当前值 | 信号 | 说明 |
|------|--------|------|------|
| 溢价率 | {premium_rate}% | {signal} | {interpretation} |
| 套利空间 | {arbitrage_space}% | {signal} | {interpretation} |
| 流动性排名 | {liquidity_rank} | {signal} | {interpretation} |

## 历史异常波动事件（最近5个）
{events_table}
总计发现 {total_events} 个异常波动事件

## 综合信号统计
- 🟢 **买入信号** ({buy_count}个): {buy_signals}
- ⚪ **中性信号** ({neutral_count}个): {neutral_signals}
- 🔴 **卖出信号** ({sell_count}个): {sell_signals}

## 因子重要性排序（基于历史波动预测能力）
{factor_importance_table}

## 分析要求

请按以下结构进行分析（使用Markdown格式）：

### 1. 关键因子深度解读

请重点分析以下因子，并给出明确判断：

**趋势判断**
- [ ] MACD处于什么状态？（金叉/死叉/零轴上方/零轴下方）
- [ ] RSI是否进入超买(>70)或超卖(<30)区域？
- [ ] 动量因子是否显示加速或减速？

**资金面**
- [ ] 主力资金是流入还是流出？趋势如何？
- [ ] 大单与散户行为是否背离？

**情绪面**
- [ ] 市场整体情绪是亢奋还是低迷？
- [ ] 涨停家数是否异常？
- [ ] 市场宽度是否健康？

**ETF/LOF特性**
- [ ] 当前溢价/折价程度如何？
- [ ] 是否存在套利机会？
- [ ] 价格与净值背离程度？

请给出每个因子的：当前值、历史位置、信号含义、操作建议

### 2. 历史规律
该标的异常波动的特点是什么？通常持续多久？
触发条件有哪些？

### 3. 时机判断
当前是否适合买入？请给出明确判断：
- ✅ **适合买入** - 因子显示即将出现异常波动
- ⏸️ **观望** - 信号不明确，建议继续观察
- ❌ **不适合买入** - 因子显示风险较高

### 4. 操作建议
如果判断适合买入，请给出：
- **买入点位**: 具体价格（基于当前价格给出）
- **止盈位**: 目标价格（给出1-2个）
- **止损位**: 风险控制价格
- **建议仓位**: 轻仓/中仓/重仓
- **持有周期**: 预计持有天数

如果不适合买入，请说明原因和后续关注点。

### 5. 风险提示
提示本次交易的主要风险点。
```

### 6.2 信号判断逻辑

```python
def get_signal(value, thresholds, interpretation_dict):
    """生成信号标记

    Args:
        value: 当前值
        thresholds: {'buy': x, 'sell': y}
        interpretation_dict: 信号解释字典

    Returns:
        (signal_emoji, interpretation)
    """
    if value >= thresholds['buy']:
        return '🟢', interpretation_dict['buy']
    elif value <= thresholds['sell']:
        return '🔴', interpretation_dict['sell']
    else:
        return '⚪', interpretation_dict['neutral']

# 示例阈值配置
SIGNAL_THRESHOLDS = {
    'rsi': {'buy': 70, 'sell': 30},
    'macd': {'buy': 0, 'sell': 0},  # 需结合DIF/DEA关系
    'momentum_5': {'buy': 0.03, 'sell': -0.02},
    'main_force_ratio': {'buy': 0.05, 'sell': -0.05},
    'market_breadth': {'buy': 0.6, 'sell': 0.4},
    'premium_rate': {'buy': -0.02, 'sell': 0.02},  # 折价买入，溢价谨慎
}
```

## 7. 测试策略

### 7.1 测试文件结构

```
tests/
├── test_factors/
│   ├── __init__.py
│   ├── test_sentiment_analyzer.py
│   ├── test_money_flow_analyzer.py
│   ├── test_etf_lof_specific.py
│   └── test_technical_indicators.py
│
└── test_etf_lof_gamble.py
```

### 7.2 关键测试用例

#### 情绪因子测试
```python
def test_market_breadth_returns_valid_ratio()
def test_sentiment_score_in_valid_range()
def test_sentiment_factors_dataframe_structure()
```

#### 资金流因子测试
```python
def test_fund_flow_returns_dataframe()
def test_capital_accumulation_calculation()
def test_order_momentum_calculation()
```

#### ETF/LOF特有因子测试
```python
def test_premium_rate_calculation()
def test_arbitrage_space_with_cost()
def test_liquidity_rank_calculation()
```

#### 因子验证测试
```python
def test_rsi_range_0_to_100()
def test_kdj_range_0_to_100()
def test_no_infinite_values_in_factors()
def test_factor_consistency()
```

## 8. 实施步骤

1. **阶段一：基础设施**
   - 创建 `analysis/factors/` 目录
   - 实现 `SentimentAnalyzer`
   - 实现 `MoneyFlowAnalyzer`
   - 实现 `ETFLOFSpecificAnalyzer`

2. **阶段二：数据获取**
   - 增强 `AKShareFetcher` 新增方法
   - 添加缓存策略

3. **阶段三：因子整合**
   - 增强 `PredictiveFactorAnalyzer`
   - 整合所有因子计算

4. **阶段四：AI优化**
   - 优化 `build_etf_lof_gamble_prompt`
   - 添加信号判断逻辑
   - 添加因子历史百分位计算

5. **阶段五：测试**
   - 编写单元测试
   - 集成测试
   - 验证AI分析质量

## 9. 风险与注意事项

1. **数据可用性风险**：部分AKShare接口可能不稳定，需要降级策略
2. **API限流**：注意请求频率，合理使用缓存
3. **计算性能**：大量因子计算可能影响性能，考虑异步处理
4. **AI提示词长度**：因子增多后提示词变长，注意不超过模型限制
