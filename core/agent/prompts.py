"""
Prompt Engineering Module
提示词工程模块，用于构建各种AI分析任务的提示词
"""

from typing import Dict, List, Optional, Union


class PromptBuilder:
    """提示词构建器，负责生成各种金融分析任务的提示词"""

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
2. **估值分析**：结合绝对价格、溢价率、YTM评估估值水平
3. **动能分析**：分析价格趋势、成交量变化、波动率情况
4. **条款博弈**：分析强赎、回售、下修条款的触发距离和博弈空间
5. **流动性分析**：根据成交量评估流动性
6. **投资建议**：综合以上分析，给出买入/持有/卖出建议及核心逻辑

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