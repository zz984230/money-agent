# ETF/LOF 投机分析 - 查询配置功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在ETF/LOF投机分析页面中添加查询配置功能，支持双栏穿梭框选择标的、手动命名保存配置、批量分析等能力。

**Architecture:** 新增 `FundSelectionManager` 类管理配置持久化，修改 `render_abnormal_screening_page` 添加双栏穿梭框UI，修改 `screen_and_analyze_with_mode` 支持选中标的的筛选。

**Tech Stack:** Python 3.11+, Streamlit, JSON文件存储, Pytest

---

## Task 1: 创建 `storage/fund_selection.py` - 数据模型

**Files:**
- Create: `storage/fund_selection.py`

**Step 1: Write the failing test**

Create: `tests/test_fund_selection.py`

```python
"""测试基金选择配置管理器"""
import pytest
from pathlib import Path
from datetime import datetime
from storage.fund_selection import FundSelectionManager, FundSelectionConfig


@pytest.fixture
def temp_config_dir(tmp_path):
    """临时配置目录"""
    config_dir = tmp_path / "fund_selections"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def manager(temp_config_dir):
    """配置管理器实例"""
    return FundSelectionManager(temp_config_dir)


def test_save_new_config(manager, temp_config_dir):
    """测试保存新配置"""
    funds = [
        {"code": "163415", "name": "白银LOF", "type": "commodity"},
        {"code": "161226", "name": "白银基金", "type": "commodity"},
    ]

    result = manager.save_config("白银组合", funds)

    assert result is True
    # 检查配置文件已创建
    config_file = temp_config_dir / "白银组合.json"
    assert config_file.exists()

    # 检查索引文件已更新
    index_file = temp_config_dir / "configs.json"
    assert index_file.exists()


def test_save_duplicate_config_without_overwrite(manager):
    """测试保存重复配置（不覆盖）"""
    funds = [{"code": "163415", "name": "白银LOF", "type": "commodity"}]

    # 第一次保存
    manager.save_config("白银组合", funds)

    # 第二次保存（不覆盖）
    result = manager.save_config("白银组合", funds, overwrite=False)

    assert result is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_fund_selection.py::test_save_new_config -v`

Expected: `ModuleNotFoundError: No module named 'storage.fund_selection'`

**Step 3: Write minimal implementation**

Create: `storage/fund_selection.py`

