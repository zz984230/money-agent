# Money-Agent - A 股 AI 投研竞技场

<div align="center">

**面向中国 A 股市场的 AI 投研辅助平台**

支持股票、ETF、可转债的多 AI 模型竞技分析

[![Python](https://img.shields.io/badge/Python-3.13.5-blue)](https://www.python.org/)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-purple)](https://github.com/astral-sh/uv)
[![GLM](https://img.shields.io/badge/AI-GLM--4.7-green)](https://open.bigmodel.cn/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 项目简介

Money-Agent 是一个基于人工智能的 A 股投研辅助平台，通过集成多个 AI 模型（目前支持 GLM-4.7），为投资者提供智能化的投资分析和决策支持。

平台采用现代化的 Python 技术栈，使用 UV 包管理器，结合 AKShare 数据源和 Streamlit Web 界面，为用户提供便捷、高效的投资研究工具。

### 核心特性

- **智能选股**: 基于财务指标（PE、PB、ROE、PS、股息率）进行股票筛选，AI 分析推荐优质标的
- **市场分析**: 分析大盘指数走势，评估市场情绪和趋势，支持上证指数、沪深300、中证500等主流指数
- **ETF 分析**: ETF 基金智能分析和推荐，覆盖宽基、行业、债券、商品、跨境等类别
- **可转债分析**: 可转债详细分析和双低策略筛选，帮助发现低估投资机会
- **多 AI 模型支持**: 架构设计支持接入多个 AI 模型进行竞技分析

---

## 功能特性

### 选股筛选

- 支持多种财务指标筛选：PE（市盈率）、PB（市净率）、ROE（净资产收益率）、PS（市销率）、股息率
- AI 智能分析筛选结果，提供投资建议
- 支持自定义筛选条件和返回数量

### 市场分析

- 支持主流指数分析：上证指数、沪深300、中证500、深证成指、创业板指
- 市场情绪评估和趋势预测
- 历史数据分析和可视化

### ETF 分析

- 单个 ETF 详细分析
- 按类别智能推荐 ETF
- 支持宽基、行业、债券、商品、跨境等类别

### 可转债分析

- 单个可转债详细分析
- 双低策略筛选（价格低、溢价率低）
- 自定义筛选参数（最大价格、最大溢价率、返回数量）

---

## 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **编程语言** | Python | 3.13.5 | 核心开发语言 |
| **包管理** | UV | 最新 | 快速、现代的 Python 包管理器 |
| **AI 模型** | GLM | 4.7 | 智谱 AI 的语言模型 |
| **数据源** | AKShare | 1.18.0+ | A 股金融数据获取 |
| **Web 框架** | Streamlit | 1.31.0+ | 快速构建数据应用 |
| **数据处理** | Pandas | 2.2.3+ | 数据分析和处理 |
| **数值计算** | NumPy | 2.1.0+ | 科学计算库 |
| **AI 框架** | LangChain | 0.3.0+ | AI 应用开发框架 |
| **配置管理** | Pydantic | 2.8.0+ | 数据验证和设置管理 |

---

## 安装

### 前置要求

- Python 3.10 或更高版本（推荐 3.13.5）
- UV 包管理器
- Git

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/money-agent.git
cd money-agent
```

#### 2. 安装 UV（如果尚未安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 3. 安装项目依赖

```bash
# 使用 UV 同步依赖
uv sync
```

#### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加您的 GLM API Key
# GLM_API_KEY=your_api_key_here
```

获取 GLM API Key: [智谱 AI 开放平台](https://open.bigmodel.cn/)

---

## 快速开始

### 启动 Streamlit 仪表板

#### Linux/macOS:

```bash
# 使用启动脚本
./run_ui.sh

# 或直接使用 streamlit
uv run streamlit run ui/dashboard.py
```

#### Windows:

```batch
# 使用启动脚本
run_ui.bat

# 或在命令行中运行
uv run streamlit run ui/dashboard.py
```

启动后，在浏览器中访问: `http://localhost:8501`

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并显示详细输出
uv run pytest -v

# 运行测试并生成覆盖率报告
uv run pytest --cov=. --cov-report=html
```

### 使用 Python 代码

```python
from analysis.screening import StockScreener
from analysis.market_analysis import MarketAnalyzer
from analysis.etf_analysis import ETFAnalyzer
from analysis.convertible_analysis import ConvertibleBondAnalyzer

# 选股筛选
screener = StockScreener()
criteria = {"pe": [10, 30], "roe": [15, 100]}
stocks = screener.screen_stocks(criteria)

# 市场分析
market_analyzer = MarketAnalyzer()
analysis = market_analyzer.analyze_index("000001", "上证指数")

# ETF 分析
etf_analyzer = ETFAnalyzer()
etf_analysis = etf_analyzer.analyze_etf("510300", "沪深300ETF")

# 可转债分析
cb_analyzer = ConvertibleBondAnalyzer()
cb_analysis = cb_analyzer.analyze_convertible("113050", "南航转债")
```

---

## 项目结构

```
money-agent/
├── core/                          # 核心模块
│   ├── agent/                     # AI Agent 模块
│   │   ├── base_agent.py          # AI Agent 抽象基类
│   │   ├── glm_agent.py           # GLM-4.7 Agent 实现
│   │   └── prompts.py             # 提示词构建器
│   └── __init__.py
├── data/                          # 数据相关
│   ├── fetchers/                  # 数据获取模块
│   │   └── akshare_fetcher.py     # AKShare 数据获取器
│   └── __init__.py
├── analysis/                      # 分析模块
│   ├── screening.py               # 股票筛选器
│   ├── market_analysis.py         # 市场分析器
│   ├── etf_analysis.py            # ETF 分析器
│   └── convertible_analysis.py    # 可转债分析器
├── config/                        # 配置管理
│   └── settings.py                # 配置管理模块
├── utils/                         # 工具模块
├── ui/                            # Web 界面
│   ├── dashboard.py               # Streamlit 主应用
│   └── README.md                  # UI 文档
├── tests/                         # 测试目录
│   ├── test_config.py             # 配置测试
│   ├── test_akshare_fetcher.py    # 数据获取测试
│   ├── test_glm_agent.py          # AI Agent 测试
│   ├── test_prompts.py            # 提示词测试
│   ├── test_screening.py          # 选股测试
│   ├── test_market_analysis.py    # 市场分析测试
│   ├── test_etf_analysis.py       # ETF 分析测试
│   ├── test_convertible_analysis.py  # 可转债分析测试
│   └── test_dashboard.py          # 仪表板测试
├── docs/                          # 文档目录
│   └── plans/                     # 计划文档
│       ├── 2026-01-27-ai-investment-agent-design.md
│       └── 2026-01-27-money-agent-implementation.md
├── .claude/                       # Claude Code 配置
│   └── schedule/
│       └── development-progress.md # 开发进度记录
├── pyproject.toml                 # UV 项目配置
├── uv.lock                        # 依赖锁文件
├── .python-version                # Python 版本
├── .env.example                   # 环境变量模板
├── .gitignore                     # Git 忽略规则
├── run_ui.sh                      # Linux/macOS 启动脚本
├── run_ui.bat                     # Windows 启动脚本
└── README.md                      # 项目说明
```

---

## 使用说明

### 环境变量配置

在 `.env` 文件中配置以下环境变量：

```bash
# GLM API 配置
GLM_API_KEY=your_api_key_here              # 必需：智谱 AI API Key
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4  # 可选：API 基础 URL
GLM_MODEL=glm-4-plus                       # 可选：使用的模型版本
```

### Streamlit 配置

可以通过命令行参数自定义 Streamlit 配置：

```bash
uv run streamlit run ui/dashboard.py \
    --server.port=8501 \           # 端口
    --server.address=localhost \   # 绑定地址
    --theme.base=light \           # 主题
    --browser.gatherUsageStats=false
```

### 功能页面说明

#### 1. 选股筛选页面

- 输入筛选条件（PE、PB、ROE、PS、股息率）
- 点击"开始筛选"按钮
- 查看 AI 分析结果和推荐股票

#### 2. 市场分析页面

- 选择要分析的指数
- 查看指数走势分析
- 查看市场情绪评估

#### 3. ETF 分析页面

- **单个 ETF 分析**: 输入 ETF 代码和名称
- **ETF 推荐**: 选择类别和推荐数量
- 查看分析结果和推荐列表

#### 4. 可转债分析页面

- **单个可转债分析**: 输入可转债代码和名称
- **双低策略筛选**: 设置最大价格、最大溢价率、返回数量
- 查看分析结果和筛选列表

---

## 开发指南

### 添加新功能

1. 在相应的模块中添加新功能
2. 编写单元测试
3. 运行测试确保通过
4. 更新文档

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解
- 编写文档字符串
- 保持测试覆盖率 > 80%

### 提交代码

```bash
# 添加变更
git add .

# 提交变更
git commit -m "feat: add new feature"

# 推送到远程仓库
git push origin develop
```

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_screening.py

# 运行特定测试用例
uv run pytest tests/test_screening.py::test_stock_screening_with_mock

# 查看测试覆盖率
uv run pytest --cov=. --cov-report=html
```

---

## 测试结果

当前测试套件包含 62 个测试用例：

- ✅ 58 个通过
- ⏭️ 4 个跳过（集成测试，需要真实 API Key）
- ⚠️ 6 个警告（依赖库的 DeprecationWarning）

测试覆盖：
- 配置管理
- 数据获取（AKShare）
- AI Agent（GLM）
- 提示词构建
- 选股筛选
- 市场分析
- ETF 分析
- 可转债分析
- Streamlit 仪表板

---

## 常见问题

### 1. 模块导入错误

**问题**: ImportError 或 ModuleNotFoundError

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/money-agent

# 重新安装依赖
uv sync

# 使用 uv run 运行脚本
uv run streamlit run ui/dashboard.py
```

### 2. API Key 错误

**问题**: GLM API Key 相关错误

**解决方案**:
- 确保在 `.env` 文件中正确设置了 `GLM_API_KEY`
- 检查 API Key 是否有效
- 确认 API Key 有足够的额度

### 3. 数据获取失败

**问题**: AKShare 数据获取失败

**解决方案**:
- 检查网络连接
- 确认 AKShare API 是否正常
- 稍后重试（可能是 API 限制）

### 4. Streamlit 缓存问题

**问题**: 数据或界面未更新

**解决方案**:
```bash
# 清除 Streamlit 缓存
rm -rf ~/.streamlit/cache

# 重启 Streamlit
uv run streamlit run ui/dashboard.py --server.runOnSave=false
```

---

## 路线图

### 已完成 (v0.1.0)

- ✅ 项目基础架构
- ✅ AKShare 数据获取模块
- ✅ GLM-4.7 AI Agent 框架
- ✅ 提示词工程模块
- ✅ 选股筛选模块
- ✅ 市场分析模块
- ✅ ETF 分析模块
- ✅ 可转债分析模块
- ✅ Streamlit 仪表板
- ✅ 完整测试套件
- ✅ UV 包管理迁移

### 计划中 (v0.2.0)

- ⏳ 支持更多 AI 模型（如 Claude、GPT）
- ⏳ 用户认证和权限管理
- ⏳ 投资组合跟踪
- ⏳ 历史分析记录
- ⏳ 回测功能
- ⏳ 移动端适配

### 未来展望 (v1.0.0)

- 🔮 多 AI 模型竞技
- 🔮 量化策略回测
- 🔮 实时行情推送
- 🔮 社区分享功能
- 🔮 云端部署

---

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'feat: add some amazing feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献规范

- 遵循现有的代码风格
- 编写清晰的提交信息
- 添加必要的测试
- 更新相关文档

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 致谢

- [AKShare](https://github.com/akfamily/akshare) - 提供 A 股金融数据接口
- [LangChain](https://github.com/langchain-ai/langchain) - AI 应用开发框架
- [Streamlit](https://streamlit.io/) - 快速构建数据应用的 Web 框架
- [智谱 AI](https://open.bigmodel.cn/) - 提供 GLM-4.7 AI 模型

---

## 联系方式

- 作者: zero
- 项目地址: [https://github.com/your-username/money-agent](https://github.com/your-username/money-agent)
- 问题反馈: [Issues](https://github.com/your-username/money-agent/issues)

---

## 更新日志

### v0.1.0 (2026-01-28)

- 完成核心功能开发
- 实现 Streamlit 仪表板
- 完成测试套件（62 个测试用例）
- 迁移到 UV 包管理
- 完善项目文档

### v0.0.5 (2026-01-27)

- 添加可转债分析模块
- 添加 ETF 分析模块
- 添加市场分析模块

### v0.0.1 (2026-01-26)

- 项目初始化
- 完成基础架构搭建

---

<div align="center">

**如果觉得这个项目有帮助，请给个 ⭐️ Star**

Made with ❤️ by [zero](https://github.com/your-username)

</div>
