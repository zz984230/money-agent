# ETF/LOF 投机分析 - 查询配置功能设计

**日期**: 2025-01-31
**状态**: 设计完成，待实施

---

## 1. 需求概述

对【ETF/LOF 投机分析】页面的"筛选模式"中"使用缓存重新计算"功能进行优化：

1. **展示效果优化**：将下拉框改为大框内容展示（双栏穿梭框），可同时看到多个标的
2. **查询配置功能**：支持从列表中选择指定标的进行批量分析，配置按版本粒度缓存供后续追加使用

---

## 2. 整体架构

### 2.1 新增组件

| 组件 | 文件路径 | 职责 |
|------|----------|------|
| `FundSelectionManager` | `storage/fund_selection.py` | 配置管理核心，负责保存/加载/追加配置 |

### 2.2 存储结构

```
.cache/streamlit/fund_selections/
├── configs.json              # 配置元数据索引
└── {config_name}.json        # 各配置详情（如：白银LOF组合.json）
```

### 2.3 UI层级结构

```
ETF/LOF 投机分析页面
├── 筛选模式 (Radio: use_cache | rescan)
│
├── 【新增】查询配置区域 (当use_cache时显示)
│   ├── 配置选择器 (加载历史配置 / 新建配置)
│   ├── 双栏穿梭框
│   │   ├── 左侧：搜索框 + 全部标的列表（多选）
│   │   ├── 中间：移动按钮 (→ 移入选中 | ← 移出选中 | » 全部 | « 清空)
│   │   └── 右侧：已选标的展示区（支持移除）
│   ├── 配置名称输入框（手动命名）
│   └── 操作按钮：[保存配置] [加载配置] [立即批量分析]
│
└── 筛选表单 (原有的window/threshold等参数)
```

---

## 3. 数据结构设计

### 3.1 配置元数据索引 (`configs.json`)

```json
{
  "configs": [
    {
      "name": "白银LOF组合",
      "created_at": "2025-01-31T10:30:00",
      "updated_at": "2025-01-31T14:20:00",
      "fund_count": 5,
      "fund_types": ["commodity", "overseas"]
    },
    {
      "name": "黄金ETF观察",
      "created_at": "2025-01-30T09:15:00",
      "updated_at": "2025-01-30T09:15:00",
      "fund_count": 3,
      "fund_types": ["commodity"]
    }
  ]
}
```

### 3.2 单个配置详情 (`{config_name}.json`)

```json
{
  "name": "白银LOF组合",
  "created_at": "2025-01-31T10:30:00",
  "updated_at": "2025-01-31T14:20:00",
  "funds": [
    {"code": "163415", "name": "白银LOF", "type": "commodity"},
    {"code": "161226", "name": "白银基金", "type": "commodity"},
    {"code": "518880", "name": "黄金ETF", "type": "commodity"}
  ]
}
```

---

## 4. UI交互流程

### 4.1 新建配置并分析

| 步骤 | 用户操作 | 界面响应 |
|------|----------|----------|
| 1 | 选择"使用缓存重新计算" | 展开查询配置区域 |
| 2 | 看到双栏穿梭框 | 左侧显示全部基金（按类型分组），右侧为空 |
| 3 | 在左侧搜索框输入"白银" | 左侧列表过滤，只显示含"白银"的标的 |
| 4 | 勾选多个标的，点击"→ 移入" | 选中的标的移动到右侧已选区 |
| 5 | 点击"保存配置"，输入名称"白银组合" | 配置保存，出现成功提示 |
| 6 | 点击"立即批量分析" | 对右侧已选标的执行分析 |

### 4.2 加载历史配置并追加

| 步骤 | 用户操作 | 界面响应 |
|------|----------|----------|
| 1 | 在配置选择器选择"白银组合" | 右侧自动填充该配置的标的 |
| 2 | 追加新标的到右侧 | 追加后点击"保存"可更新配置 |