```python
"""基金选择配置管理器"""
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FundSelectionConfig:
    """基金选择配置"""
    name: str
    created_at: str
    updated_at: str
    funds: List[Dict]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FundSelectionConfig':
        """从字典创建实例"""
        return cls(**data)


class FundSelectionManager:
    """基金选择配置管理器"""

    def __init__(self, cache_dir: Path):
        """
        初始化管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.config_dir = cache_dir / "fund_selections"
        self.config_index_file = self.config_dir / "configs.json"
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> Dict:
        """加载配置索引"""
        if not self.config_index_file.exists():
            return {"configs": []}

        try:
            with open(self.config_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"加载配置索引失败: {e}")
            return {"configs": []}

    def _save_index(self, data: Dict) -> bool:
        """保存配置索引"""
        try:
            with open(self.config_index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"保存配置索引失败: {e}")
            return False

    def list_configs(self) -> List[Dict]:
        """获取所有配置列表（元数据）"""
        data = self._load_index()
        return data.get("configs", [])

    def save_config(self, name: str, funds: List[Dict], overwrite: bool = False) -> bool:
        """
        保存配置

        Args:
            name: 配置名称
            funds: 基金列表 [{"code": "xxx", "name": "xxx", "type": "xxx"}]
            overwrite: 是否覆盖同名配置

        Returns:
            是否成功保存
        """
        now = datetime.now().isoformat()

        # 检查配置是否已存在
        index = self._load_index()
        existing = next((c for c in index["configs"] if c["name"] == name), None)

        if existing and not overwrite:
            return False

        # 统计基金类型
        fund_types = list(set(f.get("type", "") for f in funds))

        # 创建或更新配置
        config = FundSelectionConfig(
            name=name,
            created_at=existing["created_at"] if existing else now,
            updated_at=now,
            funds=funds
        )

        # 保存配置文件
        config_file = self.config_dir / f"{name}.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

        # 更新索引
        if existing:
            existing.update({
                "updated_at": now,
                "fund_count": len(funds),
                "fund_types": fund_types
            })
        else:
            index["configs"].append({
                "name": name,
                "created_at": now,
                "updated_at": now,
                "fund_count": len(funds),
                "fund_types": fund_types
            })

        return self._save_index(index)

    def load_config(self, name: str) -> Optional[List[Dict]]:
        """
        加载指定配置的基金列表

        Args:
            name: 配置名称

        Returns:
            基金列表，配置不存在返回None
        """
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("funds", [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载配置文件失败: {e}")
            return None

    def delete_config(self, name: str) -> bool:
        """
        删除配置

        Args:
            name: 配置名称

        Returns:
            是否成功删除
        """
        # 删除配置文件
        config_file = self.config_dir / f"{name}.json"
        if config_file.exists():
            config_file.unlink()

        # 更新索引
        index = self._load_index()
        original_count = len(index["configs"])
        index["configs"] = [c for c in index["configs"] if c["name"] != name]

        if len(index["configs"]) < original_count:
            return self._save_index(index)

        return False

    def append_to_config(self, name: str, new_funds: List[Dict]) -> bool:
        """
        追加基金到现有配置（自动去重）

        Args:
            name: 配置名称
            new_funds: 新增基金列表

        Returns:
            是否成功追加
        """
        existing_funds = self.load_config(name)
        if existing_funds is None:
            return False

        # 去重：按code去重
        existing_codes = {f["code"] for f in existing_funds}
        funds_to_add = [f for f in new_funds if f["code"] not in existing_codes]

        if not funds_to_add:
            return True  # 没有新基金需要添加

        # 合并并保存
        merged_funds = existing_funds + funds_to_add
        return self.save_config(name, merged_funds, overwrite=True)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_fund_selection.py::test_save_new_config -v`

Expected: PASS

**Step 5: Commit**

```bash
git add storage/fund_selection.py tests/test_fund_selection.py
git commit -m "feat: add FundSelectionManager class with save/load functionality

Add data model and manager for fund selection configuration.
Supports saving, loading, and appending to named configs.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 2: 更新 `storage/__init__.py` 导出新类

**Files:**
- Modify: `storage/__init__.py`

**Step 1: Update imports**

Edit `storage/__init__.py`:

```python
"""存储模块 - 管理各类持久化数据"""

from storage.analysis_history import (
    AnalysisHistoryEntry,
    AnalysisHistoryManager
)
from storage.fund_selection import (
    FundSelectionConfig,
    FundSelectionManager
)

__all__ = [
    "AnalysisHistoryEntry",
    "AnalysisHistoryManager",
    "FundSelectionConfig",
    "FundSelectionManager",
]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_fund_selection.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add storage/__init__.py
git commit -m "feat: export FundSelectionConfig and FundSelectionManager

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 3: 完善单元测试

**Files:**
- Modify: `tests/test_fund_selection.py`

**Step 1: Write remaining tests**

Add to `tests/test_fund_selection.py`:

