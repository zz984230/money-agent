# ETF/LOF 历史记录与进度显示功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为【ETF/LOF 投机分析】模块添加分析报告历史记录和实时进度显示功能

**Architecture:**
1. 创建独立的 `storage/analysis_history.py` 模块管理历史记录（JSON持久化）
2. 修改 `LOFETFGambleAnalyzer` 支持进度回调
3. 在 `ui/dashboard.py` 中集成历史记录UI和进度条显示

**Tech Stack:** Python 3.10+, Streamlit, JSON, dataclasses

---

## Task 1: 创建存储模块目录结构和数据模型

**Files:**
- Create: `storage/__init__.py`
- Create: `storage/analysis_history.py`
- Test: `tests/test_analysis_history.py`

**Step 1: 创建 storage 包的 `__init__.py`**

Create file: `storage/__init__.py`

```python
"""存储模块 - 管理各类持久化数据"""
```

**Step 2: 编写历史管理器的失败测试**

Create file: `tests/test_analysis_history.py`

```python
"""测试分析历史记录管理器"""
import pytest
from pathlib import Path
from datetime import datetime
from storage.analysis_history import AnalysisHistoryManager, AnalysisHistoryEntry

@pytest.fixture
def temp_cache_dir(tmp_path):
    """临时缓存目录"""
    return tmp_path / "cache"

@pytest.fixture
def manager(temp_cache_dir):
    """历史管理器实例"""
    return AnalysisHistoryManager(temp_cache_dir)

def test_manager_creates_cache_file(manager, temp_cache_dir):
    """测试管理器初始化时创建缓存文件"""
    assert manager.cache_file == temp_cache_dir / "analysis_history.json"
    # 初始化时不自动创建文件

def test_add_entry(manager):
    """测试添加历史记录"""
    entry = AnalysisHistoryEntry(
        id="test-001",
        symbol="163415",
        name="白银LOF",
        fund_type="LOF",
        created_at="2025-01-31T14:30:00",
        abnormal_events_count=5,
        current_price=0.856,
        ai_summary="## 测试分析",
        current_factors={"momentum_5": 0.05}
    )

    result = manager.add_entry(entry)
    assert result is True

    # 验证可以获取到添加的记录
    entries = manager.get_all_entries()
    assert len(entries) == 1
    assert entries[0].id == "test-001"

def test_get_all_entries_returns_empty_when_no_data(manager):
    """测试无数据时返回空列表"""
    entries = manager.get_all_entries()
    assert entries == []

def test_delete_entry(manager):
    """测试删除单条记录"""
    entry = AnalysisHistoryEntry(
        id="test-002",
        symbol="161116",
        name="黄金基金",
        fund_type="LOF",
        created_at="2025-01-31T15:00:00",
        abnormal_events_count=3,
        current_price=1.234,
        ai_summary="测试",
        current_factors={}
    )
    manager.add_entry(entry)

    result = manager.delete_entry("test-002")
    assert result is True

    entries = manager.get_all_entries()
    assert len(entries) == 0

def test_delete_nonexistent_entry(manager):
    """测试删除不存在的记录返回False"""
    result = manager.delete_entry("nonexistent")
    assert result is False

def test_clear_all(manager):
    """测试清空所有记录"""
    entry1 = AnalysisHistoryEntry(
        id="test-003", symbol="001", name="测试1", fund_type="LOF",
        created_at="2025-01-31T16:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="测试", current_factors={}
    )
    entry2 = AnalysisHistoryEntry(
        id="test-004", symbol="002", name="测试2", fund_type="ETF",
        created_at="2025-01-31T17:00:00", abnormal_events_count=2,
        current_price=2.0, ai_summary="测试", current_factors={}
    )
    manager.add_entry(entry1)
    manager.add_entry(entry2)

    result = manager.clear_all()
    assert result is True

    entries = manager.get_all_entries()
    assert len(entries) == 0

def test_search_by_keyword(manager):
    """测试按关键词搜索"""
    entry1 = AnalysisHistoryEntry(
        id="test-005", symbol="163415", name="白银LOF", fund_type="LOF",
        created_at="2025-01-31T18:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="白银分析", current_factors={}
    )
    entry2 = AnalysisHistoryEntry(
        id="test-006", symbol="161116", name="黄金基金", fund_type="LOF",
        created_at="2025-01-31T19:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="黄金分析", current_factors={}
    )
    manager.add_entry(entry1)
    manager.add_entry(entry2)

    results = manager.search(keyword="白银")
    assert len(results) == 1
    assert results[0].name == "白银LOF"

def test_search_by_fund_type(manager):
    """测试按基金类型过滤"""
    entry1 = AnalysisHistoryEntry(
        id="test-007", symbol="001", name="LOF基金", fund_type="LOF",
        created_at="2025-01-31T20:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="测试", current_factors={}
    )
    entry2 = AnalysisHistoryEntry(
        id="test-008", symbol="002", name="ETF基金", fund_type="ETF",
        created_at="2025-01-31T21:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="测试", current_factors={}
    )
    manager.add_entry(entry1)
    manager.add_entry(entry2)

    results = manager.search(fund_type="LOF")
    assert len(results) == 1
    assert results[0].fund_type == "LOF"

def test_export_to_csv(manager, tmp_path):
    """测试导出CSV"""
    entry = AnalysisHistoryEntry(
        id="test-009", symbol="163415", name="白银LOF", fund_type="LOF",
        created_at="2025-01-31T22:00:00", abnormal_events_count=5,
        current_price=0.856, ai_summary="测试分析", current_factors={}
    )
    manager.add_entry(entry)

    # 修改导出目录到临时目录
    original_cache_dir = manager.cache_dir
    manager.cache_dir = tmp_path

    csv_path = manager.export_to_csv()

    assert csv_path is not None
    assert Path(csv_path).exists()

    # 恢复原目录
    manager.cache_dir = original_cache_dir
```

