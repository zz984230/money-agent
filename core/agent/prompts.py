"""
Prompt Engineering Module
提示词工程模块，用于构建各种AI分析任务的提示词
"""

from typing import Dict, List, Optional, Union
import pandas as pd


class PromptBuilder:
    """提示词构建器，负责生成各种金融分析任务的提示词"""

    # ETF/LOF投机分析信号阈值配置
    SIGNAL_THRESHOLDS = {
        'rsi_14': {'overbought': 70, 'oversold': 30, 'neutral_range': (30, 70)},
        'kdj_k': {'overbought': 80, 'oversold': 20, 'neutral_range': (20, 80)},
        'kdj_j': {'overbought': 100, 'oversold': 0, 'neutral_range': (0, 100)},
        'williams_r': {'overbought': -20, 'oversold': -80, 'neutral_range': (-80, -20)},
        'cci': {'overbought': 100, 'oversold': -100, 'neutral_range': (-100, 100)},
        'mfi': {'overbought': 80, 'oversold': 20, 'neutral_range': (20, 80)},
        'macd_hist': {'bullish': 0, 'bearish': 0},
        'bollinger_position': {'upper': 0.8, 'lower': 0.2, 'neutral_range': (0.2, 0.8)},
        'volume_ratio': {'high': 2.0, 'low': 0.5},
        'volatility_20': {'high': 0.03, 'low': 0.01},
        'obv_divergence': {'bullish': 1.0, 'bearish': -1.0},
        'momentum_reversal': {'strong': 0.05, 'weak': -0.05},
    }

    # 信号解释字典
    SIGNAL_EXPLANATIONS = {
        'rsi_14': 'RSI相对强弱指标，高于{overbought}超买，低于{oversold}超卖',
        'kdj_k': 'KDJ随机指标K值，高于{overbought}超买，低于{oversold}超卖',
        'kdj_j': 'KDJ随机指标J值，敏感性更强，高于{overbought}极度超买',
        'williams_r': '威廉指标，高于{oversold}超卖（注意反向），低于{overbought}超买',
        'cci': '顺势指标，高于{overbought}超买，低于{oversold}超卖',
        'mfi': '资金流量指标，结合成交量的RSI，高于{overbought}资金流入过度',
        'macd_hist': 'MACD柱状图，正值看涨，负值看跌',
        'bollinger_position': '布林带位置，高于{upper}接近上轨（超买），低于{lower}接近下轨（超卖）',
        'volume_ratio': '量比，高于{high}放量，低于{low}缩量',
        'volatility_20': '20日波动率，高于{high}高波动，低于{low}低波动',
        'obv_divergence': 'OBV背离，高于{bullish}资金净流入，低于{bearish}资金净流出',
        'momentum_reversal': '动量反转，正值短期强于长期，负值短期弱于长期',
    }

    def __init__(self):
        """初始化提示词构建器"""
        self.system_prompt = """你是一位专业的A股投资分析师，拥有丰富的市场分析经验。
请基于提供的金融市场数据和公司信息，进行客观、专业、深入的分析。
分析应该包括：
1. 关键指标解读
2. 趋势分析
3. 风险评估
4. 投资建议（如有必要）
请保持客观中立，避免主观臆断。"""

    def _get_signal(self, factor_name: str, factor_value: float) -> str:
        """
        根据因子值判断信号

        Args:
            factor_name: 因子名称
            factor_value: 因子值

        Returns:
            信号字符串（bullish/bearish/neutral）
        """
        if factor_name not in self.SIGNAL_THRESHOLDS:
            return 'neutral'

        thresholds = self.SIGNAL_THRESHOLDS[factor_name]

        # 处理不同的阈值类型
        if 'overbought' in thresholds and 'oversold' in thresholds:
            if factor_value > thresholds['overbought']:
                return 'bearish' if factor_name in ['williams_r'] else 'bullish'
            elif factor_value < thresholds['oversold']:
                return 'bullish' if factor_name in ['williams_r'] else 'bearish'
            else:
                return 'neutral'
        elif 'bullish' in thresholds and 'bearish' in thresholds:
            if factor_value > thresholds['bullish']:
                return 'bullish'
            elif factor_value < thresholds['bearish']:
                return 'bearish'
            else:
                return 'neutral'
        elif 'upper' in thresholds and 'lower' in thresholds:
            if factor_value > thresholds['upper']:
                return 'bearish'  # 接近上轨，可能回调
            elif factor_value < thresholds['lower']:
                return 'bullish'  # 接近下轨，可能反弹
            else:
                return 'neutral'

        return 'neutral'

    def _format_factor_value(self, factor_name: str, factor_value: float) -> str:
        """
        格式化因子值显示

        Args:
            factor_name: 因子名称
            factor_value: 因子值

        Returns:
            格式化后的字符串
        """
        # 根据因子类型选择合适的格式
        if factor_name in ['rsi_14', 'kdj_k', 'kdj_j', 'mfi', 'bollinger_position']:
            return f"{factor_value:.2f}"
        elif factor_name in ['williams_r', 'cci', 'macd_hist', 'obv_divergence']:
            return f"{factor_value:.2f}"
        elif factor_name in ['volume_ratio', 'volatility_20', 'momentum_reversal']:
            return f"{factor_value:.4f}"
        else:
            return f"{factor_value:.6f}"

    def _build_factor_table(
        self,
        current_factors: Dict,
        feature_importance: pd.DataFrame,
        top_n: int = 10
    ) -> str:
        """
        构建因子表格（带信号解读）

        Args:
            current_factors: 当前因子值字典
            feature_importance: 因子重要性DataFrame
            top_n: 显示前N个因子

        Returns:
            Markdown格式的因子表格字符串
        """
        if len(feature_importance) == 0:
            return "无因子数据"

        top_factors = feature_importance.head(top_n)

        table_lines = []
        table_lines.append("| 因子名称 | 当前值 | 信号 | 说明 |")
        table_lines.append("|---------|-------|------|------|")

        for _, row in top_factors.iterrows():
            factor_name = row['feature']
            factor_value = current_factors.get(factor_name, 0)

            # 获取信号
            signal = self._get_signal(factor_name, factor_value)
            signal_icon = {'bullish': '🟢看涨', 'bearish': '🔴看跌', 'neutral': '⚪中性'}.get(signal, '⚪中性')

            # 格式化值
            formatted_value = self._format_factor_value(factor_name, factor_value)

            # 获取解释
            explanation_template = self.SIGNAL_EXPLANATIONS.get(factor_name, '')
            explanation = explanation_template.format(**self.SIGNAL_THRESHOLDS.get(factor_name, {}))

            table_lines.append(f"| {factor_name} | {formatted_value} | {signal_icon} | {explanation} |")

        return "\n".join(table_lines)

    def _format_criteria(self, criteria: Dict[str, Dict[str, Union[int, float]]]) -> str:
        """
        格式化筛选条件

        Args:
            criteria: 筛选条件字典，如 {"pe": {"max": 30}, "roe": {"min": 15}}

        Returns:
            格式化后的筛选条件字符串
        """
        formatted_conditions = []

        for key, value in criteria.items():
            if isinstance(value, dict):
                for op, val in value.items():
                    if op == "max":
                        formatted_conditions.append(f"{key} ≤ {val}")
                    elif op == "min":
                        formatted_conditions.append(f"{key} ≥ {val}")
                    elif op == "eq":
                        formatted_conditions.append(f"{key} = {val}")

        return "，".join(formatted_conditions)

    def build_stock_screening_prompt(self, criteria: Dict[str, Dict[str, Union[int, float]]], stock_count: int = 10) -> str:
        """
        构建选股提示词

        Args:
            criteria: 筛选条件字典
            stock_count: 需要筛选的股票数量

        Returns:
            构建好的选股提示词
        """
        formatted_criteria = self._format_criteria(criteria)

        prompt = f"""作为专业的选股分析师，请根据以下筛选条件，从A股市场中筛选出符合条件的{stock_count}只优质股票：

筛选条件：
{formatted_criteria}

请重点关注以下方面：
1. 基本面指标（PE、PB、ROE、净利润增长率等）
2. 技术面走势
3. 行业前景
4. 流动性指标

请返回股票代码、股票名称、主要指标以及简要的投资理由。"""

        return prompt

    def build_market_analysis_prompt(self, index_code: str, date: str) -> str:
        """
        构建市场分析提示词

        Args:
            index_code: 指数代码
            date: 分析日期

        Returns:
            构建好的市场分析提示词
        """
        prompt = f"""请对以下市场指数进行分析：

指数代码：{index_code}
分析日期：{date}

请从以下几个方面进行分析：
1. 指数走势分析（短期、中期、长期）
2. 成交量分析
3. 市场情绪指标
4. 主要影响因素
5. 后市展望

请提供详细的数据分析和专业的见解。"""

        return prompt

    def build_stock_analysis_prompt(self, symbol: str, company_name: str, analysis_type: str = "comprehensive") -> str:
        """
        构建个股分析提示词

        Args:
            symbol: 股票代码
            company_name: 公司名称
            analysis_type: 分析类型（comprehensive/technical/fundamental）

        Returns:
            构建好的个股分析提示词
        """
        if analysis_type == "technical":
            prompt = f"""请对以下股票进行技术分析：

股票代码：{symbol}
股票名称：{company_name}

请重点分析：
1. K线走势分析
2. 技术指标（MACD、RSI、均线等）
3. 支撑位和压力位
4. 交易量分析
5. 短期走势预测

请提供详细的技术分析图表和解读。"""
        elif analysis_type == "fundamental":
            prompt = f"""请对以下股票进行基本面分析：

股票代码：{symbol}
股票名称：{company_name}

请重点分析：
1. 公司基本面状况
2. 财务状况分析（收入、利润、负债等）
3. 行业地位和竞争优势
4. 成长性和盈利能力
5. 风险因素评估

请提供详细的财务数据分析和基本面评估。"""
        else:
            prompt = f"""请对以下股票进行全面分析：

股票代码：{symbol}
股票名称：{company_name}

请从以下几个方面进行综合分析：
1. 基本面分析
   - 公司财务状况
   - 行业地位和前景
   - 竞争优势
   - 成长性

2. 技术面分析
   - 股价走势
   - 技术指标
   - 成交量分析

3. 风险评估
   - 系统性风险
   - 个股风险
   - 流动性风险

4. 投资建议
   - 价值判断
   - 时机选择
   - 风险提示

请提供全面、客观、深入的分析报告。"""

        return prompt

    def build_etf_analysis_prompt(self, etf_code: str, etf_name: str) -> str:
        """
        构建 ETF 分析提示词

        Args:
            etf_code: ETF 代码
            etf_name: ETF 名称

        Returns:
            构建好的 ETF 分析提示词
        """
        prompt = f"""请对以下ETF基金进行分析：

ETF代码：{etf_code}
ETF名称：{etf_name}

请重点分析：
1. ETF 基本信息跟踪标的、规模、费率等）
2. 历史业绩表现
3. 持仓结构分析
4. 流动性分析
5. 适合的投资场景
6. 风险提示

请提供详细的ETF分析报告。"""

        return prompt

    def build_convertible_analysis_prompt(self, cb_code: str, cb_name: str) -> str:
        """
        构建可转债分析提示词

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称

        Returns:
            构建好的可转债分析提示词
        """
        prompt = f"""请对以下可转债进行分析：

可转债代码：{cb_code}
可转债名称：{cb_name}

请重点分析：
1. 可转债基本信息（发行规模、转股价、期限等）
2. 正股表现分析
3. 可转债条款分析（转股条款、回售条款、赎回条款等）
4. 估值分析（纯债价值、期权价值）
5. 投资价值评估
6. 风险提示

请提供详细的可转债分析报告。"""

        return prompt

    def build_convertible_technical_prompt(
        self,
        technical_data: 'ConvertibleTechnicalData'
    ) -> str:
        """
        构建可转债技术面分析提示词

        Args:
            technical_data: ConvertibleTechnicalData 对象

        Returns:
            构建好的技术面分析提示词
        """
        prompt = f"""你是一位专业的可转债技术分析师。请分析以下可转债的技术面情况：

【基础信息】
代码：{technical_data.cb_code}
名称：{technical_data.cb_name}
现价：{technical_data.price}元
涨跌幅：{technical_data.change_percent}%
成交量：{technical_data.volume}手

【转股数据】
转股价：{technical_data.conversion_price}元
转股价值：{technical_data.conversion_value}元
转股溢价率：{technical_data.premium_rate}%

【债券属性】
债券评级：{technical_data.bond_rating}
纯债价值：{technical_data.pure_bond_value}元
到期收益率：{technical_data.ytm}%

【条款信息】
强赎触发价：{technical_data.call_trigger_price}元
回售触发价：{technical_data.put_trigger_price}元

【技术指标】
5日均线：{technical_data.ma5}元
20日均线：{technical_data.ma20}元
20日波动率：{technical_data.volatility_20d}%

请从以下几个维度进行分析：

1. **定位判断**：判断该转债属于偏股型、平衡型还是偏债型，并说明理由
2. **动能分析**：分析价格趋势、成交量变化、波动率情况
3. **条款博弈**：分析强赎、回售、下修条款的触发距离和博弈空间
4. **投资建议**：综合以上分析，给出买入/持有/卖出建议及核心逻辑

请用简洁专业的语言进行分析，重点关注投资价值和风险点。"""

        return prompt

    def build_convertible_terms_prompt(
        self,
        cb_code: str,
        cb_name: str,
        stock_price: float,
        stock_name: str,
        call_trigger_price: float,
        put_trigger_price: float,
        conversion_price: float
    ) -> str:
        """
        构建条款博弈分析提示词

        Args:
            cb_code: 可转债代码
            cb_name: 可转债名称
            stock_price: 正股当前价格
            stock_name: 正股名称
            call_trigger_price: 强赎触发价
            put_trigger_price: 回售触发价
            conversion_price: 转股价

        Returns:
            构建好的条款博弈分析提示词
        """
        # 计算距离各条款触发价的位置
        call_distance = (stock_price / call_trigger_price - 1) * 100 if call_trigger_price > 0 else 0
        put_distance = (stock_price / put_trigger_price - 1) * 100 if put_trigger_price > 0 else 0
        conversion_distance = (stock_price / conversion_price - 1) * 100 if conversion_price > 0 else 0

        call_status = "已触发" if stock_price >= call_trigger_price else "未触发"
        put_status = "已触发" if stock_price <= put_trigger_price else "未触发"

        prompt = f"""请分析以下可转债的条款博弈情况：

【转债信息】
{cb_name} ({cb_code})

【正股信息】
{stock_name}
当前股价：{stock_price}元

【条款触发分析】
强赎条款：
  - 触发价：{call_trigger_price}元
  - 当前距离：{call_distance:.2f}%
  - 状态：{call_status}

回售条款：
  - 触发价：{put_trigger_price}元
  - 当前距离：{put_distance:.2f}%
  - 状态：{put_status}

下修条款：
  - 转股价：{conversion_price}元
  - 当前距离转股价：{conversion_distance:.2f}%

请分析：
1. 各条款的触发可能性和时间窗口
2. 发行人可能的应对策略（强赎、下修、不行使权利）
3. 投资者的应对策略和风险收益分析
4. 给出具体的操作建议"""

        return prompt

    def build_medium_term_analysis_prompt(
        self,
        industries: list,
        top_bonds: list
    ) -> str:
        """
        构建中期量化分析提示词

        Args:
            industries: 强势行业列表
            top_bonds: Top转债列表

        Returns:
            构建好的中期量化分析提示词
        """
        # 格式化行业信息
        industry_text = "\n".join([
            f"- {ind.industry_name}: 相对强弱 {ind.relative_strength:.1f}%, 60日动量 {ind.momentum_60d:.1f}%"
            for ind in industries[:5]
        ])

        # 格式化转债信息
        bond_text = "\n".join([
            f"- {b['cb_name']} ({b['cb_code']}): 行业 {b['industry']}, 溢价率 {b['premium_rate']:.1f}%, 评分 {b['score']:.1f}"
            for b in top_bonds[:10]
        ])

        prompt = f"""你是一位专业的可转债投资分析师。请基于以下中期量化筛选结果，提供专业的投资分析建议：

【识别出的强势行业】
{industry_text}

【精选转债列表】
{bond_text}

请从以下几个方面进行分析：

1. **行业趋势分析**
   - 分析各强势行业的驱动因素和可持续性
   - 识别最具投资价值的行业

2. **转债投资价值**
   - 评估精选转债的风险收益特征
   - 识别最具进攻性和防守性的标的

3. **配置建议**
   - 建议的行业配置比例
   - 建议的转债选择策略

4. **风险提示**
   - 行业轮动风险
   - 个券条款风险
   - 流动性风险

请用简洁专业的语言提供分析，重点关注实战价值。"""

        return prompt

    def build_etf_lof_gamble_prompt(
        self,
        symbol: str,
        name: str,
        fund_type: str,
        abnormal_events: List[Dict],
        current_factors: Dict,
        feature_importance: pd.DataFrame,
        current_data: Dict
    ) -> str:
        """
        构建ETF/LOF投机分析的Prompt（增强版，使用新的结构化格式）

        Args:
            symbol: 基金代码
            name: 基金名称
            fund_type: 基金类型 (LOF/ETF)
            abnormal_events: 历史异常波动事件列表
            current_factors: 当前预测因子值字典
            feature_importance: 因子重要性DataFrame
            current_data: 当前行情数据字典

        Returns:
            完整的分析Prompt字符串
        """
        # 格式化异常事件（最近5个）
        recent_events = abnormal_events[-5:] if len(abnormal_events) > 5 else abnormal_events
        events_text = "\n".join([
            f"- {e['date'].strftime('%Y-%m-%d')}: "
            f"{'📈' if e['return_pct'] > 0 else '📉'} "
            f"{e['return_pct']*100:.1f}% "
            f"(波动率: {e['volatility']*100:.1f}%, 类型: {'累计' if e.get('type') == 'cumulative' else '单日'})"
            for e in recent_events
        ]) if recent_events else "无历史异常事件"

        # 构建增强的因子表格
        factor_table = self._build_factor_table(current_factors, feature_importance, top_n=12)

        # 统计信号数量
        bullish_signals = 0
        bearish_signals = 0
        neutral_signals = 0

        if len(feature_importance) > 0:
            for _, row in feature_importance.head(10).iterrows():
                factor_name = row['feature']
                factor_value = current_factors.get(factor_name, 0)
                signal = self._get_signal(factor_name, factor_value)
                if signal == 'bullish':
                    bullish_signals += 1
                elif signal == 'bearish':
                    bearish_signals += 1
                else:
                    neutral_signals += 1

        prompt = f"""
你是一位专业的ETF/LOF短线交易分析师。请基于以下多维度数据进行分析：

## 📊 标的概况
- **代码**: {symbol}
- **名称**: {name}
- **类型**: {fund_type}
- **分析时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 当前行情
| 指标 | 数值 |
|------|------|
| 价格 | {current_data.get('price', 'N/A')} |
| 涨跌幅 | {current_data.get('change_pct', 'N/A')}% |
| 成交量 | {current_data.get('volume', 'N/A')} |
| 波动率(20日) | {current_data.get('volatility_20d', 'N/A')} |

## 🔍 历史异常波动事件（最近5个）
{events_text}

**总计**: 发现 {len(abnormal_events)} 个异常波动事件

## 🎯 当前关键因子分析（Top 10-12）
{factor_table}

**信号汇总**:
- 🟢 看涨信号: {bullish_signals}个
- 🔴 看跌信号: {bearish_signals}个
- ⚪ 中性信号: {neutral_signals}个

## 📋 分析要求

请按以下结构进行分析（使用Markdown格式）：

### 1. 📊 因子综合解读
分析当前关键因子值的综合含义：
- 哪些因子发出强烈的预警信号？
- 技术面、资金流、情绪面是否共振？
- 因子之间是否存在背离？

### 2. 📜 历史规律总结
基于历史异常波动事件：
- 该标的异常波动的触发条件是什么？
- 通常持续多久？涨幅/跌幅幅度如何？
- 是否存在周期性或季节性规律？

### 3. ⏰ 时机判断
**当前是否适合买入？请给出明确判断：**

根据信号汇总和因子分析，选择以下一种判断：
- ✅ **强烈推荐买入** - 多个因子共振显示即将出现异常上涨
- 🟢 **适合买入** - 部分因子显示有上涨机会
- ⏸️ **观望** - 信号不明确或相互矛盾，建议继续观察
- ❌ **不适合买入** - 因子显示风险较高或无明显机会

**判断依据**: 请列出支持你判断的3-5个关键因子及其当前值。

### 4. 💰 操作建议
**如果判断适合买入（强烈推荐/适合），请给出：**

| 操作项 | 建议值 | 说明 |
|--------|--------|------|
| **买入点位** | 基于当前价格{current_data.get('price', 'N/A')}给出 | 具体价格区间 |
| **止盈位** | 给出1-2个目标价格 | 第一目标、第二目标 |
| **止损位** | 风险控制价格 | 最大可接受亏损 |
| **建议仓位** | 轻仓(10-20%)/中仓(20-40%)/重仓(40-60%) | 根据信号强度 |
| **持有周期** | 预计持有天数 | 短线(1-3天)/中线(3-7天) |

**如果不适合买入（观望/不适合），请说明：**
- 当前不适合的具体原因
- 需要等待什么信号或条件
- 后续关注的重点因子和阈值

### 5. ⚠️ 风险提示
请提示本次交易的主要风险点：
- 市场系统性风险
- 个别流动性风险
- 因子失效风险
- 止损执行风险

### 6. 🎯 执行计划
给出明确的执行计划：
- **第1天**: 买入时机和价位
- **第2-N天**: 持仓管理和加仓/减仓条件
- **退出策略**: 止盈/止损的具体触发条件

---

**重要提示**:
1. 所有建议必须基于当前因子值，避免主观臆断
2. 给出具体的数值，而非模糊的建议
3. 考虑最坏情况下的风险控制措施
4. 建议应该具有可执行性，而非空泛的理论
"""

        return prompt