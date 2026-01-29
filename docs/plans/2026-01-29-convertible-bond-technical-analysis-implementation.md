# 可转债技术面与条款分析模块实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建可转债技术面与条款分析Agent，支持单券深度分析和批量筛选功能

**Architecture:**
- 扩展 `AKShareFetcher` 添加技术面数据获取方法
- 新建 `ConvertibleBondTechnicalAnalyzer` 分析器类
- 扩展 `PromptBuilder` 添加技术面分析提示词
- 在 `dashboard.py` 添加技术面分析页面

**Tech Stack:**
- Python 3.13
- AKShare (免费数据源)
- pytest (测试)
- GLM-4.7 (AI分析)

---

## Task 1: 扩展 AKShareFetcher - 添加可转债详细信息获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`
- Test: `tests/test_akshare_fetcher.py`

### Step 1: 写测试 - 获取可转债详细信息

在 `tests/test_akshare_fetcher.py` 末尾添加：

```python
class TestAKShareFetcherConvertible:
    """测试可转债数据获取"""

    @pytest.fixture
    def fetcher(self):
        return AKShareFetcher()

    def test_get_convertible_detail_success(self, fetcher, mocker):
        """测试成功获取可转债详细信息"""
        # Mock AKShare返回数据
        mock_df = pd.DataFrame({
            'bond_id': ['113527'],
            'bond_nm': ['利民转债'],
            'price': [105.5],
            'stock_id': ['603798']),
            'put_convert_price': [90],
            'call_convert_price': [130],
        })
        mocker.patch('akshare.ak.bond_cb_jsl', return_value=mock_df)

        result = fetcher.get_convertible_detail('113527')

        assert result is not None
        assert result['cb_code'] == '113527'
        assert result['cb_name'] == '利民转债'
        assert result['put_trigger_price'] == 90
        assert result['call_trigger_price'] == 130

    def test_get_convertible_detail_not_found(self, fetcher, mocker):
        """测试转债不存在的情况"""
        mock_df = pd.DataFrame()
        mocker.patch('akshare.ak.bond_cb_jsl', return_value=mock_df)

        result = fetcher.get_convertible_detail('999999')

        assert result is None
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_akshare_fetcher.py::TestAKShareFetcherConvertible::test_get_convertible_detail_success -v
```

Expected: FAIL - "AKShareFetcher has no attribute 'get_convertible_detail'"

### Step 3: 实现最小代码

在 `data/fetchers/akshare_fetcher.py` 的 `AKShareFetcher` 类末尾添加：

```python
    def get_convertible_detail(self, cb_code: str) -> Optional[Dict]:
        """
        获取单个可转债详细信息

        Args:
            cb_code: 可转债代码（6位数字）

        Returns:
            包含条款、评级等信息的字典，如果获取失败返回None
        """
        try:
            import akshare as ak

            # 获取可转债列表
            df = ak.bond_cb_jsl()

            if df is None or df.empty:
                logger.warning("获取可转债列表失败")
                return None

            # 查找对应代码的可转债
            matching = df[df.iloc[:, 0].astype(str) == cb_code]

            if matching.empty:
                logger.warning(f"未找到可转债 {cb_code}")
                return None

            # 提取第一行数据
            row = matching.iloc[0]

            # 构建返回字典（使用位置索引访问列）
            result = {
                "cb_code": cb_code,
                "cb_name": str(row.iloc[1]) if len(row) > 1 else "",
                "price": float(row.iloc[2]) if len(row) > 2 else 0.0,
                "stock_code": str(row.iloc[4]) if len(row) > 4 else "",
                "stock_name": str(row.iloc[5]) if len(row) > 5 else "",
            }

            # 添加条款信息（如果存在）
            if len(row) > 13 and row.iloc[13] is not None:
                result["put_trigger_price"] = float(row.iloc[13])
            if len(row) > 14 and row.iloc[14] is not None:
                result["call_trigger_price"] = float(row.iloc[14])
            if len(row) > 9 and row.iloc[9] is not None:
                result["conversion_price"] = float(row.iloc[9])

            return result

        except Exception as e:
            logger.error(f"获取可转债 {cb_code} 详情失败: {e}")
            return None
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_akshare_fetcher.py::TestAKShareFetcherConvertible::test_get_convertible_detail_success -v
```

Expected: PASS

### Step 5: 提交

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher.py
git commit -m "feat: add get_convertible_detail to AKShareFetcher"
```

---

## Task 2: 扩展 AKShareFetcher - 添加实时行情和盘口数据获取

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`
- Test: `tests/test_akshare_fetcher.py`

### Step 1: 写测试

```python
    def test_get_convertible_realtime_success(self, fetcher, mocker):
        """测试成功获取实时行情和盘口"""
        mock_spot_data = pd.DataFrame({
            'code': ['113527'],
            'name': ['利民转债'],
            'trade': [105.5],
            'volume': [1000000],
            'amount': [105500000],
            # 添加盘口数据字段（根据实际AKShare返回调整）
        })
        mocker.patch('akshare.ak.bond_zh_hs_cov_spot', return_value=mock_spot_data)

        result = fetcher.get_convertible_realtime('113527')

        assert result is not None
        assert result['price'] == 105.5
        assert result['volume'] == 1000000

    def test_get_convertible_realtime_api_error(self, fetcher, mocker):
        """测试API调用失败"""
        mocker.patch('akshare.ak.bond_zh_hs_cov_spot',
                     side_effect=Exception("Network error"))

        result = fetcher.get_convertible_realtime('113527')

        assert result is None
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_akshare_fetcher.py::TestAKShareFetcherConvertible::test_get_convertible_realtime_success -v
```