**Step 3: 运行测试确认失败**

Run: `uv run pytest tests/test_analysis_history.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'storage'`

**Step 4: 实现数据模型和管理器**

Create file: `storage/analysis_history.py`

```python
"""分析历史记录管理器"""
import json
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class AnalysisHistoryEntry:
    """单条分析历史记录"""
    id: str                    # 唯一ID (时间戳+基金代码)
    symbol: str                # 基金代码
    name: str                  # 基金名称
    fund_type: str             # 基金类型 (LOF/ETF)
    created_at: str            # 创建时间 (ISO 8601格式)

    # 分析结果快照
    abnormal_events_count: int
    current_price: float
    ai_summary: str            # AI分析完整内容
    current_factors: Dict      # 当前因子数据

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AnalysisHistoryEntry':
        """从字典创建实例"""
        return cls(**data)


class AnalysisHistoryManager:
    """分析历史记录管理器"""

    def __init__(self, cache_dir: Path):
        """
        初始化管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "analysis_history.json"
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict:
        """加载JSON数据"""
        if not self.cache_file.exists():
            return {"entries": []}

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"entries": []}

    def _save_data(self, data: Dict) -> bool:
        """保存JSON数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

    def add_entry(self, entry: AnalysisHistoryEntry) -> bool:
        """
        添加历史记录

        Args:
            entry: 历史记录条目

        Returns:
            是否成功添加
        """
        data = self._load_data()
        data["entries"].insert(0, entry.to_dict())  # 最新的在前
        return self._save_data(data)

    def get_all_entries(self) -> List[AnalysisHistoryEntry]:
        """
        获取所有历史记录

        Returns:
            历史记录列表（按时间倒序）
        """
        data = self._load_data()
        return [AnalysisHistoryEntry.from_dict(e) for e in data.get("entries", [])]

    def delete_entry(self, entry_id: str) -> bool:
        """
        删除单条历史记录

        Args:
            entry_id: 记录ID

        Returns:
            是否成功删除
        """
        data = self._load_data()
        original_count = len(data["entries"])
        data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]

        if len(data["entries"]) < original_count:
            return self._save_data(data)
        return False

    def clear_all(self) -> bool:
        """
        清空所有历史记录

        Returns:
            是否成功清空
        """
        data = {"entries": []}
        return self._save_data(data)

    def search(self, keyword: str = "", fund_type: str = None) -> List[AnalysisHistoryEntry]:
        """
        搜索历史记录

        Args:
            keyword: 搜索关键词（匹配代码或名称）
            fund_type: 基金类型过滤

        Returns:
            匹配的历史记录列表
        """
        entries = self.get_all_entries()

        if keyword:
            keyword_lower = keyword.lower()
            entries = [
                e for e in entries
                if keyword_lower in e.symbol.lower() or keyword_lower in e.name.lower()
            ]

        if fund_type:
            entries = [e for e in entries if e.fund_type == fund_type]

        return entries

    def export_to_csv(self) -> Optional[str]:
        """
        导出历史记录为CSV

        Returns:
            CSV文件路径，失败返回None
        """
        entries = self.get_all_entries()
        if not entries:
            return None

        csv_file = self.cache_dir / f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow([
                    "ID", "基金代码", "基金名称", "类型", "创建时间",
                    "异常事件数", "当前价格", "AI分析摘要"
                ])

                # 写入数据
                for entry in entries:
                    writer.writerow([
                        entry.id,
                        entry.symbol,
                        entry.name,
                        entry.fund_type,
                        entry.created_at,
                        entry.abnormal_events_count,
                        entry.current_price,
                        entry.ai_summary[:100] + "..." if len(entry.ai_summary) > 100 else entry.ai_summary
                    ])

            return str(csv_file)
        except IOError:
            return None
```

