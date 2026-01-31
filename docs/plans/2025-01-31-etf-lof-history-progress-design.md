# ETF/LOF 投机分析 - 历史记录与进度显示功能设计

**日期**: 2025-01-31
**状态**: 设计完成

## 概述

为【ETF/LOF 投机分析】模块添加以下两项功能：

1. **分析报告历史记录**：将AI分析结果归档，支持查看、搜索、过滤、删除和导出
2. **分析进度显示**：在异常波动筛选时显示实时进度

## 需求总结

| 功能 | 位置 | 实现方式 |
|------|------|----------|
| 分析历史记录 | AI深度分析标签页内（可折叠区域） | JSON文件存储 |
| 分析进度显示 | 异常波动筛选标签页 | Streamlit进度条 |

## 1. 数据模型设计

### 1.1 历史记录数据结构

```python
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
```

### 1.2 存储文件

```
.cache/streamlit/analysis_history.json
```

文件格式：
```json
{
  "entries": [
    {
      "id": "1738300000000-163415",
      "symbol": "163415",
      "name": "白银LOF",
      "fund_type": "LOF",
      "created_at": "2025-01-31T14:30:00",
      "abnormal_events_count": 5,
      "current_price": 0.856,
      "ai_summary": "## AI分析报告\n...",
      "current_factors": {"momentum_5": 0.05, ...}
    }
  ]
}
```

## 2. 存储模块设计

### 2.1 AnalysisHistoryManager

```python
class AnalysisHistoryManager:
    """分析历史记录管理器"""

    def __init__(self, cache_dir: Path):
        self.cache_file = cache_dir / "analysis_history.json"

    def add_entry(self, entry: AnalysisHistoryEntry) -> bool
    def get_all_entries(self) -> List[AnalysisHistoryEntry]
    def delete_entry(self, entry_id: str) -> bool
    def clear_all(self) -> bool
    def export_to_csv(self) -> str
    def search(self, keyword: str = "", fund_type: str = None) -> List[AnalysisHistoryEntry]
```

## 3. 进度显示设计

### 3.1 进度追踪器

在 `screen_and_analyze_with_mode` 函数中集成：

```python
# 快速筛选阶段 (0-40%)
progress_bar = st.progress(0, text="正在筛选异常波动标的...")
for i, item in enumerate(target_list[:top_n * 3]):
    # ... 筛选逻辑 ...
    progress = (i + 1) / len(target_list[:top_n * 3])
    progress_bar.progress(progress * 0.4, text=f"筛选中... {i+1}/{total}")

# 深度分析阶段 (40-100%)
progress_bar.progress(0.4, text="开始AI深度分析...")
for i, target in enumerate(top_targets):
    # ... 分析逻辑 ...
    progress = 0.4 + (i + 1) / len(top_targets) * 0.6
    progress_bar.progress(progress, text=f"分析中... {target['name']} ({i+1}/{total})")

progress_bar.progress(1.0, text="分析完成！")
```

### 3.2 进度阶段划分

| 阶段 | 进度范围 | 描述 |
|------|----------|------|
| 快速筛选 | 0% - 40% | 遍历基金列表检测异常波动 |
| 深度分析 | 40% - 100% | AI分析筛选出的标的 |

## 4. UI 界面设计

### 4.1 AI深度分析标签页

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 AI深度分析                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 输入基金代码进行分析                                      │ │
│ │ 基金代码: [163415]                    [开始分析]         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📜 分析历史记录                               [展开/收起] │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 搜索: [______] 类型: [全部▼]                             │ │
│ │                                                          │ │
│ │ 白银LOF (163415) | 2025-01-31 14:30 | [查看][删除]       │ │
│ │ 黄金基金 (161116) | 2025-01-30 09:15 | [查看][删除]       │ │
│ │                                                         │ │
│ │ [清空全部] [导出CSV]                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 异常波动筛选标签页

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 异常波动筛选                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 筛选条件配置 (现有表单)                                       │
│                                    [开始筛选]                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 筛选进度                                                 │ │
│ │ ████████████████████░░░░░ 85%                           │ │
│ │ 分析中... 白银LOF (17/20)                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 筛选结果                                                    │
└─────────────────────────────────────────────────────────────┘
```

## 5. 文件结构

```
money-agent/
├── analysis/
│   └── etf_lof_gamble.py          # 修改：添加进度回调支持
├── storage/
│   ├── __init__.py
│   └── analysis_history.py        # 新增：历史记录管理器
├── ui/
│   └── dashboard.py               # 修改：添加历史记录UI和进度显示
└── .cache/
    └── streamlit/
        └── analysis_history.json  # 运行时自动创建
```

## 6. 交互流程

### 6.1 异常波动筛选（带进度）

1. 用户设置筛选条件
2. 点击"开始筛选"
3. 显示进度条：筛选阶段 → 分析阶段 → 完成
4. 显示筛选结果列表

### 6.2 AI分析并保存历史

1. 用户输入基金代码
2. 点击"开始分析"
3. 分析完成后自动保存到历史
4. 历史记录区域自动刷新

### 6.3 历史记录管理

1. 展开历史记录区域
2. 搜索/过滤记录
3. 查看/删除单条记录
4. 清空全部或导出CSV

## 7. 实现要点

### 7.1 进度回调

修改 `LOFETFGambleAnalyzer.screen_and_analyze()` 添加可选的进度回调：

```python
def screen_and_analyze(
    self,
    criteria: Optional[Dict] = None,
    top_n: int = 20,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List[GambleAnalysisResult]:
    # 在循环中调用 progress_callback(progress, message)
```

### 7.2 自动保存历史

在AI分析完成后自动保存：

```python
# 在 cached_analyze_single 中
if result:
    history_manager.add_entry(AnalysisHistoryEntry(
        id=f"{int(time.time()*1000)}-{symbol}",
        symbol=result.symbol,
        name=result.name,
        # ...
    ))
```

### 7.3 UI状态管理

使用 `st.session_state` 管理历史记录展开状态和搜索条件。

## 8. 验收标准

- [ ] 异常波动筛选显示实时进度
- [ ] AI分析后自动保存到历史
- [ ] 历史记录支持搜索和过滤
- [ ] 历史记录支持删除单条和清空全部
- [ ] 历史记录支持查看详情
- [ ] 历史记录支持导出CSV
- [ ] JSON文件正确持久化数据