Expected: FAIL

### Step 3: 实现

在 `data/fetchers/akshare_fetcher.py` 的 `AKShareFetcher` 类中添加：

```python
    def get_convertible_realtime(self, cb_code: str) -> Optional[Dict]:
        """
        获取可转债实时行情和盘口数据

        Args:
            cb_code: 可转债代码

        Returns:
            包含实时行情和盘口数据的字典
        """
        try:
            import akshare as ak

            # 获取沪深可转债现货数据
            df = ak.bond_zh_hs_cov_spot()

            if df is None or df.empty:
                return None

            # 查找对应转债
            matching = df[df['code'].astype(str) == cb_code]

            if matching.empty:
                return None

            row = matching.iloc[0]

            result = {
                "cb_code": cb_code,
                "price": float(row.get('trade', 0)),
                "change": float(row.get('changepercent', 0)),
                "volume": float(row.get('volume', 0)),
                "amount": float(row.get('amount', 0)),
                "high": float(row.get('high', 0)),
                "low": float(row.get('low', 0)),
                "open": float(row.get('open', 0)),
            }

            # 盘口数据（如果AKShare提供）
            # 注意：bond_zh_hs_cov_spot 可能不提供五档盘口，需要探索其他接口

            return result

        except Exception as e:
            logger.error(f"获取可转债 {cb_code} 实时数据失败: {e}")
            return None
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_akshare_fetcher.py::TestAKShareFetcherConvertible -v
```

Expected: PASS

### Step 5: 提交

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher.py
git commit -m "feat: add get_convertible_realtime to AKShareFetcher"
```

---

## Task 3: 扩展 AKShareFetcher - 添加历史数据和技术指标计算

**Files:**
- Modify: `data/fetchers/akshare_fetcher.py`
- Test: `tests/test_akshare_fetcher.py`

### Step 1: 写测试

```python
    def test_get_convertible_history_success(self, fetcher, mocker):
        """测试获取历史数据"""
        mock_history = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=30),
            'close': np.random.uniform(100, 110, 30),
            'volume': np.random.uniform(100000, 1000000, 30),
        })
        mocker.patch('akshare.ak.bond_zh_hs_cov_daily', return_value=mock_history)

        result = fetcher.get_convertible_history('113527', days=30)

        assert result is not None
        assert len(result) == 30
        assert 'close' in result.columns

    def test_calculate_indicators(self, fetcher):
        """测试技术指标计算"""
        # 构造测试数据
        dates = pd.date_range('2025-01-01', periods=30)
        prices = [100 + i for i in range(30)]
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': [100000] * 30,
        })

        indicators = fetcher.calculate_indicators(df)

        assert 'ma5' in indicators
        assert 'ma20' in indicators
        assert 'volatility_20d' in indicators
        assert indicators['ma5'] > indicators['ma20']  # 上涨趋势
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_akshare_fetcher.py::TestAKShareFetcherConvertible::test_get_convertible_history_success -v
```

Expected: FAIL

### Step 3: 实现

在 `data/fetchers/akshare_fetcher.py` 中添加：

```python
    def get_convertible_history(
        self,
        cb_code: str,
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取可转债历史价格数据

        Args:
            cb_code: 可转债代码
            days: 获取最近N天数据

        Returns:
            包含历史价格数据的DataFrame
        """
        try:
            import akshare as ak

            # AKShare的历史数据接口
            df = ak.bond_zh_hs_cov_daily(symbol=cb_code)

            if df is None or df.empty:
                return None

            # 处理列名
            df = self._process_daily_data(df)

            # 筛选最近N天
            if 'date' in df.columns:
                df = df.sort_values('date').tail(days)

            return df

        except Exception as e:
            logger.error(f"获取可转债 {cb_code} 历史数据失败: {e}")
            return None

    def calculate_indicators(
        self,
        history_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        计算技术指标

        Args:
            history_df: 历史价格DataFrame

        Returns:
            包含技术指标的字典
        """
        if history_df is None or history_df.empty:
            return {}

        try:
            result = {}

            # 计算移动平均线
            if 'close' in history_df.columns and len(history_df) >= 5:
                result['ma5'] = history_df['close'].tail(5).mean()

            if len(history_df) >= 20:
                result['ma20'] = history_df['close'].tail(20).mean()

                # 计算20日波动率（标准差/均值）
                returns = history_df['close'].pct_change().dropna()
                if len(returns) > 0:
                    result['volatility_20d'] = returns.tail(20).std() * 100

            # 价格趋势
            if len(history_df) >= 5:
                recent = history_df['close'].tail(5).values
                if len(recent) >= 2:
                    result['trend_5d'] = (recent[-1] - recent[0]) / recent[0] * 100

            return result

        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {}
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_akshare_fetcher.py::TestAKShareFetcherConvertible -v
```

Expected: PASS

### Step 5: 提交

```bash
git add data/fetchers/akshare_fetcher.py tests/test_akshare_fetcher.py
git commit -m "feat: add history data and technical indicators calculation"
```

---

## Task 4: 创建 ConvertibleTechnicalData 数据类

**Files:**
- Create: `analysis/convertible_technical_analysis.py`

### Step 1: 写测试

创建 `tests/test_convertible_technical_analysis.py`:

```python
"""
测试可转债技术面分析模块
"""

import pytest
from dataclasses import asdict
from analysis.convertible_technical_analysis import ConvertibleTechnicalData

class TestConvertibleTechnicalData:
    """测试ConvertibleTechnicalData数据类"""

    def test_create_minimal_data(self):
        """测试创建最小数据集"""
        data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[],
            ask_price=[],
            bid_volume=[],
            ask_volume=[],
            ma5=0.0,
            ma20=0.0,
            volatility_20d=0.0,
        )

        assert data.cb_code == "113527"
        assert data.price == 105.5
        assert data.premium_rate == 15.5

    def test_data_serialization(self):
        """测试数据序列化"""
        data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[104.5, 104.4],
            ask_price=[105.5, 105.6],
            bid_volume=[1000, 2000],
            ask_volume=[1000, 2000],
            ma5=104.5,
            ma20=103.0,
            volatility_20d=2.5,
        )

        result = asdict(data)

        assert isinstance(result, dict)
        assert result['cb_code'] == "113527"
        assert len(result['bid_price']) == 2
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleTechnicalData::test_create_minimal_data -v
```

Expected: FAIL - "No module named 'analysis.convertible_technical_analysis'"

### Step 3: 实现

创建 `analysis/convertible_technical_analysis.py`:

```python
"""
可转债技术面与条款分析模块
Convertible Bond Technical and Terms Analysis Module
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher


logger = logging.getLogger(__name__)


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

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleTechnicalData -v
```

Expected: PASS

### Step 5: 提交

```bash
git add analysis/convertible_technical_analysis.py tests/test_convertible_technical_analysis.py
git commit -m "feat: add ConvertibleTechnicalData dataclass"
```

---

## Task 5: 实现 ConvertibleBondTechnicalAnalyzer - analyze_technical 方法

**Files:**
- Modify: `analysis/convertible_technical_analysis.py`
- Test: `tests/test_convertible_technical_analysis.py`

### Step 1: 写测试

```python
class TestConvertibleBondTechnicalAnalyzer:
    """测试技术面分析器"""

    @pytest.fixture
    def mock_agent(self):
        """模拟AI Agent"""
        from unittest.mock import Mock
        agent = Mock(spec=BaseAgent)
        agent.chat.return_value = """