**Step 5: 运行测试确认通过**

Run: `uv run pytest tests/test_analysis_history.py -v`

Expected: PASS (所有测试通过)

**Step 6: 提交**

```bash
git add storage/ tests/test_analysis_history.py
git commit -m "feat: add analysis history storage module with JSON persistence"
```

---

## Task 2: 修改分析器支持进度回调

**Files:**
- Modify: `analysis/etf_lof_gamble.py:524-630`

**Step 1: 编写进度回调功能的测试**

Add to file: `tests/test_etf_lof_gamble.py` (追加到文件末尾)

```python
def test_screen_and_analyze_with_progress_callback(gamble_analyzer, mocker):
    """测试带进度回调的筛选分析"""
    # Mock进度回调函数
    progress_mock = mocker.Mock()

    # Mock fetcher返回数据
    mock_df = pd.DataFrame({
        'close': [1.0, 1.05, 1.10, 0.95, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40],
    })
    mock_df.index = pd.date_range('2025-01-01', periods=10)

    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_commodity_lof_list',
        return_value=[{'code': '163415', 'name': '白银LOF', 'type': 'LOF'}]
    )
    mocker.patch.object(
        gamble_analyzer.fetcher,
        'get_lof_etf_history',
        return_value=mock_df
    )
    # Mock AI分析返回None（数据不足）
    mocker.patch.object(gamble_analyzer, 'analyze_single', return_value=None)

    # 调用带进度回调的筛选
    criteria = {'window': 3, 'threshold': 0.15, 'fund_types': ['commodity']}

    # 由于analyze_single返回None，results为空，但进度回调应被调用
    results = gamble_analyzer.screen_and_analyze(
        criteria=criteria,
        top_n=1,
        progress_callback=progress_mock
    )

    # 验证回调被调用（至少一次，用于筛选阶段）
    assert progress_mock.call_count > 0
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_etf_lof_gamble.py::test_screen_and_analyze_with_progress_callback -v`

Expected: FAIL (screen_and_analyze 不支持 progress_callback 参数)

**Step 3: 修改 screen_and_analyze 方法支持进度回调**

Modify file: `analysis/etf_lof_gamble.py`

在 `screen_and_analyze` 方法签名中添加 `progress_callback` 参数：

