# ETF/LOF投机页面进度展示优化设计

## 问题概述

当前ETF/LOF投机页面进行"重新扫描计算"时，只显示"正在筛选 60 个标的"的单一状态，用户无法了解具体进度和处理状态，体验不佳。

## 设计目标

- 筛选阶段和分析阶段都提供实时进度反馈
- 显示当前处理的标的名称和具体位置（如：3/60）
- 完成后自动收起进度区域，支持展开查看详情

## 技术方案

### 整体架构

使用 Streamlit 的 `st.status` 组件作为容器，配合 `st.progress` 显示实时进度：

1. **状态容器**：作为进度区域外层容器，支持展开/折叠
2. **进度条**：显示 0-100% 的进度百分比
3. **状态文本**：显示当前操作详情
4. **完成摘要**：完成后显示在状态容器内

### 进度分配

| 阶段 | 进度范围 |
|------|----------|
| 筛选阶段 | 0% → 40% |
| 分析阶段 | 40% → 100% |

### 回调机制

扩展现有 `progress_callback` 函数签名：

```python
def progress_callback(
    progress: float,              # 0.0 - 1.0
    message: str,                 # 主要消息
    detail: Optional[str] = None, # 当前标的名称
    current: Optional[int] = None, # 当前索引
    total: Optional[int] = None    # 总数
)
```

调用示例：
```python
# 筛选阶段
progress_callback(
    progress=0.4 * (i + 1) / total,
    message="📊 筛选中...",
    detail=item['name'],
    current=i + 1,
    total=total
)

# 分析阶段
progress_callback(
    progress=0.4 + 0.6 * (i + 1) / total,
    message="🤖 分析中...",
    detail=target['name'],
    current=i + 1,
    total=total
)
```

### UI 层实现

```python
# 创建可折叠的状态容器
status_container = st.status(
    label="📊 开始筛选...",
    state="running",
    expanded=True
)

with status_container:
    progress_bar = st.progress(0, text="准备开始筛选...")
    detail_text = st.empty()

# 进度回调函数
def update_progress(progress, message, detail=None, current=None, total=None):
    progress_bar.progress(progress, text=message)
    if detail and current and total:
        detail_text.markdown(f"**{message}: {detail} ({current}/{total})**")

# 完成后
status_container.update(
    label="✅ 筛选完成！",
    state="complete",
    expanded=False
)
```

### 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| 单个标的分析失败 | 跳过继续，记录 `⚠️ 跳过: XX基金 (数据获取失败)` |
| 用户中断 | 状态设为 `error`，显示 `❌ 已中断: 处理了 X 个标的` |
| 全部失败 | 显示 `⚠️ 未找到符合条件的标的`，保持展开 |
| 快速扫描模式 | 只显示筛选阶段进度 |
| 完整扫描模式 | 显示筛选+分析两个阶段 |

## 实现文件

- `analysis/etf_lof_gamble.py` - 修改 `screen_and_analyze` 方法的回调调用
- `ui/dashboard.py` - 使用 `st.status` 替换现有进度展示逻辑
