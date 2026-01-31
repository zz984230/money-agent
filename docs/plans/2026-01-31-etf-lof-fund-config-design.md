# ETF/LOF 基金配置管理功能设计文档

**创建日期**: 2025-01-31
**作者**: Claude
**状态**: 设计阶段

## 1. 概述

### 1.1 背景

在ETF/LOF投机分析页面中，当前使用"缓存重新计算"模式时，用户只能通过下拉框（selectbox）单个查看缓存的基金列表，无法方便地：
- 整体浏览所有可用的标的
- 批量选择感兴趣的标的进行筛选
- 保存和复用常用的标的组合

### 1.2 目标

设计并实现一个**基金配置管理功能**，支持：
1. **优化展示效果**: 使用搜索+多选组合，大框展示所有标的
2. **配置管理**: 保存、加载、删除基金配置，支持版本追踪
3. **灵活使用**: 配置+手动混合模式，支持基于历史配置调整

### 1.3 用户价值

| 用户痛点 | 解决方案 |
|---------|---------|
| 无法整体查看300+只ETF | 大框列表展示，支持滚动浏览 |
| 每次手动勾选大量标的 | 保存配置，一键加载 |
| 无法追踪历史选择 | 版本管理，按时间线查看 |
| 无法基于已有配置调整 | 加载后可追加/删除，另存为新版本 |

## 2. 整体架构

### 2.1 组件架构

```
┌─────────────────────────────────────────────────────────┐
│                  UI层 (dashboard.py)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 搜索过滤区    │  │ 多选列表区    │  │ 配置操作区    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│            FundConfigManager (storage/fund_config_manager.py)│
│  - save_config()    - load_config()    - list_configs() │
│  - delete_config()  - merge_configs()  - validate()     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              配置文件存储 (storage/fund_configs/)        │
│  commodity/v20250131_160000.json                         │
│  overseas/v20250131_163000_白银精选.json                 │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心数据模型

```python
@dataclass
class FundItem:
    """基金标的项"""
    code: str    # 基金代码
    name: str    # 基金名称
    type: str    # 类型：'LOF' 或 'ETF'


@dataclass
class FundConfig:
    """基金配置"""
    id: str                      # 唯一ID（时间戳_备注）
    name: str                    # 配置名称/备注
    fund_type: str               # 'commodity' 或 'overseas'
    funds: List[FundItem]        # 基金列表
    created_at: str              # 创建时间（ISO格式）
    updated_at: str              # 更新时间（ISO格式）
    parent_id: Optional[str]     # 父配置ID（用于版本追踪）


@dataclass
class FundConfigMetadata:
    """配置元数据（用于列表展示）"""
    id: str
    name: str
    fund_type: str
    fund_count: int
    created_at: str
```

### 2.3 目录结构

```
storage/
  fund_configs/
    commodity/
      v20250131_160000.json
      v20250131_163000_白银精选.json
      v20250131_170000_白银精选_v2.json
    overseas/
      v20250131_161500.json
      v20250131_165000_科技组合.json
```

## 3. UI设计

### 3.1 主界面布局

```
┌──────────────────────────────────────────────────────────────┐
│  📋 基金池配置                           [加载配置▼] [保存配置]  │
├──────────────────────────────────────────────────────────────┤
│  🔍 搜索: [________________]  清除[X]    已选: 5/34 只        │
├──────────────────────────────────────────────────────────────┤
│  ┌─ 大宗商品LOF (34只) ──────────────────────────────────┐   │
│  │ ☑ 161226 - 国投白银LOF                    (搜索匹配)    │   │
│  │ ☐ 163415 - 白银LOF                                       │   │
│  │ ☐ 162411 - 华宝油气                                     │   │
│  │ ☐ 161116 - 有色金属LOF                                  │   │
│  │ ... (支持滚动显示)                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─ 海外ETF (302只) ───────────────────────────────────────┐   │
│  │ ☑ 513100 - 纳斯达克100                                  │   │
│  │ ☑ 513500 - 标普500                                      │   │
│  │ ☐ 159941 - 黄金ETF                                      │   │
│  │ ... (支持滚动显示)                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  [全选] [全不选] [反选]    清空所有选择                      │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 配置管理对话框

**保存配置对话框**：
```
┌─────────────────────────────────────────┐
│  保存配置                                │
├─────────────────────────────────────────┤
│  配置备注: [________________]  (可选)    │
│                                          │
│  当前已选: 7 只                          │
│  - 161226 国投白银LOF                    │
│  - 513100 纳斯达克100                    │
│  ...                                    │
│                                          │
│  [取消]              [保存]              │
└─────────────────────────────────────────┘
```