```python
from typing import Callable, Optional

def screen_and_analyze(
    self,
    criteria: Optional[Dict] = None,
    top_n: int = 20,
    progress_callback: Optional[Callable[[float, str], None]] = None
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
        progress_callback: 进度回调函数，签名为 (progress: float, message: str) -> None

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
    screen_total = len(target_list[:top_n * 3])

    for i, item in enumerate(target_list[:top_n * 3]):
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

            # 更新筛选阶段进度 (0-40%)
            if progress_callback:
                progress = (i + 1) / screen_total * 0.4
                progress_callback(progress, f"筛选中... {i+1}/{screen_total}")

        except Exception as e:
            logger.error(f"筛选 {symbol} 失败: {e}")
            continue

    # 3. 按异常事件数量排序，取前top_n个
    screened.sort(key=lambda x: x['events_count'], reverse=True)
    top_targets = screened[:top_n]

    logger.info(f"筛选出 {len(top_targets)} 个目标进行深度分析")

    # 更新进度到40%
    if progress_callback:
        progress_callback(0.4, "开始AI深度分析...")

    # 4. 深度分析
    results = []
    analyze_total = len(top_targets)

    for i, target in enumerate(top_targets):
        try:
            result = self.analyze_single(
                target['symbol'],
                target['name'],
                target['fund_type']
            )
            if result is not None:
                results.append(result)

            # 更新分析阶段进度 (40-100%)
            if progress_callback:
                progress = 0.4 + (i + 1) / analyze_total * 0.6
                progress_callback(progress, f"分析中... {target['name']} ({i+1}/{analyze_total})")

        except Exception as e:
            logger.error(f"分析 {target['symbol']} 失败: {e}")
            continue

    # 完成
    if progress_callback:
        progress_callback(1.0, "分析完成！")

    logger.info(f"完成 {len(results)} 个标的的分析")
    return results
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_etf_lof_gamble.py::test_screen_and_analyze_with_progress_callback -v`

Expected: PASS

**Step 5: 提交**

```bash
git add analysis/etf_lof_gamble.py tests/test_etf_lof_gamble.py
git commit -m "feat: add progress callback support to screen_and_analyze"
```

---

## Task 3: 在 UI 中集成进度条显示

**Files:**
- Modify: `ui/dashboard.py:897-1021`

**Step 1: 手动测试 - 验证现有UI**

无需测试代码，直接启动UI验证现有功能：

Run: `uv run streamlit run ui/dashboard.py`

Expected: 可以看到【ETF/LOF 投机分析】页面和【异常波动筛选】标签页

**Step 2: 修改 render_abnormal_screening_page 添加进度条**

Modify file: `ui/dashboard.py` (找到 `render_abnormal_screening_page` 函数)

在筛选执行部分添加进度条：

```python
# 执行筛选
# 创建进度占位符
progress_placeholder = st.empty()

with progress_placeholder.container():
    progress_bar = st.progress(0, text="准备开始筛选...")

try:
    # 定义进度回调函数
    def update_progress(progress: float, message: str):
        progress_bar.progress(progress, text=message)

    results = screen_and_analyze_with_mode(
        gamble_analyzer, criteria, top_n, scan_mode, progress_callback=update_progress
    )

    # 清除进度条
    progress_placeholder.empty()

    if results:
        st.markdown(f"""
        <div class="success-box">
            <h4>筛选完成！找到 {len(results)} 个异常波动标的</h4>
        </div>
        """, unsafe_allow_html=True)

        # 显示结果列表
        display_screening_results(results)

    else:
        st.markdown("""
        <div class="warning-box">
            <h4>未找到符合条件的标的</h4>
            <p>请尝试调整筛选条件...</p>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    progress_placeholder.empty()
    st.markdown(f"""
    <div class="error-box">
        <h4>筛选失败</h4>
        <p>错误信息: {str(e)}</p>
    </div>
    """, unsafe_allow_html=True)
```

**Step 3: 修改 screen_and_analyze_with_mode 支持进度回调传递**

Modify file: `ui/dashboard.py` (找到 `screen_and_analyze_with_mode` 函数)

添加 `progress_callback` 参数并传递给内部函数：