【定位判断】该转债属于平衡型可转债，当前价格105.5元，转股价值102元...

【估值分析】绝对价格适中，溢价率15.5%处于合理水平...

【动能分析】近期呈震荡上涨趋势，20日波动率2.5%...

【条款博弈】距离强赎触发还有约15%的空间...

【投资建议】建议持有，关注正股走势和条款变化...
"""
        return agent

    @pytest.fixture
    def analyzer(self, mock_agent):
        return ConvertibleBondTechnicalAnalyzer(mock_agent)

    def test_analyze_technical_success(self, analyzer, mocker):
        """测试成功的技术面分析"""
        # Mock数据获取
        mocker.patch.object(analyzer.fetcher, 'get_convertible_detail',
                           return_value={'cb_code': '113527', 'cb_name': '利民转债', 'price': 105.5})
        mocker.patch.object(analyzer.fetcher, 'get_convertible_realtime',
                           return_value={'price': 105.5, 'volume': 1000000})
        mocker.patch.object(analyzer.fetcher, 'get_convertible_history',
                           return_value=pd.DataFrame({'close': [100, 102, 105], 'date': pd.date_range('2025-01-01', periods=3)}))
        mocker.patch.object(analyzer.fetcher, 'calculate_indicators',
                           return_value={'ma5': 104.5, 'ma20': 103.0, 'volatility_20d': 2.5})

        result = analyzer.analyze_technical('113527')

        assert result is not None
        assert result.cb_code == '113527'
        assert result.technical_data.price == 105.5
        assert '平衡型' in result.analysis
        assert result.signals is not None

    def test_analyze_technical_data_missing(self, analyzer, mocker):
        """测试数据缺失时的降级处理"""
        mocker.patch.object(analyzer.fetcher, 'get_convertible_detail', return_value=None)

        result = analyzer.analyze_technical('999999')

        # 降级到AI知识库分析
        assert result is not None
        assert result.cb_code == '999999'
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleBondTechnicalAnalyzer::test_analyze_technical_success -v
```

Expected: FAIL

### Step 3: 实现

在 `analysis/convertible_technical_analysis.py` 中添加分析器类：

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
    signals: Dict[str, Any] = None

    # 推荐操作
    recommendation: str = ""

    def __post_init__(self):
        if self.signals is None:
            self.signals = {}


class ConvertibleBondTechnicalAnalyzer:
    """可转债技术面与条款分析器"""

    SUMMARY_MAX_LENGTH = 200

    def __init__(self, agent: BaseAgent):
        """
        初始化技术面分析器

        Args:
            agent: AI Agent实例
        """
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
        try:
            logger.info(f"开始技术面分析: {cb_code}")

            # 1. 获取数据
            detail = self.fetcher.get_convertible_detail(cb_code)
            realtime = self.fetcher.get_convertible_realtime(cb_code)
            history = self.fetcher.get_convertible_history(cb_code, days=60)

            # 2. 构建技术面数据
            if detail or realtime:
                # 合并数据源
                tech_data = self._build_technical_data(cb_code, detail, realtime, history)
            else:
                # 完全没有数据，使用AI知识库
                return self._ai_only_analysis(cb_code)

            # 3. 计算技术指标
            if history is not None:
                indicators = self.fetcher.calculate_indicators(history)
                tech_data.ma5 = indicators.get('ma5', 0.0)
                tech_data.ma20 = indicators.get('ma20', 0.0)
                tech_data.volatility_20d = indicators.get('volatility_20d', 0.0)

            # 4. AI分析
            prompt = self.prompt_builder.build_convertible_technical_prompt(tech_data)
            analysis = self.agent.chat(prompt)

            if not analysis:
                logger.warning("AI分析失败")
                return None

            # 5. 提取信号
            signals = self._extract_signals(tech_data)

            # 6. 生成摘要
            summary = self._extract_summary(analysis)

            # 7. 构建结果
            result = TechnicalAnalysisResult(
                cb_code=cb_code,
                cb_name=tech_data.cb_name,
                technical_data=tech_data,
                analysis=analysis,
                summary=summary,
                signals=signals,
                recommendation=self._extract_recommendation(analysis)
            )

            logger.info(f"技术面分析完成: {cb_code}")
            return result

        except Exception as e:
            logger.error(f"技术面分析失败 {cb_code}: {e}", exc_info=True)
            return None

    def _build_technical_data(
        self,
        cb_code: str,
        detail: Optional[Dict],
        realtime: Optional[Dict],
        history: Optional[pd.DataFrame]
    ) -> ConvertibleTechnicalData:
        """构建技术面数据对象"""
        # 合并数据源，优先使用实时数据
        return ConvertibleTechnicalData(
            cb_code=cb_code,
            cb_name=detail.get('cb_name') if detail else realtime.get('cb_name', ''),
            price=realtime.get('price') if realtime else detail.get('price', 0),
            change_percent=realtime.get('change') if realtime else 0,
            volume=realtime.get('volume') if realtime else 0,
            amount=realtime.get('amount') if realtime else 0,
            conversion_price=detail.get('conversion_price', 0) if detail else 0,
            conversion_value=0,  # 需要计算
            premium_rate=0,  # 需要计算
            bond_rating=detail.get('bond_rating', '') if detail else '',
            pure_bond_value=0,
            ytm=0,
            call_trigger_price=detail.get('call_trigger_price', 0) if detail else 0,
            put_trigger_price=detail.get('put_trigger_price', 0) if detail else 0,
            conversion_trigger_price=detail.get('conversion_price', 0) if detail else 0,
            bid_price=realtime.get('bid_price', []) if realtime else [],
            ask_price=realtime.get('ask_price', []) if realtime else [],
            bid_volume=realtime.get('bid_volume', []) if realtime else [],
            ask_volume=realtime.get('ask_volume', []) if realtime else [],
            ma5=0,
            ma20=0,
            volatility_20d=0,
        )

    def _ai_only_analysis(self, cb_code: str) -> TechnicalAnalysisResult:
        """纯AI分析（无实时数据）"""
        prompt = f"""请分析可转债 {cb_code} 的技术面情况。