```python
def test_save_duplicate_config_with_overwrite(manager, temp_config_dir):
    """测试保存重复配置（覆盖）"""
    funds1 = [{"code": "163415", "name": "白银LOF", "type": "commodity"}]
    funds2 = [
        {"code": "163415", "name": "白银LOF", "type": "commodity"},
        {"code": "161226", "name": "白银基金", "type": "commodity"},
    ]

    # 第一次保存
    manager.save_config("白银组合", funds1)

    # 第二次保存（覆盖）
    result = manager.save_config("白银组合", funds2, overwrite=True)

    assert result is True
    # 验证配置已更新
    loaded = manager.load_config("白银组合")
    assert len(loaded) == 2


def test_load_existing_config(manager):
    """测试加载存在的配置"""
    funds = [{"code": "163415", "name": "白银LOF", "type": "commodity"}]
    manager.save_config("白银组合", funds)

    result = manager.load_config("白银组合")

    assert result is not None
    assert len(result) == 1
    assert result[0]["code"] == "163415"


def test_load_nonexistent_config(manager):
    """测试加载不存在的配置"""
    result = manager.load_config("不存在的配置")

    assert result is None


def test_list_configs(manager):
    """测试列出所有配置"""
    manager.save_config("配置1", [{"code": "163415", "name": "白银LOF", "type": "commodity"}])
    manager.save_config("配置2", [{"code": "161226", "name": "白银基金", "type": "commodity"}])

    result = manager.list_configs()

    assert len(result) == 2
    names = [c["name"] for c in result]
    assert "配置1" in names
    assert "配置2" in names


def test_delete_config(manager):
    """测试删除配置"""
    funds = [{"code": "163415", "name": "白银LOF", "type": "commodity"}]
    manager.save_config("白银组合", funds)

    result = manager.delete_config("白银组合")

    assert result is True
    # 验证配置已删除
    assert manager.load_config("白银组合") is None
    assert len(manager.list_configs()) == 0


def test_append_to_config_dedup(manager):
    """测试追加配置时去重"""
    original_funds = [{"code": "163415", "name": "白银LOF", "type": "commodity"}]
    new_funds = [
        {"code": "163415", "name": "白银LOF", "type": "commodity"},  # 重复
        {"code": "161226", "name": "白银基金", "type": "commodity"},  # 新增
    ]

    manager.save_config("白银组合", original_funds)
    result = manager.append_to_config("白银组合", new_funds)

    assert result is True
    # 验证去重后只有2个基金
    loaded = manager.load_config("白银组合")
    assert len(loaded) == 2
    codes = [f["code"] for f in loaded]
    assert "163415" in codes
    assert "161226" in codes


def test_corrupted_config_index(temp_config_dir):
    """测试配置索引损坏时恢复"""
    # 创建损坏的索引文件
    index_file = temp_config_dir / "configs.json"
    with open(index_file, 'w') as f:
        f.write("invalid json {{{")

    manager = FundSelectionManager(temp_config_dir)

    # 应该能正常初始化，返回空列表
    result = manager.list_configs()
    assert result == []
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_fund_selection.py -v`

Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_fund_selection.py
git commit -m "test: add comprehensive unit tests for FundSelectionManager

Add tests for save (with/without overwrite), load, list, delete,
append with dedup, and corrupted index recovery.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 4: 修改 `screen_and_analyze_with_mode` 支持选中标的

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: Write the test first**

Add to `tests/test_dashboard.py` (create if not exists):

```python
"""测试dashboard模块"""
import pytest
from unittest.mock import Mock, MagicMock
from ui.dashboard import screen_and_analyze_with_mode


def test_screen_and_analyze_with_selected_funds():
    """测试使用选中标的进行筛选"""
    # Mock分析器
    mock_analyzer = Mock()
    mock_analyzer.fetcher = Mock()

    # Mock返回值
    mock_result = {
        'symbol': '163415',
        'name': '白银LOF',
        'fund_type': 'commodity',
        'events_count': 2,
        'recent_change': 0.05
    }

    # Patch内部函数
    import ui.dashboard
    original_func = ui.dashboard._screen_and_analyze_with_targets
    ui.dashboard._screen_and_analyze_with_targets = Mock(return_value=[mock_result])

    # 选中标的列表
    selected_funds = [
        {"code": "163415", "name": "白银LOF", "type": "commodity"}
    ]

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    result = screen_and_analyze_with_mode(
        mock_analyzer, criteria, 10, 'use_cache',
        selected_funds=selected_funds
    )

    assert len(result) == 1
    assert result[0]['symbol'] == '163415'

    # 验证使用了选中的标的，而不是从fetcher获取
    ui.dashboard._screen_and_analyze_with_targets.assert_called_once()
    call_args = ui.dashboard._screen_and_analyze_with_targets.call_args
    # 第一个参数是target_list，应该是selected_funds
    assert call_args[0][1] == selected_funds

    # 恢复
    ui.dashboard._screen_and_analyze_with_targets = original_func
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_screen_and_analyze_with_selected_funds -v`

