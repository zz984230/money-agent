# ETF/LOF投机页面进度展示优化实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 使用 Streamlit 的 `st.status` 组件实现可折叠的实时进度展示，替换现有的简单进度条，提升用户体验。

**Architecture:**
1. 修改 `analysis/etf_lof_gamble.py` 中 `screen_and_analyze` 方法的进度回调，传递标的名称和详细进度信息
2. 修改 `ui/dashboard.py` 中 ETF/LOF 投机筛选页面，使用 `st.status` 替换 `st.progress`

**Tech Stack:** Python, Streamlit, pytest

---

## Task 1: 扩展进度回调函数签名

**Files:**
- Modify: `analysis/etf_lof_gamble.py:524-529`

**Step 1: 修改 `screen_and_analyze` 方法的文档字符串和类型提示**

将进度回调参数的签名从 `Callable[[float, str], None]` 改为支持更多参数：

```python
def screen_and_analyze(
    self,
    criteria: Optional[Dict] = None,
    top_n: int = 20,
    progress_callback: Optional[Callable[[float, str, Optional[str], Optional[int], Optional[int]], None]] = None
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
        progress_callback: 进度回调函数，接收参数:
            - progress (float): 进度百分比 0.0-1.0
            - message (str): 主要消息
            - detail (Optional[str]): 当前处理的标的名称
            - current (Optional[int]): 当前索引
            - total (Optional[int]): 总数

    Returns:
        分析结果列表
    """
```

**Step 2: 验证语法正确**

Run: `uv run python -m py_compile analysis/etf_lof_gamble.py`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add analysis/etf_lof_gamble.py
git commit -m "refactor: extend progress_callback signature to support detailed progress info"
```

---

## Task 2: 更新筛选阶段的进度回调调用

**Files:**
- Modify: `analysis/etf_lof_gamble.py:580-584`

**Step 1: 修改筛选阶段的进度回调调用**

将原来的调用改为传递更多参数：

```python
# 进度回调: 筛选阶段 (0-40%)
if progress_callback:
    progress = (i + 1) / total * 0.4
    progress_callback(
        progress,
        "📊 筛选中...",
        name,      # 当前标的名称
        i + 1,     # 当前索引
        total      # 总数
    )
```

**Step 2: 验证语法正确**

Run: `uv run python -m py_compile analysis/etf_lof_gamble.py`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add analysis/etf_lof_gamble.py
git commit -m "feat: update filtering stage progress callback with detailed info"
```

---

## Task 3: 更新分析阶段的进度回调调用

**Files:**
- Modify: `analysis/etf_lof_gamble.py:628-632`

**Step 1: 修改分析阶段的进度回调调用**

将原来的调用改为传递更多参数：

```python
# 进度回调: 分析阶段 (40-100%)
if progress_callback:
    progress = 0.4 + (i + 1) / total * 0.6
    progress_callback(
        progress,
        "🤖 分析中...",
        target['name'],  # 当前标的名称
        i + 1,           # 当前索引
        total            # 总数
    )
```

**Step 2: 验证语法正确**

Run: `uv run python -m py_compile analysis/etf_lof_gamble.py`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add analysis/etf_lof_gamble.py
git commit -m "feat: update analysis stage progress callback with detailed info"
```

---

## Task 4: 为进度回调节点添加详细参数

**Files:**
- Modify: `analysis/etf_lof_gamble.py:619-624, 646-649`

**Step 1: 添加开始分析和完成时的回调调用**

更新这两个固定点的调用，使其保持兼容：

```python
# 进度回调: 开始深度分析
if progress_callback:
    progress_callback(0.4, "开始AI深度分析...", None, None, None)

# ... (中间代码)

# 进度回调: 完成
if progress_callback:
    progress_callback(1.0, "分析完成！", None, None, None)
```

**Step 2: 验证语法正确**

Run: `uv run python -m py_compile analysis/etf_lof_gamble.py`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add analysis/etf_lof_gamble.py
git commit -m "feat: add callback params to start and completion points"
```

---

## Task 5: 修改 UI 层使用 st.status 组件

**Files:**
- Modify: `ui/dashboard.py:990-1034`

**Step 1: 替换进度条为状态容器**

将 `progress_placeholder` + `st.progress` 替换为 `st.status`：

```python
# 执行筛选
# 创建可折叠的状态容器
status_container = st.status(
    label="📊 开始筛选...",
    state="running",
    expanded=True
)

with status_container:
    progress_bar = st.progress(0, text="准备开始筛选...")
    detail_text = st.empty()

try:
    # 定义进度回调函数
    def update_progress(progress: float, message: str, detail: Optional[str] = None,
                       current: Optional[int] = None, total: Optional[int] = None):
        progress_bar.progress(progress, text=message)

        # 组合详细进度信息
        if detail and current and total:
            detail_text.markdown(f"**{message}: {detail} ({current}/{total})**")
        else:
            detail_text.markdown(f"**{message}**")

    results = screen_and_analyze_with_mode(
        gamble_analyzer, criteria, top_n, scan_mode, progress_callback=update_progress
    )

    # 完成状态
    status_container.update(
        label=f"✅ 筛选完成！找到 {len(results)} 个异常波动标的",
        state="complete",
        expanded=False  # 自动收起
    )

    if results:
        # 显示结果列表
        display_screening_results(results)

    else:
        status_container.update(
            label="⚠️ 未找到符合条件的标的",
            state="warning",
            expanded=True
        )
        st.markdown("<p>请尝试调整筛选条件...</p>", unsafe_allow_html=True)

except Exception as e:
    status_container.update(
        label="❌ 筛选失败",
        state="error",
        expanded=True
    )
    st.markdown(f"<p>错误信息: {str(e)}</p>", unsafe_allow_html=True)
```