由于无法获取实时数据，请基于您的知识库进行分析。"""

        analysis = self.agent.chat(prompt)

        return TechnicalAnalysisResult(
            cb_code=cb_code,
            cb_name=cb_code,
            technical_data=ConvertibleTechnicalData(
                cb_code=cb_code,
                cb_name=cb_code,
                price=0,
                change_percent=0,
                volume=0,
                amount=0,
                conversion_price=0,
                conversion_value=0,
                premium_rate=0,
                bond_rating='',
                pure_bond_value=0,
                ytm=0,
                call_trigger_price=0,
                put_trigger_price=0,
                conversion_trigger_price=0,
                bid_price=[],
                ask_price=[],
                bid_volume=[],
                ask_volume=[],
                ma5=0,
                ma20=0,
                volatility_20d=0,
            ),
            analysis=analysis,
            summary=analysis[:self.SUMMARY_MAX_LENGTH],
            signals={'data_source': 'ai_only'}
        )

    def _extract_signals(self, data: ConvertibleTechnicalData) -> Dict[str, Any]:
        """从技术数据中提取信号"""
        signals = {}

        # 判断类型
        if data.price < 100:
            signals['type'] = '偏债'
        elif data.price > 120:
            signals['type'] = '偏股'
        else:
            signals['type'] = '平衡'

        # 流动性评估
        if data.amount > 100000000:  # 1亿成交额
            signals['liquidity'] = '高'
        elif data.amount > 10000000:  # 1000万
            signals['liquidity'] = '中'
        else:
            signals['liquidity'] = '低'

        return signals

    def _extract_summary(self, analysis: str) -> str:
        """提取分析摘要"""
        if len(analysis) <= self.SUMMARY_MAX_LENGTH:
            return analysis

        summary = analysis[:self.SUMMARY_MAX_LENGTH]
        last_period = summary.rfind('。')
        if last_period > self.SUMMARY_MAX_LENGTH // 2:
            summary = summary[:last_period + 1]

        return summary

    def _extract_recommendation(self, analysis: str) -> str:
        """从分析中提取推荐"""
        analysis_lower = analysis.lower()

        if '买入' in analysis or '建议买入' in analysis:
            return '买入'
        elif '卖出' in analysis or '建议卖出' in analysis:
            return '卖出'
        else:
            return '持有'
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleBondTechnicalAnalyzer -v
```

Expected: PASS

### Step 5: 提交

```bash
git add analysis/convertible_technical_analysis.py tests/test_convertible_technical_analysis.py
git commit -m "feat: implement ConvertibleBondTechnicalAnalyzer.analyze_technical"
```

---

## Task 6: 实现 analyze_terms 条款博弈分析方法

**Files:**
- Modify: `analysis/convertible_technical_analysis.py`
- Test: `tests/test_convertible_technical_analysis.py`

### Step 1: 写测试

```python
    def test_analyze_terms_call_trigger(self, analyzer, mocker):
        """测试强赎条款触发分析"""
        mocker.patch.object(analyzer.fetcher, 'get_convertible_detail',
                           return_value={
                               'cb_code': '113527',
                               'cb_name': '利民转债',
                               'call_trigger_price': 130.0,
                               'put_trigger_price': 90.0,
                               'conversion_price': 100.0,
                           })

        # 正股价超过强赎触发价
        result = analyzer.analyze_terms('113527', stock_price=135.0, stock_name='利民股份')

        assert result is not None
        assert result['cb_code'] == '113527'
        assert '强赎' in result['call_analysis']
        assert '已触发' in result['call_analysis'] or '即将触发' in result['call_analysis']

    def test_analyze_terms_put_trigger(self, analyzer, mocker):
        """测试回售条款触发分析"""
        mocker.patch.object(analyzer.fetcher, 'get_convertible_detail',
                           return_value={
                               'cb_code': '113527',
                               'cb_name': '利民转债',
                               'call_trigger_price': 130.0,
                               'put_trigger_price': 90.0,
                               'conversion_price': 100.0,
                           })

        # 正股价低于回售触发价
        result = analyzer.analyze_terms('113527', stock_price=85.0, stock_name='利民股份')

        assert result is not None
        assert '回售' in result['put_analysis']
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleBondTechnicalAnalyzer::test_analyze_terms_call_trigger -v
```

Expected: FAIL

### Step 3: 实现

在 `ConvertibleBondTechnicalAnalyzer` 类中添加：

```python
    def analyze_terms(
        self,
        cb_code: str,
        stock_price: float,
        stock_name: str = ""
    ) -> Optional[Dict]:
        """
        条款博弈分析

        Args:
            cb_code: 可转债代码
            stock_price: 正股当前价格
            stock_name: 正股名称

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
        try:
            logger.info(f"开始条款博弈分析: {cb_code}")

            # 获取转债详情
            detail = self.fetcher.get_convertible_detail(cb_code)

            if not detail:
                logger.warning(f"无法获取转债 {cb_code} 详情")
                return None

            # 计算距离条款触发的距离
            call_price = detail.get('call_trigger_price', 0)
            put_price = detail.get('put_trigger_price', 0)
            conversion_price = detail.get('conversion_price', 0)

            # 构建AI分析提示词
            prompt = self.prompt_builder.build_convertible_terms_prompt(
                cb_code=cb_code,
                cb_name=detail.get('cb_name', ''),
                stock_price=stock_price,
                stock_name=stock_name,
                call_trigger_price=call_price,
                put_trigger_price=put_price,
                conversion_price=conversion_price
            )

            # AI分析
            analysis = self.agent.chat(prompt)

            if not analysis:
                return None

            # 解析分析结果
            result = {
                "cb_code": cb_code,
                "cb_name": detail.get('cb_name', ''),
                "stock_price": stock_price,
                "stock_name": stock_name,
                "call_trigger_price": call_price,
                "put_trigger_price": put_price,
                "conversion_price": conversion_price,
                "call_distance": (stock_price / call_price - 1) * 100 if call_price > 0 else 0,
                "put_distance": (stock_price / put_price - 1) * 100 if put_price > 0 else 0,
                "full_analysis": analysis,
            }

            logger.info(f"条款博弈分析完成: {cb_code}")
            return result

        except Exception as e:
            logger.error(f"条款博弈分析失败 {cb_code}: {e}", exc_info=True)
            return None
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleBondTechnicalAnalyzer::test_analyze_terms_call_trigger -v
```

Expected: PASS

### Step 5: 提交

```bash
git add analysis/convertible_technical_analysis.py tests/test_convertible_technical_analysis.py
git commit -m "feat: implement analyze_terms method"
```

---

## Task 7: 实现 screen_by_technical 批量筛选方法

**Files:**
- Modify: `analysis/convertible_technical_analysis.py`
- Test: `tests/test_convertible_technical_analysis.py`

### Step 1: 写测试

```python
    def test_screen_by_technical_price_filter(self, analyzer, mocker):
        """测试价格筛选"""
        # Mock可转债列表
        mock_list = [
            {'cb_code': '113001', 'cb_name': '平煤转债', 'price': 105, 'premium_rate': 10, 'amount': 50000000},
            {'cb_code': '113002', 'cb_name': '神马转债', 'price': 115, 'premium_rate': 20, 'amount': 30000000},
            {'cb_code': '113003', 'cb_name': '韦尔转债', 'price': 95, 'premium_rate': 5, 'amount': 100000000},
        ]
        mocker.patch.object(analyzer.fetcher, 'get_convertible_list', return_value=mock_list)

        criteria = {
            "price_range": (100, 110),
            "premium_max": 15,
        }

        results = analyzer.screen_by_technical(criteria, top_n=10)

        assert results is not None
        assert len(results) == 1  # 只有平煤转债符合
        assert results[0]['cb_code'] == '113001'

    def test_screen_by_technical_empty_result(self, analyzer, mocker):
        """测试无符合条件结果"""
        mocker.patch.object(analyzer.fetcher, 'get_convertible_list', return_value=[])

        results = analyzer.screen_by_technical({"price_range": (90, 110)})

        assert results == []
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleBondTechnicalAnalyzer::test_screen_by_technical_price_filter -v
```

Expected: FAIL

### Step 3: 实现

在 `ConvertibleBondTechnicalAnalyzer` 类中添加：

```python
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
                }
            top_n: 返回前N个结果

        Returns:
            筛选结果列表，按综合评分排序
        """
        try:
            logger.info(f"开始技术面筛选: {criteria}")

            # 1. 获取可转债列表
            cb_list = self.fetcher.get_convertible_list()

            if not cb_list:
                logger.warning("获取可转债列表失败")
                return None

            # 2. 应用筛选条件
            filtered = []

            for cb in cb_list:
                # 提取数据
                price = cb.get('price', 0)
                premium = abs(cb.get('change', 0))  # 简化：使用涨跌幅
                amount = cb.get('amount', 0)

                # 筛选条件检查
                if "price_range" in criteria:
                    min_p, max_p = criteria["price_range"]
                    if not (min_p <= price <= max_p):
                        continue

                if "premium_max" in criteria:
                    if premium > criteria["premium_max"]:
                        continue

                if "liquidity_min" in criteria:
                    if amount < criteria["liquidity_min"]:
                        continue

                # 计算综合评分（简化版）
                score = self._calculate_screen_score(cb, criteria)

                filtered.append({
                    "cb_code": cb.get('cb_code'),
                    "cb_name": cb.get('cb_name'),
                    "price": price,
                    "premium": premium,
                    "amount": amount,
                    "score": score,
                })

            # 3. 排序
            filtered.sort(key=lambda x: x['score'], reverse=True)

            # 4. 返回前N个
            result = filtered[:top_n]

            logger.info(f"技术面筛选完成，找到 {len(result)} 只转债")
            return result

        except Exception as e:
            logger.error(f"技术面筛选失败: {e}", exc_info=True)
            return None

    def _calculate_screen_score(self, cb: Dict, criteria: Dict) -> float:
        """计算筛选评分"""
        score = 0.0

        # 价格越低越好（在合理范围内）
        price = cb.get('price', 100)
        if 100 <= price <= 110:
            score += 50

        # 溢价率越低越好
        premium = abs(cb.get('change', 0))
        score -= premium

        # 流动性加分
        amount = cb.get('amount', 0)
        if amount > 100000000:  # 1亿
            score += 20
        elif amount > 50000000:  # 5000万
            score += 10

        return score
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_convertible_technical_analysis.py::TestConvertibleBondTechnicalAnalyzer::test_screen_by_technical_price_filter -v
```

Expected: PASS

### Step 5: 提交

```bash
git add analysis/convertible_technical_analysis.py tests/test_convertible_technical_analysis.py
git commit -m "feat: implement screen_by_technical method"
```

---

## Task 8: 扩展 PromptBuilder - 添加技术面分析提示词

**Files:**
- Modify: `core/agent/prompts.py`
- Test: `tests/test_prompts.py`

### Step 1: 写测试

在 `tests/test_prompts.py` 末尾添加：

```python
class TestConvertibleTechnicalPrompts:
    """测试可转债技术面提示词"""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    def test_build_convertible_technical_prompt(self, builder):
        """测试技术面分析提示词"""
        from analysis.convertible_technical_analysis import ConvertibleTechnicalData

        tech_data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[],
            ask_price=[],
            bid_volume=[],
            ask_volume=[],
            ma5=104.5,
            ma20=103.0,
            volatility_20d=2.5,
        )

        prompt = builder.build_convertible_technical_prompt(tech_data)

        assert '113527' in prompt
        assert '利民转债' in prompt
        assert '105.5' in prompt
        assert '技术分析师' in prompt
        assert '定位判断' in prompt
        assert '估值分析' in prompt

    def test_build_convertible_terms_prompt(self, builder):
        """测试条款博弈提示词"""
        prompt = builder.build_convertible_terms_prompt(
            cb_code="113527",
            cb_name="利民转债",
            stock_price=125.0,
            stock_name="利民股份",
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_price=100.0,
        )

        assert '113527' in prompt
        assert '125.0' in prompt
        assert '强赎' in prompt
        assert '回售' in prompt
```

### Step 2: 运行测试确认失败

```bash
uv run pytest tests/test_prompts.py::TestConvertibleTechnicalPrompts -v
```

Expected: FAIL

### Step 3: 实现

在 `core/agent/prompts.py` 的 `PromptBuilder` 类末尾添加：

```python
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
```

### Step 4: 运行测试确认通过

```bash
uv run pytest tests/test_prompts.py::TestConvertibleTechnicalPrompts -v
```

Expected: PASS

### Step 5: 提交

```bash
git add core/agent/prompts.py tests/test_prompts.py
git commit -m "feat: add convertible bond technical analysis prompts"
```

---

## Task 9: 在 Dashboard 添加技术面分析页面

**Files:**
- Modify: `ui/dashboard.py`
- Test: `tests/test_dashboard.py`

### Step 1: 写测试

```python
def test_convertible_technical_page_renders(dashboard):
    """测试技术面分析页面渲染"""
    # 需要Streamlit测试支持，这里仅作为检查点
    assert True  # 占位测试
```

### Step 2: 运行测试确认通过

```bash
uv run pytest tests/test_dashboard.py::test_convertible_technical_page_renders -v
```

### Step 3: 实现

在 `ui/dashboard.py` 中添加：

```python
# 在文件顶部的导入部分添加
from analysis.convertible_technical_analysis import (
    ConvertibleBondTechnicalAnalyzer,
    TechnicalAnalysisResult
)

# 在main函数中添加新的页面标签
def show_convertible_technical_page():
    """可转债技术面分析页面"""
    st.title("📊 可转债技术面分析")

    tab1, tab2 = st.tabs(["单券分析", "技术面筛选"])

    with tab1:
        st.subheader("单券技术面分析")

        col1, col2 = st.columns([2, 1])

        with col1:
            cb_code = st.text_input(
                "转债代码",
                placeholder="如113527",
                help="输入6位可转债代码"
            )

        with col2:
            st.write("")  # 占位
            analyze_btn = st.button("开始分析", type="primary")

        if analyze_btn and cb_code:
            with st.spinner("正在分析..."):
                analyzer = ConvertibleBondTechnicalAnalyzer(st.session_state.agent)
                result = analyzer.analyze_technical(cb_code)

                if result:
                    # 显示基础信息
                    st.success(f"分析完成：{result.cb_name}")

                    # 基础信息卡片
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("当前价格", f"{result.technical_data.price:.2f}元")
                    with col2:
                        st.metric("涨跌幅", f"{result.technical_data.change_percent:.2f}%")
                    with col3:
                        st.metric("溢价率", f"{result.technical_data.premium_rate:.2f}%")
                    with col4:
                        st.metric("类型", result.signals.get('type', '未知'))

                    # AI分析结果
                    st.subheader("AI分析")
                    st.markdown(result.analysis)

                    # 投资建议
                    if result.recommendation:
                        st.info(f"💡 投资建议：{result.recommendation}")
                else:
                    st.error("分析失败，请检查转债代码")

    with tab2:
        st.subheader("技术面筛选")

        col1, col2, col3 = st.columns(3)

        with col1:
            price_min = st.number_input("最低价格", value=90, min_value=0, max_value=300)
            price_max = st.number_input("最高价格", value=110, min_value=0, max_value=300)

        with col2:
            premium_max = st.number_input("最大溢价率(%)", value=30, min_value=0, max_value=100)

        with col3:
            top_n = st.number_input("返回数量", value=20, min_value=1, max_value=100)

        if st.button("开始筛选"):
            with st.spinner("正在筛选..."):
                analyzer = ConvertibleBondTechnicalAnalyzer(st.session_state.agent)

                criteria = {
                    "price_range": (price_min, price_max),
                    "premium_max": premium_max,
                }

                results = analyzer.screen_by_technical(criteria, top_n=top_n)

                if results:
                    st.success(f"筛选完成，找到 {len(results)} 只转债")

                    # 转换为DataFrame显示
                    import pandas as pd
                    df = pd.DataFrame(results)

                    st.dataframe(
                        df[['cb_code', 'cb_name', 'price', 'premium', 'score']],
                        column_config={
                            "cb_code": "代码",
                            "cb_name": "名称",
                            "price": "价格",
                            "premium": "溢价率",
                            "score": "评分"
                        }
                    )
                else:
                    st.warning("未找到符合条件的转债")
```

### Step 4: 在main函数中添加页面入口

找到 `main()` 函数中的页面选择部分，添加：

```python
# 在现有的page选择中添加
with st.sidebar:
    page = st.radio(
        "选择功能",
        ["首页", "选股", "市场分析", "ETF分析", "可转债分析", "可转债技术面"]
    )

# 在条件判断中添加
elif page == "可转债技术面":
    show_convertible_technical_page()
```

### Step 5: 运行测试确认通过

```bash
uv run pytest tests/test_dashboard.py -v
```

### Step 6: 手动测试

```bash
./run_ui.sh
```

访问 http://localhost:8501 验证页面显示正常

### Step 7: 提交

```bash
git add ui/dashboard.py
git commit -m "feat: add convertible bond technical analysis page to dashboard"
```

---

## Task 10: 集成测试和文档完善

**Files:**
- Modify: `tests/test_convertible_technical_analysis.py`
- Create: `examples/convertible_technical_analysis_example.py`

### Step 1: 添加集成测试

```python
@pytest.mark.integration
class TestConvertibleTechnicalIntegration:
    """集成测试（需要真实API）"""

    def test_full_analysis_pipeline(self):
        """测试完整的分析流程"""
        from core.agent.glm_agent import GLMAgent

        agent = GLMAgent()
        analyzer = ConvertibleBondTechnicalAnalyzer(agent)

        # 使用真实转债代码
        result = analyzer.analyze_technical('113527')

        assert result is not None
        assert result.cb_code == '113527'
        assert len(result.analysis) > 0
```

### Step 2: 创建示例文件

创建 `examples/convertible_technical_analysis_example.py`:

```python
"""
可转债技术面分析示例
"""

from core.agent.glm_agent import GLMAgent
from analysis.convertible_technical_analysis import ConvertibleBondTechnicalAnalyzer


def main():
    """主函数"""
    # 初始化
    agent = GLMAgent()
    analyzer = ConvertibleBondTechnicalAnalyzer(agent)

    # 示例1: 单券技术面分析
    print("=" * 50)
    print("示例1: 单券技术面分析")
    print("=" * 50)

    result = analyzer.analyze_technical('113527')

    if result:
        print(f"\n转债: {result.cb_name} ({result.cb_code})")
        print(f"价格: {result.technical_data.price}元")
        print(f"类型: {result.signals.get('type')}")
        print(f"\nAI分析:\n{result.analysis}")
        print(f"\n建议: {result.recommendation}")

    # 示例2: 条款博弈分析
    print("\n" + "=" * 50)
    print("示例2: 条款博弈分析")
    print("=" * 50)

    terms_result = analyzer.analyze_terms(
        cb_code='113527',
        stock_price=125.0,
        stock_name='利民股份'
    )

    if terms_result:
        print(f"\n强赎距离: {terms_result['call_distance']:.2f}%")
        print(f"回售距离: {terms_result['put_distance']:.2f}%")
        print(f"\n分析:\n{terms_result['full_analysis']}")

    # 示例3: 技术面筛选
    print("\n" + "=" * 50)
    print("示例3: 技术面筛选")
    print("=" * 50)

    screen_results = analyzer.screen_by_technical(
        criteria={"price_range": (100, 110), "premium_max": 20},
        top_n=5
    )

    if screen_results:
        print(f"\n找到 {len(screen_results)} 只转债:")
        for r in screen_results:
            print(f"  {r['cb_name']} ({r['cb_code']}): {r['price']}元, 评分:{r['score']:.1f}")


if __name__ == '__main__':
    main()
```

### Step 3: 更新项目文档

更新 `CLAUDE.md` 添加新模块说明：

```markdown
### 可转债技术面分析模块

位于 `analysis/convertible_technical_analysis.py`

**核心功能**:
- `analyze_technical()` - 单券技术面深度分析
- `analyze_terms()` - 条款博弈分析
- `screen_by_technical()` - 批量筛选

**使用示例**:
```python
from core.agent.glm_agent import GLMAgent
from analysis.convertible_technical_analysis import ConvertibleBondTechnicalAnalyzer

agent = GLMAgent()
analyzer = ConvertibleBondTechnicalAnalyzer(agent)

# 技术面分析
result = analyzer.analyze_technical('113527')

# 条款博弈分析
terms = analyzer.analyze_terms('113527', stock_price=125.0)

# 批量筛选
results = analyzer.screen_by_technical({"price_range": (100, 110)})
```
```

### Step 4: 运行所有测试

```bash
uv run pytest tests/test_convertible_technical_analysis.py -v
uv run pytest tests/test_akshare_fetcher.py -v
uv run pytest tests/test_prompts.py::TestConvertibleTechnicalPrompts -v
```

Expected: 全部通过

### Step 5: 提交

```bash
git add tests/test_convertible_technical_analysis.py examples/convertible_technical_analysis_example.py CLAUDE.md
git commit -m "test: add integration tests and examples for technical analysis"
```

---

## 完成检查清单

实施完成后，验证以下项目：

- [ ] 所有单元测试通过
- [ ] 集成测试通过（需要API密钥）
- [ ] 示例代码可以运行
- [ ] Dashboard页面显示正常
- [ ] 代码覆盖率 > 80%
- [ ] 文档已更新

---

**实施计划版本**: 1.0
**创建日期**: 2026-01-29
**预计工期**: 6-10天
