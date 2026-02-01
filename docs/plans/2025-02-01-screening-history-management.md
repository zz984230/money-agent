# Screening History Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add save/view/delete functionality for AI analysis reports in the ETF/LOF screening page

**Architecture:** Reuse existing `AnalysisHistoryManager` for storage, add batch save button in screening results, create new "Screening History" tab page

**Tech Stack:** Streamlit, Python dataclasses, JSON storage

---

## Task 1: Add Batch Save Function

**Files:**
- Create: None
- Modify: `ui/dashboard.py` (after line 1220, in `display_screening_results` function)
- Test: `tests/test_dashboard_screening.py` (create new)

**Step 1: Write the failing test**

Create `tests/test_dashboard_screening.py`:

```python
"""Tests for screening history management in dashboard"""
import pytest
from unittest.mock import Mock, patch
from analysis.etf_lof_gamble import GambleAnalysisResult
from storage.analysis_history import AnalysisHistoryManager
from pathlib import Path
import tempfile

def test_batch_save_screening_results():
    """Test batch save screening results to history"""
    # Create mock results
    mock_result = Mock(spec=GambleAnalysisResult)
    mock_result.symbol = "163415"
    mock_result.name = "白银LOF"
    mock_result.fund_type = "LOF"
    mock_result.abnormal_events_count = 3
    mock_result.ai_summary = "Test AI summary"
    mock_result.current_factors = {"price_trend": 100.5}

    results = [mock_result]

    # Patch the history manager
    with patch('ui.dashboard.get_history_manager') as mock_get_manager:
        mock_manager = Mock(spec=AnalysisHistoryManager)
        mock_manager.add_entry.return_value = True
        mock_get_manager.return_value = mock_manager

        # Import after patching
        from ui.dashboard import batch_save_screening_results

        # Call function
        count = batch_save_screening_results(results)

        # Verify
        assert count == 1
        mock_manager.add_entry.assert_called_once()
        call_args = mock_manager.add_entry.call_args
        entry = call_args[0][0]
        assert entry.symbol == "163415"
        assert entry.name == "白银LOF"


def test_batch_save_with_partial_failure():
    """Test batch save when some entries fail"""
    mock_result1 = Mock(spec=GambleAnalysisResult)
    mock_result1.symbol = "163415"
    mock_result1.name = "白银LOF"
    mock_result1.fund_type = "LOF"
    mock_result1.abnormal_events_count = 3
    mock_result1.ai_summary = "Test AI summary 1"
    mock_result1.current_factors = {"price_trend": 100.5}

    mock_result2 = Mock(spec=GambleAnalysisResult)
    mock_result2.symbol = "161116"
    mock_result2.name = "黄金基金"
    mock_result2.fund_type = "LOF"
    mock_result2.abnormal_events_count = 2
    mock_result2.ai_summary = "Test AI summary 2"
    mock_result2.current_factors = {"price_trend": 200.5}

    results = [mock_result1, mock_result2]

    with patch('ui.dashboard.get_history_manager') as mock_get_manager:
        mock_manager = Mock(spec=AnalysisHistoryManager)
        mock_manager.add_entry.side_effect = [True, False]  # First succeeds, second fails
        mock_get_manager.return_value = mock_manager

        from ui.dashboard import batch_save_screening_results

        count = batch_save_screening_results(results)

        # Only first should succeed
        assert count == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard_screening.py::test_batch_save_screening_results -v`

Expected: FAIL with "cannot import 'batch_save_screening_results'"

**Step 3: Write minimal implementation**

In `ui/dashboard.py`, add this function after the `display_screening_results` function (around line 1220):

```python
def batch_save_screening_results(results: List) -> int:
    """
    批量保存筛选结果到历史记录

    Args:
        results: GambleAnalysisResult 对象列表

    Returns:
        成功保存的数量
    """
    from storage.analysis_history import AnalysisHistoryEntry
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)
    manager = get_history_manager()
    saved_count = 0

    for result in results:
        try:
            entry = AnalysisHistoryEntry(
                id=f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{result.symbol}",
                symbol=result.symbol,
                name=result.name,
                fund_type=result.fund_type,
                created_at=datetime.now().isoformat(),
                abnormal_events_count=result.abnormal_events_count,
                current_price=result.current_factors.get('price_trend', 0),
                ai_summary=result.ai_summary,
                current_factors=result.current_factors
            )
            if manager.add_entry(entry):
                saved_count += 1
        except Exception as e:
            logger.error(f"保存 {result.symbol} 失败: {e}")

    return saved_count
```

Also need to add the import at the top of the file (around line 30):

```python
from typing import List, Dict, Any, Optional
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard_screening.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_dashboard_screening.py ui/dashboard.py
git commit -m "feat: add batch_save_screening_results function"
```

---

## Task 2: Add Batch Save Button to Screening Results

**Files:**
- Modify: `ui/dashboard.py:1205-1220` (in `display_screening_results` function)
- Test: Manual testing in browser

**Step 1: Modify display_screening_results function**