**加载配置对话框**：
```
┌─────────────────────────────────────────┐
│  加载历史配置                            │
├─────────────────────────────────────────┤
│  🔍 搜索: [________________]            │
│                                          │
│  配置列表:                               │
│  ┌───────────────────────────────────┐  │
│  │ v20250131_163000_白银精选        │  │
│  │ 2025-01-31 16:30 | 5只 commodity  │  │
│  │ [加载] [删除]                     │  │
│  ├───────────────────────────────────┤  │
│  │ v20250131_160000                   │  │
│  │ 2025-01-31 16:00 | 10只          │  │
│  │ [加载] [删除]                     │  │
│  └───────────────────────────────────┘  │
│                                          │
│  [取消]              [加载]              │
└─────────────────────────────────────────┘
```

### 3.3 交互细节

**搜索功能**：
- 实时过滤，支持代码、名称模糊搜索
- 高亮匹配关键词
- 搜索时自动展开对应分类

**多选功能**：
- 支持全选/全不选/反选
- 显示已选数量（如"已选: 5/34"）
- 标的显示顺序：已选的排在前面

**配置操作**：
- 加载配置时，自动勾选对应的标的
- 保存配置时，记录父配置ID（版本追踪）
- 删除配置前确认提示

## 4. 数据流与状态管理

### 4.1 Session State 结构

```python
# st.session_state 中的配置相关状态
st.session_state.fund_config = {
    # 当前选中的标的（代码列表）
    'selected_funds': {
        'commodity': ['161226', '163415'],
        'overseas': ['513100', '513500']
    },

    # 当前加载的配置ID（如果有）
    'loaded_config_id': 'v20250131_163000_白银精选',

    # 搜索关键词
    'search_query': '白银',

    # 展开状态
    'expanded_sections': ['commodity'],

    # 配置列表缓存
    'config_list': [],
}
```

### 4.2 核心数据流

**多选操作流程**：
```
用户搜索/多选
    ↓
更新 st.session_state.fund_config['selected_funds']
    ↓
UI 重新渲染（选中状态实时更新）
```

**保存配置流程**：
```
用户点击"保存配置"
    ↓
收集当前 selected_funds + 用户输入的备注
    ↓
FundConfigManager.save_config()
    ↓
生成配置ID (时间戳_备注)
    ↓
写入 JSON 文件到 storage/fund_configs/
    ↓
更新 loaded_config_id，显示成功提示
```

**加载配置流程**：
```
用户点击"加载配置"
    ↓
弹出配置列表对话框
    ↓
用户选择配置，点击"加载"
    ↓
FundConfigManager.load_config(config_id)
    ↓
读取 JSON 文件，解析基金列表
    ↓
更新 selected_funds + loaded_config_id
    ↓
UI 重新渲染，显示加载的标的为已选状态
```

**筛选执行流程**：
```
用户点击"开始筛选"
    ↓
检查是否有 selected_funds
    ↓
有自定义选择: 使用 selected_funds 构建筛选列表
无自定义选择: 使用完整缓存列表
    ↓
调用 screen_and_analyze_with_mode(selected_funds=target_list)
```

## 5. API设计

### 5.1 FundConfigManager 类

```python
class FundConfigManager:
    """基金配置管理器"""

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置存储目录，默认为 storage/fund_configs/
        """
        self.config_dir = config_dir or Path(__file__).parent / "fund_configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self, config: FundConfig) -> bool:
        """
        保存配置到文件

        Args:
            config: FundConfig 对象

        Returns:
            是否保存成功
        """

    def load_config(self, config_id: str, fund_type: str) -> Optional[FundConfig]:
        """
        加载配置

        Args:
            config_id: 配置ID
            fund_type: 基金类型 ('commodity' 或 'overseas')

        Returns:
            FundConfig 对象，不存在时返回 None
        """

    def list_configs(self, fund_type: str) -> List[FundConfigMetadata]:
        """
        列出指定类型的所有配置

        Args:
            fund_type: 基金类型

        Returns:
            配置元数据列表（按创建时间倒序）
        """

    def delete_config(self, config_id: str, fund_type: str) -> bool:
        """
        删除配置

        Args:
            config_id: 配置ID
            fund_type: 基金类型

        Returns:
            是否删除成功
        """

    def merge_configs(self, config_ids: List[str], fund_type: str) -> FundConfig:
        """
        合并多个配置（去重）

        Args:
            config_ids: 配置ID列表
            fund_type: 基金类型

        Returns:
            合并后的新配置
        """

    def validate_config(self, config: FundConfig, available_funds: List[Dict]) -> Tuple[bool, List[str]]:
        """
        验证配置（检查基金代码是否有效）

        Args:
            config: 待验证的配置
            available_funds: 当前可用的基金列表

        Returns:
            (是否有效, 失效的基金代码列表)
        """
```

### 5.2 筛选逻辑调整

修改 `screen_and_analyze_with_mode()` 函数签名：