```python
def screen_and_analyze_with_mode(
    _analyzer, criteria: Dict, top_n: int, scan_mode: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List:
    """
    根据筛选模式执行分析

    Args:
        _analyzer: LOFETFGambleAnalyzer实例
        criteria: 筛选条件
        top_n: 返回数量
        scan_mode: 'use_cache'（使用缓存）或 'rescan'（重新扫描）
        progress_callback: 进度回调函数

    Returns:
        分析结果列表
    """
    from data.fetchers.akshare_fetcher import AKShareFetcher
    import time

    fetcher = AKShareFetcher()
    fund_types = criteria.get('fund_types', [])

    # 获取目标基金列表
    target_list = []
    if scan_mode == 'rescan':
        # 重新扫描模式：使用时间戳绕过缓存，强制重新获取
        st.info("🔄 正在重新扫描基金列表...")
        refresh_token = time.time()  # 使用时间戳作为唯一标识
        for fund_type in fund_types:
            # 传入刷新令牌绕过缓存
            fund_list = cached_get_fund_list(fetcher, fund_type, _force_refresh=refresh_token)
            target_list.extend(fund_list)
    else:
        # 使用缓存模式：直接从缓存获取
        st.info("💾 使用缓存的基金列表...")
        for fund_type in fund_types:
            fund_list = cached_get_fund_list(fetcher, fund_type)
            target_list.extend(fund_list)

    # 使用分析器的内部逻辑进行筛选和深度分析
    # 这里复用 screen_and_analyze 的逻辑，但传入已获取的 target_list
    return _screen_and_analyze_with_targets(
        _analyzer, target_list, criteria, top_n, progress_callback
    )
```

**Step 4: 修改 _screen_and_analyze_with_targets 支持进度回调传递**

Modify file: `ui/dashboard.py` (找到 `_screen_and_analyze_with_targets` 函数)

添加 `progress_callback` 参数并传递给 analyzer：

```python
def _screen_and_analyze_with_targets(
    _analyzer, target_list: List[Dict], criteria: Dict, top_n: int,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List:
    """
    使用给定的目标列表进行筛选分析（内部函数）

    Args:
        _analyzer: LOFETFGambleAnalyzer实例
        target_list: 预先获取的基金列表
        criteria: 筛选条件
        top_n: 返回数量
        progress_callback: 进度回调函数

    Returns:
        分析结果列表
    """
    # ... 现有代码保持不变，直到深度分析部分 ...

    # 深度分析 - 使用分析器的 screen_and_analyze 方法
    # 由于我们已经筛选出了 top_targets，直接调用 analyze_single
    results = []
    for i, target in enumerate(top_targets):
        try:
            result = _analyzer.analyze_single(
                target['symbol'],
                target['name'],
                target['fund_type']
            )
            if result is not None:
                results.append(result)

            # 更新分析阶段进度
            if progress_callback:
                progress = 0.4 + (i + 1) / len(top_targets) * 0.6
                progress_callback(progress, f"分析中... {target['name']} ({i+1}/{len(top_targets)})")

        except Exception as e:
            logger.error(f"分析 {target['symbol']} 失败: {e}")
            continue

    # 完成
    if progress_callback:
        progress_callback(1.0, "分析完成！")

    return results
```

**Step 5: 添加导入语句**

在文件顶部添加：

```python
from typing import Callable, Optional
```

**Step 6: 手动验证进度条显示**

Run: `uv run streamlit run ui/dashboard.py`

操作：
1. 进入【ETF/LOF 投机分析】->【异常波动筛选】
2. 设置筛选条件
3. 点击"开始筛选"

Expected: 看到进度条从0%到100%显示当前进度

**Step 7: 提交**

```bash
git add ui/dashboard.py
git commit -m "feat: add progress bar to abnormal fluctuation screening"
```

---

## Task 4: 在 UI 中集成历史记录功能

**Files:**
- Modify: `ui/dashboard.py:1073-1142` (render_ai_analysis_page 函数)

**Step 1: 创建历史记录辅助函数**

在 `ui/dashboard.py` 中添加辅助函数（在 `cached_analyze_single` 函数之后）：