In `ui/dashboard.py`, find the `display_screening_results` function and add the batch save button after the dataframe display (around line 1203):

```python
def display_screening_results(results):
    """显示筛选结果"""
    # ... existing code to prepare data ...

    df = pd.DataFrame(result_data)

    st.dataframe(
        df,
        column_config={
            "代码": st.column_config.TextColumn("代码", width="short"),
            "名称": st.column_config.TextColumn("名称", width="medium"),
            "类型": st.column_config.TextColumn("类型", width="short"),
            "异常事件数": st.column_config.NumberColumn("异常事件", width="short"),
            "最近波动": st.column_config.TextColumn("最近波动", width="short")
        },
        use_container_width=True,
        hide_index=True
    )

    # 新增：批量保存按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        if st.button("💾 批量保存全部报告", key="batch_save_screening_results"):
            with st.spinner("正在保存报告..."):
                saved_count = batch_save_screening_results(results)
                if saved_count > 0:
                    st.success(f"✅ 已保存 {saved_count} 份报告到历史记录")
                else:
                    st.warning("⚠️ 保存失败，请查看日志")

    st.markdown("---")

    # 选择查看详情 (existing code continues below)
```

**Step 2: Test in browser**

Run: `uv run streamlit run ui/dashboard.py`

1. Navigate to "ETF/LOF投机" → "异常波动筛选"
2. Run a screening
3. Click "批量保存全部报告" button
4. Verify success message appears

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add batch save button to screening results"
```

---

## Task 3: Create History Entry to Result Converter

**Files:**
- Modify: `ui/dashboard.py` (add new function after `batch_save_screening_results`)
- Test: `tests/test_dashboard_screening.py`

**Step 1: Write the failing test**

Add to `tests/test_dashboard_screening.py`:

```python
def test_history_entry_to_result():
    """Test converting history entry to GambleAnalysisResult"""
    from storage.analysis_history import AnalysisHistoryEntry
    from analysis.etf_lof_gamble import GambleAnalysisResult
    from datetime import datetime

    entry = AnalysisHistoryEntry(
        id="20250201120000_163415",
        symbol="163415",
        name="白银LOF",
        fund_type="LOF",
        created_at="2025-02-01T12:00:00",
        abnormal_events_count=3,
        current_price=100.5,
        ai_summary="Test AI summary",
        current_factors={"price_trend": 100.5}
    )

    from ui.dashboard import history_entry_to_result

    result = history_entry_to_result(entry)

    assert result.symbol == "163415"
    assert result.name == "白银LOF"
    assert result.fund_type == "LOF"
    assert result.abnormal_events_count == 3
    assert result.ai_summary == "Test AI summary"
    # These should be empty/None for history entries
    assert result.abnormal_events == []
    assert result.feature_importance is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard_screening.py::test_history_entry_to_result -v`

Expected: FAIL with "cannot import 'history_entry_to_result'"

**Step 3: Write minimal implementation**

In `ui/dashboard.py`, add after `batch_save_screening_results`:

```python
def history_entry_to_result(entry):
    """
    将历史记录条目转换为 GambleAnalysisResult 以便复用显示函数

    Args:
        entry: AnalysisHistoryEntry 对象

    Returns:
        GambleAnalysisResult 对象
    """
    from analysis.etf_lof_gamble import GambleAnalysisResult

    return GambleAnalysisResult(
        symbol=entry.symbol,
        name=entry.name,
        fund_type=entry.fund_type,
        abnormal_events_count=entry.abnormal_events_count,
        abnormal_events=[],  # 历史记录中不包含
        current_factors=entry.current_factors,
        feature_importance=None,  # 历史记录中不包含
        ai_summary=entry.ai_summary
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard_screening.py::test_history_entry_to_result -v`

Expected: PASS

**Step 5: Commit**

```bash
git add ui/dashboard.py tests/test_dashboard_screening.py
git commit -m "feat: add history_entry_to_result converter"
```

---

## Task 4: Create Screening History Page

**Files:**
- Modify: `ui/dashboard.py` (add new function)
- Test: Manual testing in browser

**Step 1: Add render_screening_history_page function**

In `ui/dashboard.py`, add after `render_factor_summary_page` function:

```python
def render_screening_history_page(gamble_analyzer):
    """渲染筛选历史记录页面"""
    st.subheader("筛选历史记录")

    manager = get_history_manager()

    # 搜索和过滤控件
    st.markdown("### 🔍 搜索和过滤")
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        search_keyword = st.text_input(
            "搜索",
            placeholder="输入代码或名称",
            key="screening_history_search"
        )

    with col2:
        filter_type = st.selectbox(
            "类型",
            options=["全部", "LOF", "ETF"],
            key="screening_history_filter_type"
        )

    with col3:
        st.write("")
        refresh_btn = st.button("刷新", key="screening_history_refresh")

    # 获取历史记录
    fund_type_filter = None if filter_type == "全部" else filter_type
    entries = manager.search(keyword=search_keyword, fund_type=fund_type_filter)

    if not entries:
        st.info("暂无历史记录，请先进行筛选并保存报告")
        return

    # 显示历史记录列表
    st.markdown("---")
    st.markdown("### 📋 历史记录列表")

    for entry in entries:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 4, 2, 2])

            with col1:
                st.markdown(f"**{entry.symbol}**")

            with col2:
                st.markdown(f"{entry.name}")

            with col3:
                st.caption(entry.created_at.replace('T', ' '))

            with col4:
                view_btn = st.button("查看", key=f"screening_view_{entry.id}")

            with col5:
                delete_btn = st.button("删除", key=f"screening_delete_{entry.id}")

            # 查看详情
            if view_btn:
                st.markdown("---")
                result = history_entry_to_result(entry)
                display_ai_analysis_result(result)
                st.markdown("---")

            # 删除
            if delete_btn:
                if manager.delete_entry(entry.id):
                    st.success(f"已删除 {entry.symbol} 的报告")
                    st.rerun()
                else:
                    st.error("删除失败")

    # 底部操作按钮
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("清空全部", key="screening_history_clear_all"):
            if manager.clear_all():
                st.success("已清空全部历史记录")
                st.rerun()
            else:
                st.error("清空失败")

    with col2:
        if st.button("导出CSV", key="screening_history_export"):
            csv_path = manager.export_to_csv()
            if csv_path:
                st.success(f"已导出到: {csv_path}")
            else:
                st.error("导出失败")
