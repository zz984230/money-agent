# 可转债技术面与条款分析模块设计

**日期**: 2026-01-29
**模块**: ConvertibleBondTechnicalAnalyzer
**目标**: 构建全面的可转债技术面与条款分析Agent

---

## 1. 设计概述

### 1.1 核心目标

基于用户需求，优先实现**技术面与条款分析**模块，采用：
- **扩展AKShare接口**获取更多技术面数据
- **AI主导分析**，代码仅负责数据获取和准备
- **分析+筛选**双功能输出

### 1.2 设计原则

- **YAGNI**: 只实现当前需要的功能，避免过度设计
- **降级处理**: 数据获取失败时提供合理的替代方案
- **可扩展性**: 为后续基本面分析、市场分析、综合决策预留接口
- **测试驱动**: 关键功能必须有测试覆盖

---

## 2. 整体架构

### 2.1 模块结构

```
money-agent/
├── data/fetchers/
│   └── akshare_fetcher.py          # 扩展技术面数据获取方法
├── analysis/
│   ├── convertible_analysis.py     # 现有通用分析模块
│   └── convertible_technical_analysis.py  # 新技术面分析模块
├── core/agent/
│   └── prompts.py                  # 扩展技术面提示词
├── ui/
│   └── dashboard.py                # 添加技术面分析页面
└── tests/
    └── test_convertible_technical_analysis.py
```

### 2.2 核心组件

**1. 数据获取层** (`AKShareFetcher` 扩展)
- `get_convertible_detail()` - 转债详细信息
- `get_convertible_realtime()` - 实时行情和盘口
- `get_convertible_history()` - 历史价格数据
- `get_cb_index_data()` - 中证转债指数

**2. 数据模型** (`ConvertibleTechnicalData`)
- 结构化数据类，包含所有技术面字段

**3. 分析器** (`ConvertibleBondTechnicalAnalyzer`)
- `analyze_technical()` - 单券技术面分析
- `analyze_terms()` - 条款博弈分析
- `screen_by_technical()` - 批量筛选

**4. AI集成** (`PromptBuilder` 扩展)
- `build_convertible_technical_prompt()` - 技术面分析提示词
- `build_convertible_terms_prompt()` - 条款博弈提示词

---

## 3. 数据结构设计

### 3.1 核心数据类

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ConvertibleTechnicalData:
    """可转债技术面数据"""

    # 基础信息
    cb_code: str
    cb_name: str

    # 基础行情
    price: float
    change_percent: float
    volume: float
    amount: float

    # 转股相关
    conversion_price: float      # 转股价
    conversion_value: float      # 转股价值
    premium_rate: float          # 转股溢价率

    # 债券属性
    bond_rating: str             # 评级
    pure_bond_value: float       # 纯债价值
    ytm: float                   # 到期收益率

    # 条款信息
    call_trigger_price: float    # 强赎触发价
    put_trigger_price: float     # 回售触发价
    conversion_trigger_price: float  # 下修触发价

    # 市场深度
    bid_price: List[float]       # 买一到买五
    ask_price: List[float]       # 卖一到卖五
    bid_volume: List[float]      # 买量
    ask_volume: List[float]      # 卖量

    # 技术指标
    ma5: float                   # 5日均线
    ma20: float                  # 20日均线
    volatility_20d: float        # 20日波动率
```

### 3.2 分析结果结构

```python
@dataclass
class TechnicalAnalysisResult:
    """技术面分析结果"""

    cb_code: str
    cb_name: str
    technical_data: ConvertibleTechnicalData

    # AI分析
    analysis: str                # 完整分析文本
    summary: str                 # 分析摘要

    # 关键信号
    signals: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "type": "偏股/平衡/偏债",
    #     "trend": "上涨/下跌/震荡",
    #     "liquidity": "高/中/低",
    #     "safety_margin": float,
    #     "call_distance": float,    # 距强赎触发距离
    #     "put_distance": float,     # 距回售触发距离
    # }

    # 推荐操作
    recommendation: str = ""     # 买入/持有/卖出
```

---

## 4. AKShare数据获取扩展

### 4.1 新增方法

```python
# 在 data/fetchers/akshare_fetcher.py 中添加