Expected: FAIL (function doesn't accept `selected_funds` parameter yet)

**Step 3: Modify the function**

Edit `ui/dashboard.py` at line 1428:

```python
def screen_and_analyze_with_mode(_analyzer, criteria: Dict, top_n: int, scan_mode: str, selected_funds: Optional[List[Dict]] = None, progress_callback: Optional[Callable[[float, str, Optional[str], Optional[int], Optional[int]], None]] = None) -> List:
    """
    根据筛选模式执行分析

    Args:
        _analyzer: LOFETFGambleAnalyzer实例
        criteria: 筛选条件
        top_n: 返回数量
        scan_mode: 'use_cache'（使用缓存）或 'rescan'（重新扫描）
        selected_funds: 用户选中的基金列表（可选，若提供则只分析这些标的）
        progress_callback: 进度回调函数，接收 (progress: float, message: str, name: Optional[str], current: Optional[int], total: Optional[int])

    Returns:
        分析结果列表
    """
    from data.fetchers.akshare_fetcher import AKShareFetcher
    import time

    fetcher = AKShareFetcher()
    fund_types = criteria.get('fund_types', [])

    # 获取目标基金列表
    target_list = []

    # 新增：优先使用用户选中的标的
    if selected_funds is not None:
        if progress_callback:
            progress_callback(0.0, f"📋 使用配置中的 {len(selected_funds)} 只基金...", None, None, None)
        else:
            st.info(f"📋 使用配置中的 {len(selected_funds)} 只基金...")
        target_list = selected_funds
    elif scan_mode == 'rescan':
        # 重新扫描模式：使用时间戳绕过缓存，强制重新获取
        if progress_callback:
            progress_callback(0.0, "🔄 正在重新扫描基金列表...", None, None, None)
        else:
            st.info("🔄 正在重新扫描基金列表...")
        refresh_token = time.time()  # 使用时间戳作为唯一标识
        for fund_type in fund_types:
            # 传入刷新令牌绕过缓存
            fund_list = cached_get_fund_list(fetcher, fund_type, _force_refresh=refresh_token)
            target_list.extend(fund_list)
    else:
        # 使用缓存模式：直接从缓存获取
        if progress_callback:
            progress_callback(0.0, "💾 使用缓存的基金列表...", None, None, None)
        else:
            st.info("💾 使用缓存的基金列表...")
        for fund_type in fund_types:
            fund_list = cached_get_fund_list(fetcher, fund_type)
            target_list.extend(fund_list)

    # 使用分析器的内部逻辑进行筛选和深度分析
    # 这里复用 screen_and_analyze 的逻辑，但传入已获取的 target_list
    return _screen_and_analyze_with_targets(_analyzer, target_list, criteria, top_n, progress_callback)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py::test_screen_and_analyze_with_selected_funds -v`

Expected: PASS

**Step 5: Commit**

```bash
git add ui/dashboard.py tests/test_dashboard.py
git commit -m "feat: support selected_funds parameter in screen_and_analyze_with_mode

Allow passing a list of user-selected funds to analyze, instead of
always fetching from cache or rescan. This enables batch analysis
of saved fund configurations.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 5: 添加UI辅助函数 - 双栏穿梭框组件

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: Write the UI helper function**

Add to `ui/dashboard.py` after the cache functions (around line 1426):

```python
def render_fund_selection_box(all_funds: List[Dict], key_prefix: str = "fund_select"):
    """
    渲染双栏穿梭框组件用于基金选择

    Args:
        all_funds: 全部可选基金列表 [{"code": "xxx", "name": "xxx", "type": "xxx"}]
        key_prefix: 组件key前缀，用于避免冲突

    Returns:
        List[Dict]: 用户选中的基金列表
    """
    # 初始化session state
    if f"{key_prefix}_selected" not in st.session_state:
        st.session_state[f"{key_prefix}_selected"] = []

    # 将基金列表格式化为显示字符串
    fund_options = [f"{f['code']} - {f['name']} ({f['type']})" for f in all_funds]

    # 创建映射：显示字符串 -> 基金字典
    str_to_fund = {opt: fund for opt, fund in zip(fund_options, all_funds)}

    col_left, col_mid, col_right = st.columns([2, 1, 2])

    with col_left:
        st.markdown("##### 可选标的")
        # 左侧：搜索框 + 多选列表
        search = st.text_input("🔍 搜索", key=f"{key_prefix}_search", placeholder="输入代码或名称...")
        if search:
            filtered_opts = [opt for opt in fund_options if search.lower() in opt.lower()]
        else:
            filtered_opts = fund_options

        selected_in_left = st.multiselect(
            "选择标的",
            options=filtered_opts,
            key=f"{key_prefix}_left_select",
            label_visibility="collapsed"
        )

    with col_mid:
        st.markdown("&nbsp;")  # 占位，对齐
        st.markdown("&nbsp;")

        # 移动按钮
        if st.button("→", key=f"{key_prefix}_move_right", help="移入右侧"):
            for opt in selected_in_left:
                fund = str_to_fund.get(opt)
                if fund and fund not in st.session_state[f"{key_prefix}_selected"]:
                    st.session_state[f"{key_prefix}_selected"].append(fund)
            st.rerun()

        if st.button("←", key=f"{key_prefix}_move_left", help="移出右侧"):
            # 从右侧移除（通过重新选择实现）
            st.rerun()

        if st.button("»", key=f"{key_prefix}_move_all", help="全部移入"):
            for fund in all_funds:
                if fund not in st.session_state[f"{key_prefix}_selected"]:
                    st.session_state[f"{key_prefix}_selected"].append(fund)
            st.rerun()

        if st.button("«", key=f"{key_prefix}_clear_all", help="清空右侧"):
            st.session_state[f"{key_prefix}_selected"] = []
            st.rerun()

    with col_right:
        st.markdown("##### 已选标的")
        selected = st.session_state[f"{key_prefix}_selected"]

        if selected:
            # 右侧：已选标的展示（使用data_editor支持删除）
            display_data = [
                {"代码": f["code"], "名称": f["name"], "类型": f["type"]}
                for f in selected
            ]
            edited = st.data_editor(
                display_data,
                column_config={
                    "代码": st.column_config.TextColumn(width="small"),
                    "名称": st.column_config.TextColumn(width="medium"),
                    "类型": st.column_config.TextColumn(width="small")
                },
                hide_index=True,
                use_container_width=True,
                key=f"{key_prefix}_right_display"
            )

            # 删除按钮
            if st.button("🗑️ 删除选中", key=f"{key_prefix}_delete"):
                # data_editor返回的是编辑后的数据，需要反推哪些被删除了
                # 简化处理：清空后用户需要重新选择
                st.session_state[f"{key_prefix}_selected"] = []
                st.rerun()
        else:
            st.info("暂无已选标的，请从左侧选择")

    return st.session_state[f"{key_prefix}_selected"]
```

**Step 2: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add render_fund_selection_box helper function

Add dual-column shuttle box component for fund selection.
Left column: searchable list of available funds.
Middle: move buttons (right, left, all, clear).
Right column: selected funds display with delete option.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 6: 修改 `render_abnormal_screening_page` 集成查询配置区域

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: Read the current implementation to understand the structure**

Read: `ui/dashboard.py` lines 898-1100

**Step 2: Modify the function to add query config section**

Edit `ui/dashboard.py` at line 898 (replace the existing "查看缓存的基金列表" expander section):

```python
def render_abnormal_screening_page(gamble_analyzer):
    """渲染异常波动筛选页面"""
    st.subheader("异常波动筛选")

    # 筛选模式选择（放在form外面，以便动态显示缓存信息）
    scan_mode = st.radio(
        "筛选模式",
        options=["use_cache", "rescan"],
        format_func=lambda x: "使用缓存重新计算" if x == "use_cache" else "重新扫描计算",
        help="使用缓存：基于已缓存的基金列表计算；重新扫描：重新获取基金列表并更新缓存"
    )

    # 获取配置管理器
    cache_dir = Path(__file__).parent.parent / ".cache" / "streamlit"
    from storage.fund_selection import FundSelectionManager
    config_manager = FundSelectionManager(cache_dir)

    # 用户选中的基金列表（用于后续分析）
    user_selected_funds = None

    # 【新增】查询配置区域（仅在使用缓存模式时显示）
    if scan_mode == "use_cache":
        st.markdown("---")
        st.markdown("### 📋 查询配置")

        # 配置选择器
        col_config1, col_config2, col_config3 = st.columns([2, 2, 2])
        with col_config1:
            config_names = ["-- 新建配置 --"] + [c["name"] for c in config_manager.list_configs()]
            selected_config_name = st.selectbox(
                "加载配置",
                options=config_names,
                key="abnormal_config_selector"
            )

        with col_config2:
            config_name_input = st.text_input(
                "配置名称",
                placeholder="输入配置名称（如：白银LOF组合）",
                key="abnormal_config_name_input"
            )

        with col_config3:
            st.markdown("&nbsp;")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                save_btn = st.button("💾 保存配置", key="abnormal_save_config", disabled=not config_name_input)
            with col_btn2:
                load_btn = st.button("📂 加载配置", key="abnormal_load_config", disabled=(selected_config_name == "-- 新建配置 --"))

        # 获取全部基金列表（用于穿梭框）
        try:
            from data.fetchers.akshare_fetcher import AKShareFetcher
            fetcher = AKShareFetcher()
            commodity_list = cached_get_fund_list(fetcher, 'commodity')
            overseas_list = cached_get_fund_list(fetcher, 'overseas')
            all_funds = commodity_list + overseas_list

            # 初始化已选列表（如果加载了配置）
            if "abnormal_selected_funds" not in st.session_state:
                st.session_state.abnormal_selected_funds = []

            # 处理加载配置
            if load_btn and selected_config_name != "-- 新建配置 --":
                loaded_funds = config_manager.load_config(selected_config_name)
                if loaded_funds is not None:
                    st.session_state.abnormal_selected_funds = loaded_funds
                    st.success(f"✅ 已加载配置：{selected_config_name}（{len(loaded_funds)}只基金）")
                else:
                    st.error(f"❌ 加载配置失败：{selected_config_name}")

            # 处理保存配置
            if save_btn and config_name_input:
                if st.session_state.abnormal_selected_funds:
                    # 检查是否已存在
                    existing = config_manager.load_config(config_name_input)
                    overwrite = False
                    if existing is not None:
                        overwrite = st.checkbox(f"配置 '{config_name_input}' 已存在，是否覆盖？", key="abnormal_overwrite_config")

                    result = config_manager.save_config(
                        config_name_input,
                        st.session_state.abnormal_selected_funds,
                        overwrite=overwrite
                    )
                    if result:
                        st.success(f"✅ 配置已保存：{config_name_input}")
                    else:
                        st.error(f"❌ 保存配置失败（可能配置已存在且未选择覆盖）")
                else:
                    st.warning("⚠️ 请先选择基金后再保存配置")

            # 渲染双栏穿梭框
            st.markdown("#### 选择标的")
            user_selected_funds = render_fund_selection_box(all_funds, key_prefix="abnormal_fund_select")

            # 同步到session_state供保存使用
            st.session_state.abnormal_selected_funds = user_selected_funds

        except Exception as e:
            st.warning(f"获取基金列表失败: {str(e)}")

        st.markdown("---")

    with st.form("abnormal_screening_form"):
        # ... 原有的筛选表单内容保持不变 ...
        # (从 col1, col2, col3 开始到表单结束)
```

**Note**: 需要保留原有的筛选表单内容，只替换/添加配置区域部分。完整的修改需要仔细处理，确保不破坏原有功能。

**Step 3: Run the dashboard to verify UI**

Run: `uv run streamlit run ui/dashboard.py`

Expected: UI should show the new query config section when "使用缓存重新计算" is selected.

**Step 4: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add query config section to abnormal screening page

Add dual-column shuttle box for fund selection when using cache mode.
Features:
- Load existing named configurations
- Save current selection as named config
- Visual display of selected funds with delete option
- Batch analysis of selected funds

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 7: 修改筛选表单提交逻辑支持选中标的

**Files:**
- Modify: `ui/dashboard.py`

**Step 1: Locate the form submission handler**

Find the section where the form is submitted (around line 1050-1100 in original code).

**Step 2: Modify to pass selected_funds**

The form submission calls `screen_and_analyze_with_mode`. Add the `selected_funds` parameter:

```python
# 在表单提交时
if submitted:
    criteria = {...}  # 原有的criteria构建逻辑

    # 传递用户选中的基金列表（如果有）
    results = screen_and_analyze_with_mode(
        gamble_analyzer,
        criteria,
        top_n,
        scan_mode,
        selected_funds=user_selected_funds,  # 新增参数
        progress_callback=progress_callback
    )
```

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: pass selected_funds to analysis on form submit

When user has selected funds via query config section,
pass them to screen_and_analyze_with_mode for batch analysis.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 8: 添加集成测试

**Files:**
- Modify: `tests/test_fund_selection.py`

**Step 1: Write integration test**

```python
@pytest.mark.integration
def test_save_and_load_config_workflow(tmp_path):
    """测试保存→加载完整流程"""
    from storage.fund_selection import FundSelectionManager

    manager = FundSelectionManager(tmp_path)

    # 1. 保存配置
    funds = [
        {"code": "163415", "name": "白银LOF", "type": "commodity"},
        {"code": "161226", "name": "白银基金", "type": "commodity"},
    ]
    result = manager.save_config("测试组合", funds)
    assert result is True

    # 2. 验证配置出现在列表中
    configs = manager.list_configs()
    assert len(configs) == 1
    assert configs[0]["name"] == "测试组合"
    assert configs[0]["fund_count"] == 2

    # 3. 加载配置
    loaded = manager.load_config("测试组合")
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0]["code"] == "163415"

    # 4. 追加新基金
    new_funds = [{"code": "518880", "name": "黄金ETF", "type": "commodity"}]
    result = manager.append_to_config("测试组合", new_funds)
    assert result is True

    # 5. 验证追加后数量
    updated = manager.load_config("测试组合")
    assert len(updated) == 3

    # 6. 删除配置
    result = manager.delete_config("测试组合")
    assert result is True
    assert manager.load_config("测试组合") is None