```

**Step 2: Modify render_etf_lof_gamble_page to add new tab**

Find the `render_etf_lof_gamble_page` function and modify the tabs (around line 891):

```python
def render_etf_lof_gamble_page(gamble_analyzer):
    """渲染ETF/LOF投机分析页面"""
    st.markdown('<div class="sub-header">🎰 ETF/LOF 投机分析</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        识别大宗商品LOF和海外ETF的异常波动（2-3天突增突降），基于统计分析计算关键因子，AI分析并给出操作建议。
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "异常波动筛选",
        "AI深度分析",
        "因子分析汇总",
        "筛选历史记录"  # 新增
    ])

    with tab1:
        render_abnormal_screening_page(gamble_analyzer)

    with tab2:
        render_ai_analysis_page(gamble_analyzer)

    with tab3:
        render_factor_summary_page(gamble_analyzer)

    with tab4:
        render_screening_history_page(gamble_analyzer)  # 新增
```

**Step 3: Test in browser**

Run: `uv run streamlit run ui/dashboard.py`

1. Navigate to "ETF/LOF投机" → "筛选历史记录"
2. Should see the new tab page
3. After saving reports, they should appear in the list
4. Test view, delete, clear all, export

**Step 4: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: add screening history page with 4th tab"
```

---

## Task 5: Manual Testing Checklist

**Files:**
- None (manual testing)

**Step 1: Run full workflow test**

1. Start the app: `uv run streamlit run ui/dashboard.py`

2. **Test Save:**
   - Go to "ETF/LOF投机" → "异常波动筛选"
   - Run a screening with criteria: window=3, threshold=8%
   - Wait for results
   - Click "批量保存全部报告"
   - Verify success message with count

3. **Test View:**
   - Go to "筛选历史记录" tab
   - Verify saved reports appear
   - Click "查看" button
   - Verify AI report displays correctly

4. **Test Search:**
   - Enter fund code in search box
   - Verify filter works
   - Enter fund name
   - Verify filter works

5. **Test Type Filter:**
   - Select "LOF" from type dropdown
   - Verify only LOF entries shown
   - Select "ETF"
   - Verify only ETF entries shown

6. **Test Delete:**
   - Click "删除" button on an entry
   - Verify deletion message
   - Verify entry removed from list

7. **Test Clear All:**
   - Click "清空全部"
   - Verify all entries removed

8. **Test Export:**
   - Run screening again to create entries
   - Click "导出CSV"
   - Verify CSV file created in `.cache/streamlit/`

9. **Test Duplicate Save:**
   - Save the same screening twice
   - Verify both entries appear in history (different timestamps)

10. **Test Empty State:**
    - Clear all history
    - Go to "筛选历史记录" tab
    - Verify "暂无历史记录" message

**Step 2: Document any issues**

If any issues found, create bug tasks and fix them.

**Step 3: Final commit**

```bash
# If any fixes were needed
git add .
git commit -m "fix: address issues found in manual testing"
```

---

## Summary

This implementation adds:
1. **Batch save function** - `batch_save_screening_results()` to save all screening results
2. **Save button** - Added to screening results display
3. **Converter function** - `history_entry_to_result()` to reuse existing display function
4. **New tab page** - "筛选历史记录" with full CRUD operations
5. **Tests** - Unit tests for core functions
6. **Manual testing** - Complete workflow verification

**Files Modified:**
- `ui/dashboard.py` - Added 3 new functions, modified 2 existing functions

**Files Created:**
- `tests/test_dashboard_screening.py` - Unit tests

**Estimated Time:** 1-2 hours