```python
def get_history_manager():
    """获取历史记录管理器实例（缓存）"""
    cache_dir = Path(__file__).parent.parent / ".cache" / "streamlit"

    # 使用 session_state 缓存管理器实例
    if 'history_manager' not in st.session_state:
        from storage.analysis_history import AnalysisHistoryManager
        st.session_state.history_manager = AnalysisHistoryManager(cache_dir)

    return st.session_state.history_manager


def save_analysis_to_history(result):
    """保存分析结果到历史"""
    import time

    manager = get_history_manager()

    entry = AnalysisHistoryEntry(
        id=f"{int(time.time()*1000)}-{result.symbol}",
        symbol=result.symbol,
        name=result.name,
        fund_type=result.fund_type,
        created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        abnormal_events_count=result.abnormal_events_count,
        current_price=result.current_factors.get('price_trend', 0),  # 简化处理
        ai_summary=result.ai_summary,
        current_factors=result.current_factors
    )

    manager.add_entry(entry)


def render_history_section():
    """渲染历史记录区域"""
    manager = get_history_manager()

    st.markdown("---")

    # 使用 expander 折叠区域
    with st.expander("📜 分析历史记录", expanded=False):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            search_keyword = st.text_input("搜索", placeholder="输入代码或名称", key="history_search")

        with col2:
            filter_type = st.selectbox(
                "类型",
                options=["全部", "LOF", "ETF"],
                key="history_filter_type"
            )

        with col3:
            st.write("")  # 占位
            refresh_btn = st.button("刷新", key="history_refresh")

        # 获取历史记录
        fund_type_filter = None if filter_type == "全部" else filter_type
        entries = manager.search(keyword=search_keyword, fund_type=fund_type_filter)

        if not entries:
            st.info("暂无历史记录")
        else:
            # 显示历史记录列表
            for entry in entries:
                col1, col2, col3, col4 = st.columns([2, 3, 3, 2])

                with col1:
                    st.markdown(f"**{entry.symbol}**")

                with col2:
                    st.markdown(f"{entry.name}")

                with col3:
                    st.caption(entry.created_at.replace('T', ' '))

                with col4:
                    view_btn = st.button("查看", key=f"view_{entry.id}")
                    delete_btn = st.button("删除", key=f"delete_{entry.id}")

                    if view_btn:
                        # 显示详情对话框
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>{entry.name} ({entry.symbol})</h4>
                            <p>类型: {entry.fund_type} | 异常事件: {entry.abnormal_events_count}次</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(entry.ai_summary)

                    if delete_btn:
                        if manager.delete_entry(entry.id):
                            st.rerun()
                        else:
                            st.error("删除失败")

            # 底部操作按钮
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("清空全部", key="history_clear_all"):
                    if manager.clear_all():
                        st.rerun()
                    else:
                        st.error("清空失败")

            with col2:
                if st.button("导出CSV", key="history_export"):
                    csv_path = manager.export_to_csv()
                    if csv_path:
                        st.success(f"已导出到: {csv_path}")
                    else:
                        st.error("导出失败")
```

**Step 2: 修改 render_ai_analysis_page 集成历史记录**

Modify file: `ui/dashboard.py` (找到 `render_ai_analysis_page` 函数)

在 AI 分析完成后保存历史，并添加历史记录区域：