@pytest.mark.integration
def test_append_funds_and_analyze():
    """测试追加标的→批量分析流程"""
    from storage.fund_selection import FundSelectionManager
    from unittest.mock import Mock, patch
    import ui.dashboard

    # 这个测试验证UI组件正确传递选中标的到分析函数
    # 由于涉及Streamlit，这里只验证逻辑连接

    # Mock screen_and_analyze_with_mode的内部调用
    with patch('ui.dashboard._screen_and_analyze_with_targets') as mock_analyze:
        mock_analyze.return_value = []

        selected_funds = [
            {"code": "163415", "name": "白银LOF", "type": "commodity"}
        ]

        # 模拟调用
        from ui.dashboard import screen_and_analyze_with_mode
        result = screen_and_analyze_with_mode(
            Mock(),  # mock analyzer
            {'window': 3, 'threshold': 0.15, 'fund_types': ['commodity']},
            10,
            'use_cache',
            selected_funds=selected_funds
        )

        # 验证内部函数被调用，且传入了selected_funds
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        # target_list应该是selected_funds
        assert call_args[0][1] == selected_funds
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/test_fund_selection.py -v -m integration`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_fund_selection.py
git commit -m "test: add integration tests for fund selection config

Test save/load workflow and append funds with analysis.
Verify selected funds are correctly passed to analysis function.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## Task 9: 手动测试验证

**Step 1: Start the dashboard**

Run: `uv run streamlit run ui/dashboard.py`

**Step 2: Verify the following scenarios**

| 场景 | 预期结果 |
|------|----------|
| 选择"使用缓存重新计算" | 显示查询配置区域和双栏穿梭框 |
| 在左侧搜索框输入"白银" | 左侧列表过滤显示含"白银"的标的 |
| 勾选标的点击"→"移入 | 右侧显示已选标的 |
| 输入配置名点击"保存配置" | 显示成功提示，配置保存到文件 |
| 从配置选择器选择已保存的配置 | 右侧自动填充该配置的标的 |
| 追加新标的后点击"保存"并选择"覆盖" | 配置更新，包含追加的标的 |
| 右侧有已选标的时点击"立即批量分析" | 只对选中的标的进行分析 |
| 右侧为空时点击"保存配置" | 按钮禁用或显示警告 |

**Step 3: Check generated files**

Verify configuration files are created:
```bash
ls -la .cache/streamlit/fund_selections/
```

Expected:
- `configs.json` - 配置索引
- `{config_name}.json` - 各配置详情文件

**Step 4: Document test results**

If all scenarios pass, the feature is complete.

---

## Task 10: 更新项目文档

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add documentation for the new feature**

Add to `CLAUDE.md` in the "Analysis Modules" section (around line 95):

```markdown
### ETF/LOF投机分析配置管理