```python
def screen_and_analyze_with_mode(
    _analyzer,
    criteria: Dict,
    top_n: int,
    scan_mode: str,
    progress_callback: Optional[Callable] = None,
    selected_funds: Optional[List[Dict]] = None  # 新增参数
) -> List:
    """
    根据筛选模式执行分析

    Args:
        _analyzer: LOFETFGambleAnalyzer实例
        criteria: 筛选条件
        top_n: 返回数量
        scan_mode: 'use_cache'（使用缓存）或 'rescan'（重新扫描）
        progress_callback: 进度回调函数
        selected_funds: 用户手动选择的标的列表（新增）

    Returns:
        分析结果列表
    """
    if selected_funds and len(selected_funds) > 0:
        target_list = selected_funds  # 使用用户选择的标的
    else:
        # 原有逻辑：获取完整缓存列表
        ...
```

## 6. 错误处理与边界情况

### 6.1 异常处理场景

| 场景 | 处理方式 |
|------|----------|
| 配置文件损坏 | 显示警告，提供从备份恢复或删除的选项 |
| 存储目录权限问题 | 显示错误，回退到内存模式 |
| 基金代码失效 | 加载时警告，高亮显示失效标的，提供移除选项 |
| 选择的标的过多(>200) | 显示提示，用户确认后继续 |
| 并发保存冲突 | 自动添加序号后缀 |

### 6.2 边界情况

| 场景 | 处理方式 |
|------|----------|
| 配置列表为空 | 显示提示："暂无保存的配置" |
| 搜索无结果 | 显示："未找到匹配的标的" |
| 已选标的为空 | 禁用"开始筛选"，提示至少选择一只 |
| 配置名称重复 | 自动添加序号："白银精选 (2)" |
| 删除最后一个配置 | 确认后删除，返回默认状态 |

### 6.3 用户反馈机制

```
成功操作:
- ✅ 保存成功: "配置已保存为 v20250131_163000_白银精选"
- ✅ 加载成功: "已加载配置，共 5 只标的"
- ✅ 删除成功: "配置已删除"

警告提示:
- ⚠️ 部分标的失效: "3 只标的已失效，已自动移除"
- ⚠️ 配置已存在: "同名配置已存在，将创建新版本"

错误提示:
- ❌ 保存失败: "保存配置失败: {error}"
- ❌ 加载失败: "配置文件损坏或不存在"
```

## 7. 测试计划

### 7.1 单元测试

**文件**: `tests/test_fund_config_manager.py`

```python
def test_save_config():
    """测试保存配置"""

def test_load_config():
    """测试加载配置"""

def test_list_configs():
    """测试列出的配置"""

def test_merge_configs():
    """测试合并配置"""

def test_delete_config():
    """测试删除配置"""

def test_validate_config():
    """测试配置验证"""
```

### 7.2 UI集成测试

**文件**: `tests/test_dashboard_fund_config.py`

```python
def test_search_and_select():
    """测试搜索和多选功能"""

def test_save_config_flow():
    """测试保存配置流程"""

def test_load_config_flow():
    """测试加载配置流程"""

def test_empty_config_handling():
    """测试空配置处理"""

def test_large_scale_selection():
    """测试大规模选择（200+只）"""
```

## 8. 实施步骤

### Phase 1: 核心功能 (优先)
1. 创建 `storage/fund_config_manager.py`
2. 实现 `FundConfig` 和 `FundItem` 数据类
3. 实现 `save_config()`, `load_config()`, `list_configs()`, `delete_config()`
4. 编写单元测试

### Phase 2: UI组件
5. 修改 `render_abnormal_screening_page()`
6. 实现搜索+多选组合组件
7. 实现配置保存/加载对话框
8. 调整 `screen_and_analyze_with_mode()` 支持 `selected_funds`

### Phase 3: 增强功能
9. 实现配置合并功能
10. 添加配置版本追踪
11. 实现失效标的检测和提示
12. 编写集成测试

### Phase 4: 优化与文档
13. 性能优化（虚拟滚动、懒加载）
14. 编写用户文档
15. 代码审查和重构

### 8.1 文件变更清单

```
新增文件:
  storage/fund_config_manager.py       # 配置管理器
  storage/fund_configs/                # 配置存储目录
    commodity/*.json
    overseas/*.json
  tests/test_fund_config_manager.py    # 单元测试

修改文件:
  ui/dashboard.py                      # UI组件
  analysis/etf_lof_gamble.py           # 筛选逻辑调整
```

## 9. 技术约束

- 使用 Streamlit `st.data_editor` 或类似组件实现多选
- 配置文件使用 JSON 格式存储
- 兼容现有的 `@st.cache_data` 缓存机制
- 不影响现有的筛选功能

## 10. 未来扩展

- 配置分享功能（导出/导入配置文件）
- 配置市场（社区配置分享）
- 基于历史表现的配置推荐
- 配置A/B测试功能