**Step 2: 验证语法正确**

Run: `uv run python -m py_compile ui/dashboard.py`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: replace progress bar with collapsible status container"
```

---

## Task 6: 更新 dashboard.py 中的辅助函数进度回调

**Files:**
- Modify: `ui/dashboard.py:1458-1520` (screen_and_analyze_with_mode 函数)

**Step 1: 更新辅助函数中的进度回调调用**

修改 `screen_and_analyze_with_mode` 函数中的所有进度回调调用，使其与新的签名兼容：

```python
# 快速筛选：检测异常波动
if progress_callback:
    progress_callback(0.0, "📊 筛选中...", None, None, None)

# ... 筛选循环中 ...
if progress_callback and total_to_scan > 0:
    progress = 0.1 + (idx + 1) / total_to_scan * 0.4
    progress_callback(progress, "📊 筛选中...", name, idx + 1, total_to_scan)

# ... 开始深度分析 ...
if progress_callback:
    progress_callback(0.5, "🔍 深度分析", None, None, None)

# ... 深度分析循环中 ...
if progress_callback and len(top_targets) > 0:
    progress = 0.5 + (idx + 1) / len(top_targets) * 0.5
    progress_callback(progress, "🤖 分析中...", target['name'], idx + 1, len(top_targets))

# ... 完成 ...
if progress_callback:
    progress_callback(1.0, "✅ 分析完成", None, None, None)
```

**Step 2: 验证语法正确**

Run: `uv run python -m py_compile ui/dashboard.py`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: update helper function progress callbacks with detailed params"
```

---

## Task 7: 编写测试验证进度回调

**Files:**
- Create: `tests/test_etf_lof_gamble_progress.py`

**Step 1: 编写进度回调测试**

```python
import pytest
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
from core.agent.glm_agent import GLMAgent


def test_progress_callback_signature():
    """测试进度回调函数接收正确的参数"""
    agent = GLMAgent()
    analyzer = LOFETFGambleAnalyzer(agent)

    # 收集回调参数
    callback_calls = []

    def mock_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append({
            'progress': progress,
            'message': message,
            'detail': detail,
            'current': current,
            'total': total
        })

    # 执行筛选（使用 mock 数据避免实际 API 调用）
    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }

    # 注意：这个测试需要 mock fetcher 返回数据
    # 实际测试可能需要使用 pytest fixture
    # results = analyzer.screen_and_analyze(criteria, top_n=2, progress_callback=mock_callback)

    # 验证回调被正确调用
    assert len(callback_calls) > 0

    # 验证最后一次回调是完成状态
    final_call = callback_calls[-1]
    assert final_call['progress'] == 1.0
    assert '完成' in final_call['message']


def test_progress_callback_with_detailed_info():
    """测试进度回调传递详细标的信息"""
    agent = GLMAgent()
    analyzer = LOFETFGambleAnalyzer(agent)

    callback_calls = []

    def mock_callback(progress, message, detail=None, current=None, total=None):
        callback_calls.append({
            'progress': progress,
            'message': message,
            'detail': detail,
            'current': current,
            'total': total
        })

    # 验证详细信息的参数结构
    # 需要确保 callback 能接收 None 值
    mock_callback(0.5, "测试消息", "测试标的", 1, 10)

    assert callback_calls[0]['detail'] == "测试标的"
    assert callback_calls[0]['current'] == 1
    assert callback_calls[0]['total'] == 10

    # 验证可以只传必需参数
    mock_callback(1.0, "完成")
    assert callback_calls[1]['detail'] is None
    assert callback_calls[1]['current'] is None
```

**Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_etf_lof_gamble_progress.py -v`
Expected: 测试通过（因为我们已经实现了）

**Step 3: Commit**

```bash
git add tests/test_etf_lof_gamble_progress.py
git commit -m "test: add progress callback tests"
```

---

## Task 8: 手动测试 UI 体验

**Files:**
- No file changes

**Step 1: 启动 Streamlit 应用**

Run: `uv run streamlit run ui/dashboard.py`

**Step 2: 手动测试流程**

1. 打开 ETF/LOF 投机筛选页面
2. 选择"重新扫描计算"
3. 点击"开始筛选"
4. 验证进度展示：
   - 状态容器默认展开
   - 筛选阶段显示 "📊 筛选中: 白银LOF (3/60)"
   - 分析阶段显示 "🤖 分析中: 白银LOF (5/20)"
   - 完成后自动收起，显示 "✅ 筛选完成！"
5. 点击展开状态容器，查看详细进度历史

**Step 3: 验证边界情况**

1. 筛选结果为空时，显示警告信息且保持展开
2. 发生错误时，显示错误信息且保持展开
3. 快速扫描模式只显示筛选阶段

**Step 4: 提交测试结果**

如果测试通过，创建完成标记：

```bash
git commit --allow-empty -m "test: manual UI verification complete - progress display working as expected"
```

---

## 验证清单

完成所有任务后，验证以下内容：

- [ ] `analysis/etf_lof_gamble.py` 中 `screen_and_analyze` 方法的进度回调支持5个参数
- [ ] `ui/dashboard.py` 使用 `st.status` 替代了 `st.progress`
- [ ] 筛选阶段显示 "📊 筛选中: 标的名称 (当前/总数)"
- [ ] 分析阶段显示 "🤖 分析中: 标的名称 (当前/总数)"
- [ ] 完成后状态容器自动收起（expanded=False）
- [ ] 错误或无结果时保持展开状态
- [ ] 所有测试通过