class AKShareFetcher:
    # ... 现有方法 ...

    def get_convertible_detail(self, cb_code: str) -> Optional[Dict]:
        """
        获取单个可转债详细信息

        Args:
            cb_code: 可转债代码

        Returns:
            包含条款、评级等信息的字典

        数据来源: ak.bond_cb_jsl() 或其他可转债接口
        """

    def get_convertible_realtime(self, cb_code: str) -> Optional[Dict]:
        """
        获取可转债实时行情和盘口数据

        Returns:
            {
                "price": float,
                "bid_price": [买一到买五],
                "ask_price": [卖一到卖五],
                "bid_volume": [买一到买五量],
                "ask_volume": [卖一到卖五量],
                ...
            }
        """

    def get_convertible_history(
        self,
        cb_code: str,
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取可转债历史价格数据

        用于计算技术指标（MA、波动率等）
        """

    def get_cb_index_data(self, days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取中证转债指数数据

        用于判断市场整体温度
        """

    def calculate_indicators(
        self,
        history_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        计算技术指标

        Returns:
            {
                "ma5": float,
                "ma20": float,
                "volatility_20d": float,
                ...
            }
        """
```

### 4.2 数据源映射

| 数据项 | AKShare接口 | 字段名 |
|--------|-------------|--------|
| 基础行情 | bond_cb_jsl | trade, changepercent |
| 转股数据 | bond_cb_jsl | 转股价, 转股价值, 转股溢价率 |
| 条款信息 | bond_cb_jsl | 回售价, 强赎价 |
| 历史数据 | bond_zh_hs_cov_daily | close, volume |
| 盘口数据 | bond_zh_hs_cov_spot | bid/ask相关字段 |

---

## 5. 分析模块设计

### 5.1 ConvertibleBondTechnicalAnalyzer

```python
class ConvertibleBondTechnicalAnalyzer:
    """可转债技术面与条款分析器"""

    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.fetcher = AKShareFetcher()
        self.prompt_builder = PromptBuilder()

    def analyze_technical(
        self,
        cb_code: str
    ) -> Optional[TechnicalAnalysisResult]:
        """
        单个转债技术面深度分析

        Args:
            cb_code: 可转债代码

        Returns:
            TechnicalAnalysisResult 分析结果
        """

    def analyze_terms(
        self,
        cb_code: str,
        stock_price: float
    ) -> Optional[Dict]:
        """
        条款博弈分析

        分析强赎、回售、下修条款的触发情况

        Returns:
            {
                "cb_code": str,
                "stock_price": float,
                "call_analysis": str,    # 强赎分析
                "put_analysis": str,     # 回售分析
                "conversion_analysis": str,  # 下修分析
                "recommendation": str    # 条款博弈建议
            }
        """

    def screen_by_technical(
        self,
        criteria: Dict[str, Any],
        top_n: int = 20
    ) -> Optional[List[Dict]]:
        """
        批量技术面筛选

        Args:
            criteria: 筛选条件
                {
                    "price_range": (90, 110),      # 价格区间
                    "premium_max": 30,             # 最大溢价率
                    "ytm_min": -5,                 # 最小YTM
                    "types": ["偏债", "平衡"],     # 转债类型
                    "liquidity_min": 1000000,      # 最小流动性
                    "volatility_max": 0.3,         # 最大波动率
                }
            top_n: 返回前N个结果

        Returns:
            筛选结果列表，按综合评分排序
        """
```

### 5.2 分析流程

```
输入: 转债代码
  ↓
1. 数据获取
   - 基础行情 (bond_cb_jsl)
   - 实时盘口 (bond_zh_hs_cov_spot)
   - 历史数据 (bond_zh_hs_cov_daily)
   - 条款信息 (bond_cb_jsl)
  ↓
2. 数据整合与计算
   - 构建ConvertibleTechnicalData
   - 计算技术指标 (MA, 波动率)
   - 计算信号 (类型、趋势、流动性)
  ↓
3. AI分析
   - 构建提示词
   - 调用Agent.chat()
   - 获取分析文本
  ↓
4. 结果结构化
   - 提取关键信号
   - 生成摘要
   - 构建TechnicalAnalysisResult
  ↓
输出: TechnicalAnalysisResult
```

---

## 6. 提示词工程

### 6.1 技术面分析提示词

```python
def build_convertible_technical_prompt(
    self,
    cb_data: ConvertibleTechnicalData,
    stock_data: Optional[Dict] = None
) -> str:
    """构建可转债技术面分析提示词"""

    prompt = f"""
你是一位专业的可转债技术分析师。请分析以下可转债的技术面情况：

【基础信息】
代码：{cb_data.cb_code}
名称：{cb_data.cb_name}
现价：{cb_data.price}元
涨跌幅：{cb_data.change_percent}%
成交量：{cb_data.volume}手

【转股数据】
转股价：{cb_data.conversion_price}元
转股价值：{cb_data.conversion_value}元
转股溢价率：{cb_data.premium_rate}%

【债券属性】
债券评级：{cb_data.bond_rating}
纯债价值：{cb_data.pure_bond_value}元
到期收益率：{cb_data.ytm}%

【条款信息】
强赎触发价：{cb_data.call_trigger_price}元
回售触发价：{cb_data.put_trigger_price}元

【技术指标】
5日均线：{cb_data.ma5}元
20日均线：{cb_data.ma20}元
20日波动率：{cb_data.volatility_20d}%

【市场深度】
{self._format_market_depth(cb_data)}

请从以下几个维度进行分析：

1. **定位判断**：判断该转债属于偏股型、平衡型还是偏债型，并说明理由
2. **估值分析**：结合绝对价格、溢价率、YTM评估估值水平
3. **动能分析**：分析价格趋势、成交量变化、波动率情况
4. **条款博弈**：分析强赎、回售、下修条款的触发距离和博弈空间
5. **流动性分析**：根据盘口数据评估流动性和冲击成本
6. **投资建议**：综合以上分析，给出买入/持有/卖出建议及核心逻辑

请用简洁专业的语言进行分析，重点关注投资价值和风险点。
"""
    return prompt
```

### 6.2 条款博弈提示词

```python
def build_convertible_terms_prompt(
    self,
    cb_data: ConvertibleTechnicalData,
    stock_price: float,
    stock_name: str
) -> str:
    """构建条款博弈分析提示词"""

    # 计算距离各条款触发价的位置
    call_distance = (stock_price / cb_data.call_trigger_price - 1) * 100
    put_distance = (stock_price / cb_data.put_trigger_price - 1) * 100

    prompt = f"""
请分析以下可转债的条款博弈情况：

【转债信息】
{cb_data.cb_name} ({cb_data.cb_code})
转债价格：{cb_data.price}元

【正股信息】
{stock_name}
当前股价：{stock_price}元

【条款触发分析】
强赎条款：
  - 触发价：{cb_data.call_trigger_price}元
  - 当前距离：{call_distance:.2f}%
  - {"已触发" if stock_price >= cb_data.call_trigger_price else "未触发"}

回售条款：
  - 触发价：{cb_data.put_trigger_price}元
  - 当前距离：{put_distance:.2f}%
  - {"已触发" if stock_price <= cb_data.put_trigger_price else "未触发"}

请分析：
1. 各条款的触发可能性和时间窗口
2. 发行人可能的应对策略（强赎、下修、不行使权利）
3. 投资者的应对策略和风险收益分析
4. 给出具体的操作建议
"""
    return prompt
```

---

## 7. 错误处理与边界情况

### 7.1 降级处理策略

| 场景 | 降级方案 |
|------|----------|
| 实时行情获取失败 | 使用历史最新数据 + AI知识库 |
| 条款数据缺失 | 使用通用条款模板 + AI推断 |
| 盘口数据缺失 | 仅分析基础技术面，跳过流动性分析 |
| 历史数据不足(<5天) | 跳过技术指标计算，仅用当前数据 |
| 正股数据缺失 | 仅分析转债自身，不涉及正股分析 |

### 7.2 验证规则

```python
def _validate_convertible_data(data: Dict) -> bool:
    """验证可转债数据的合理性"""

    # 价格范围检查
    if not (0 <= data.get('price', 0) <= 300):
        logger.warning(f"异常价格: {data.get('price')}")

    # 溢价率检查
    premium = data.get('premium_rate', 0)
    if not (-100 <= premium <= 500):
        logger.warning(f"异常溢价率: {premium}")

    # 数据时效性检查
    data_time = data.get('timestamp')
    if data_time and (datetime.now() - data_time).days > 1:
        logger.warning("数据超过1天，可能不是最新数据")
```

### 7.3 特殊情况处理

| 情况 | 处理方式 |
|------|----------|
| 停牌转债 | 返回最后交易数据 + 明确提示 |
| 新上市转债 | 历史数据不足时提示 |
| 即将到期转债 | 高优先级风险提示 |
| 触发强赎转债 | 强制提示强赎风险 |
| 已退市转债 | 返回错误，不进行分析 |

---

## 8. UI集成

### 8.1 Dashboard页面设计

```python
# ui/dashboard.py 中添加

def show_convertible_technical_page():
    """可转债技术面分析页面"""

    st.title("可转债技术面分析")

    tab1, tab2 = st.tabs(["单券分析", "技术面筛选"])

    with tab1:
        # 单券分析
        cb_code = st.text_input("转债代码", placeholder="如113527")
        if st.button("分析"):
            result = analyzer.analyze_technical(cb_code)
            # 显示结果

    with tab2:
        # 技术面筛选
        col1, col2 = st.columns(2)
        with col1:
            price_min = st.number_input("最低价格", value=90)
            price_max = st.number_input("最高价格", value=110)
        with col2:
            premium_max = st.number_input("最大溢价率(%)", value=30)

        if st.button("筛选"):
            results = analyzer.screen_by_technical({
                "price_range": (price_min, price_max),
                "premium_max": premium_max
            })
            # 显示筛选结果
```

### 8.2 结果展示

- **基础信息卡片**：代码、名称、价格、涨跌幅
- **技术指标图表**：价格走势、MA线、成交量
- **信号指示器**：类型标签（偏股/平衡/偏债）、趋势箭头
- **AI分析文本**：结构化展示，可折叠各维度分析
- **操作建议**：醒目显示买入/持有/卖出

---

## 9. 测试策略

### 9.1 单元测试

```python
# tests/test_convertible_technical_analysis.py

class TestConvertibleTechnicalAnalyzer:

    @pytest.fixture
    def mock_agent(self):
        """模拟AI Agent"""
        agent = Mock(spec=BaseAgent)
        agent.chat.return_value = """
【定位判断】该转债属于平衡型可转债...
【估值分析】当前价格105元，溢价率15%...
【投资建议】持有观望...
"""
        return agent

    def test_analyze_technical_normal_case(self, mock_agent):
        """测试正常技术面分析"""

    def test_analyze_technical_missing_depth_data(self, mock_agent):
        """测试盘口数据缺失"""

    def test_screen_by_technical_filters(self, mock_agent):
        """测试筛选功能"""

    def test_analyze_terms_call_trigger(self, mock_agent):
        """测试强赎触发场景"""
```

### 9.2 集成测试

```python
@pytest.mark.integration
class TestConvertibleTechnicalIntegration:
    """集成测试（需要真实API）"""

    def test_analyze_technical_real_data(self):
        """使用真实数据测试完整流程"""

    def test_screen_by_technical_real_market(self):
        """真实市场筛选测试"""
```

### 9.3 测试覆盖目标

- 单元测试覆盖率：80%+
- 关键路径：100%覆盖
- 边界情况：全面测试
- 集成测试：核心功能验证

---

## 10. 实施路线图

### 阶段1：数据获取扩展 (1-2天)

- [ ] 在 `AKShareFetcher` 中添加技术面数据获取方法
- [ ] 实现 `ConvertibleTechnicalData` 数据类
- [ ] 单元测试验证数据获取

### 阶段2：分析模块核心功能 (2-3天)

- [ ] 实现 `ConvertibleBondTechnicalAnalyzer` 类
- [ ] 添加 `analyze_technical()` 方法
- [ ] 添加 `analyze_terms()` 方法
- [ ] 扩展 `PromptBuilder` 添加技术面提示词

### 阶段3：筛选功能 (1-2天)

- [ ] 实现 `screen_by_technical()` 方法
- [ ] 添加多条件筛选逻辑
- [ ] 结果排序和格式化

### 阶段4：UI集成 (1天)

- [ ] 在 `dashboard.py` 中添加技术面分析页面
- [ ] 添加筛选功能UI组件
- [ ] 显示分析结果和信号

### 阶段5：测试与优化 (1-2天)

- [ ] 完善单元测试和集成测试
- [ ] 性能优化（缓存、并发）
- [ ] 文档完善

**总计：6-10天**

---

## 11. 依赖与风险

### 11.1 依赖项

- AKShare接口稳定性和数据完整性
- GLM-4.7 API的调用限制和稳定性
- 历史数据的可用性

### 11.2 潜在风险

| 风险 | 缓解措施 |
|------|----------|
| AKShare接口变更 | 使用稳定接口，做好版本兼容 |
| 数据不完整 | 降级处理，使用AI知识库补充 |
| AI分析质量 | 持续优化提示词，添加示例 |
| 性能问题 | 数据缓存，异步处理 |
| 实时性延迟 | 明确数据时间戳，提示用户 |

---

## 12. 后续扩展方向

本设计为后续模块预留了扩展接口：

### 技能二：正股基本面分析
- 复用 `get_convertible_detail()` 中的正股代码
- 扩展财务数据获取
- 添加基本面分析提示词

### 技能三：市场与资金分析
- 复用 `get_cb_index_data()` 指数数据
- 添加资金流向数据获取
- 扩展市场温度判断逻辑

### 技能四：综合决策与估值
- 整合上述三个模块的分析结果
- 构建多维度打分系统
- 生成最终投资建议

---

## 13. 设计决策记录

1. **AI主导分析**: 充分利用AI的理解能力，减少复杂规则编码
2. **扩展AKShare而非引入新数据源**: 保持项目简单性，减少依赖
3. **降级处理优先**: 确保在数据不完美时仍能提供有价值的分析
4. **模块化设计**: 新模块独立于现有模块，不影响现有功能

---

**文档版本**: 1.0
**创建日期**: 2026-01-29
**状态**: 待实施