### 4.3 Streamlit组件选择

| 组件 | 用途 |
|------|------|
| `st.selectbox` | 配置选择器（加载历史或新建） |
| `st.columns([2,1,2])` | 双栏布局（左2中1右2） |
| `st.multiselect` | 左侧标的列表（带搜索） |
| `st.data_editor` | 右侧已选展示（支持删除） |
| `st.text_input` | 配置名称输入 |
| `st.button` × 4 | 移动按钮 + 操作按钮 |

---

## 5. 后端实现

### 5.1 `FundSelectionManager` 核心方法

```python
class FundSelectionManager:
    """基金选择配置管理器"""

    def __init__(self, cache_dir: Path):
        self.config_dir = cache_dir / "fund_selections"
        self.config_index_file = self.config_dir / "configs.json"

    def list_configs(self) -> List[Dict]:
        """获取所有配置列表（元数据）"""

    def save_config(self, name: str, funds: List[Dict], overwrite: bool = False) -> bool:
        """保存配置

        Args:
            name: 配置名称
            funds: 基金列表 [{"code": "xxx", "name": "xxx", "type": "xxx"}]
            overwrite: 是否覆盖同名配置
        """

    def load_config(self, name: str) -> Optional[List[Dict]]:
        """加载指定配置的基金列表"""

    def delete_config(self, name: str) -> bool:
        """删除配置"""

    def append_to_config(self, name: str, new_funds: List[Dict]) -> bool:
        """追加基金到现有配置（自动去重）"""
```

### 5.2 集成到筛选流程

修改 `screen_and_analyze_with_mode` 函数，新增 `selected_funds` 参数：

```python
def screen_and_analyze_with_mode(
    _analyzer,
    criteria: Dict,
    top_n: int,
    scan_mode: str,
    selected_funds: Optional[List[Dict]] = None,  # 新增
    progress_callback = None
) -> List:
    """当 selected_funds 不为空时，只对选中的标的进行分析"""
```

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 配置名称已存在 | 提示用户选择"覆盖"或"另存为" |
| 配置文件损坏 | 从索引中移除，提示用户删除该配置 |
| 保存失败（磁盘满/权限） | 显示 `st.error`，日志记录详细错误 |
| 加载的基金代码失效 | 跳过失效代码，显示警告："跳过X个已失效的基金" |
| 右侧已选区为空 | 禁用"保存配置"和"立即分析"按钮 |

---

## 7. 缓存策略

| 数据类型 | 缓存方式 | TTL |
|----------|----------|-----|
| 基金列表（全部） | `@st.cache_data` - 原有 | 持久 |
| 配置元数据索引 | 内存缓存（session_state） | 会话级 |
| 单个配置详情 | 按需从文件读取 | 持久文件 |

---

## 8. 测试策略

### 8.1 单元测试 (`tests/test_fund_selection.py`)

- `test_save_new_config`
- `test_save_duplicate_config_without_overwrite`
- `test_save_duplicate_config_with_overwrite`
- `test_load_existing_config`
- `test_load_nonexistent_config`
- `test_append_to_config_dedup`
- `test_delete_config`
- `test_list_configs`
- `test_corrupted_config_index`

### 8.2 集成测试

- `test_save_and_load_config_workflow` - 保存→加载完整流程
- `test_append_funds_and_analyze` - 追加标的→批量分析

---

## 9. 实施清单

- [ ] 创建 `storage/fund_selection.py` - `FundSelectionManager` 类
- [ ] 修改 `ui/dashboard.py` - `render_abnormal_screening_page` 函数
  - [ ] 添加查询配置区域UI
  - [ ] 实现双栏穿梭框组件
  - [ ] 集成配置保存/加载/分析按钮
- [ ] 修改 `screen_and_analyze_with_mode` 函数 - 支持 `selected_funds` 参数
- [ ] 创建 `tests/test_fund_selection.py` - 单元测试
- [ ] 更新文档（如需要）