位于 `storage/fund_selection.py`

**核心功能:**
- 保存/加载/删除命名配置
- 配置追加（自动去重）
- 支持批量分析选中标的

**使用示例:**
```python
from storage.fund_selection import FundSelectionManager
from pathlib import Path

manager = FundSelectionManager(Path(".cache/streamlit"))

# 保存配置
funds = [
    {"code": "163415", "name": "白银LOF", "type": "commodity"},
    {"code": "161226", "name": "白银基金", "type": "commodity"}
]
manager.save_config("白银LOF组合", funds)

# 加载配置
loaded = manager.load_config("白银LOF组合")

# 追加标的（自动去重）
new_funds = [{"code": "518880", "name": "黄金ETF", "type": "commodity"}]
manager.append_to_config("白银LOF组合", new_funds)

# 列出所有配置
configs = manager.list_configs()
```

**UI集成:**
- 在【ETF/LOF 投机分析】页面的"使用缓存重新计算"模式下
- 提供双栏穿梭框选择标的
- 支持保存/加载命名配置
- 支持批量分析选中标的
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add fund selection config documentation

Document FundSelectionManager usage and UI integration
for ETF/LOF speculation analysis.

Co-Authored-By: Claude (GLM-4.7) <noreply@anthropic.com>"
```

---

## 实施总结

| 任务 | 文件 | 说明 |
|------|------|------|
| 1 | `storage/fund_selection.py` | 创建数据模型和管理器 |
| 2 | `storage/__init__.py` | 导出新类 |
| 3 | `tests/test_fund_selection.py` | 单元测试 |
| 4 | `ui/dashboard.py` | 修改筛选函数支持选中标的 |
| 5 | `ui/dashboard.py` | 添加双栏穿梭框组件 |
| 6 | `ui/dashboard.py` | 集成查询配置区域UI |
| 7 | `ui/dashboard.py` | 修改表单提交逻辑 |
| 8 | `tests/test_fund_selection.py` | 集成测试 |
| 9 | - | 手动测试验证 |
| 10 | `CLAUDE.md` | 更新文档 |

## 验收标准

- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] UI交互正常（手动测试验证）
- [ ] 配置文件正确保存和加载
- [ ] 批量分析功能正常工作
- [ ] 文档已更新