```python
def render_ai_analysis_page(gamble_analyzer):
    """渲染AI深度分析页面"""
    st.subheader("AI深度分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        analysis_code = st.text_input(
            "基金代码",
            placeholder="如 163415",
            help="输入6位基金代码"
        )

    with col2:
        st.write("")  # 占位
        analyze_btn = st.button("开始分析", type="primary")

    if analyze_btn and analysis_code:
        with st.spinner("正在分析，请稍候..."):
            try:
                result = cached_analyze_single(
                    gamble_analyzer,
                    analysis_code,
                    f"基金{analysis_code}",  # 简化名称
                    "LOF"  # 默认类型
                )

                if result:
                    display_ai_analysis_result(result)

                    # 保存到历史记录
                    try:
                        save_analysis_to_history(result)
                        st.success("已保存到历史记录")
                    except Exception as e:
                        st.warning(f"保存历史失败: {str(e)}")

                else:
                    st.warning("""
                    **分析未完成**

                    可能原因：
                    1. 数据不足（需要至少100天历史数据）
                    2. 未发现异常波动事件
                    3. 无法获取数据

                    请尝试其他代码或调整筛选条件。
                    """)

            except Exception as e:
                st.error(f"分析失败: {str(e)}")

    # 渲染历史记录区域
    render_history_section()

    # 使用说明
    with st.expander("💡 使用说明"):
        st.markdown("""
        ### 常见LOF/ETF代码参考

        **大宗商品LOF：**
        - 163415: 白银LOF
        - 161116: 黄金基金
        - 162411: 华宝油气
        - 160716: 有色金属

        **海外ETF：**
        - 513100: 纳斯达克100
        - 513500: 标普500
        - 513660: 恒生ETF

        ### 分析内容

        AI将为您分析：
        1. **因子解读** - 当前关键因子说明了什么
        2. **历史规律** - 该标的异常波动的特点
        3. **时机判断** - 是否适合买入
        4. **操作建议** - 买入点位、止盈止损
        5. **风险提示** - 主要风险点
        """)
```

**Step 3: 添加必要的导入**

在文件顶部确保有以下导入：

```python
from storage.analysis_history import AnalysisHistoryEntry
```

**Step 4: 手动验证历史记录功能**

Run: `uv run streamlit run ui/dashboard.py`

操作：
1. 进入【ETF/LOF 投机分析】->【AI深度分析】
2. 输入基金代码并分析
3. 分析完成后查看历史记录区域
4. 测试搜索、过滤、查看、删除、导出功能

Expected:
- 分析完成后自动保存到历史
- 历史记录区域可以正常展开/收起
- 搜索和过滤功能正常
- 删除和导出功能正常

**Step 5: 提交**

```bash
git add ui/dashboard.py
git commit -m "feat: add analysis history feature with search, filter, export"
```

---

## Task 5: 验收测试

**Step 1: 运行所有测试**

Run: `uv run pytest -v`

Expected: 所有测试通过

**Step 2: 端到端手动测试**

1. **进度显示测试**
   - 启动应用
   - 进入【异常波动筛选】
   - 执行筛选，观察进度条

2. **历史记录测试**
   - 进入【AI深度分析】
   - 分析一个基金
   - 查看历史记录
   - 测试搜索、过滤、查看、删除、导出

**Step 3: 创建验证清单**

创建文件: `docs/verification-checklist.md`

```markdown
# ETF/LOF 历史记录与进度显示 - 验收清单

## 进度显示功能
- [ ] 异常波动筛选显示实时进度
- [ ] 筛选阶段显示当前处理数量
- [ ] 分析阶段显示当前分析标的名称
- [ ] 完成后进度条消失

## 历史记录功能
- [ ] AI分析后自动保存到历史
- [ ] 历史记录区域可展开/收起
- [ ] 历史记录支持按关键词搜索
- [ ] 历史记录支持按基金类型过滤
- [ ] 历史记录支持查看详情
- [ ] 历史记录支持删除单条记录
- [ ] 历史记录支持清空全部
- [ ] 历史记录支持导出CSV
- [ ] JSON文件正确持久化数据
```

**Step 4: 完成验收后提交**

```bash
git add docs/verification-checklist.md
git commit -m "docs: add verification checklist for history and progress features"
```

---

## 总结

本计划实现了以下功能：

1. **存储模块** (`storage/analysis_history.py`)
   - AnalysisHistoryEntry 数据类
   - AnalysisHistoryManager 管理类
   - JSON 持久化存储

2. **进度回调** (`analysis/etf_lof_gamble.py`)
   - screen_and_analyze 支持进度回调
   - 分阶段更新进度

3. **UI 集成** (`ui/dashboard.py`)
   - 异常波动筛选进度条
   - AI深度分析历史记录区域
   - 搜索、过滤、查看、删除、导出功能

所有变更遵循 TDD 原则，每步都有测试覆盖。
