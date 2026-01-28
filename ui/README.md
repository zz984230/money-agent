# Streamlit Dashboard

A 股 AI 投研竞技场的 Streamlit Web 界面。

## 功能特性

- **选股筛选**: 基于财务指标进行股票筛选，AI 分析推荐优质标的
- **市场分析**: 分析大盘指数走势，评估市场情绪和趋势
- **ETF 分析**: ETF 基金分析和智能推荐
- **可转债分析**: 可转债分析和双低策略筛选

## 快速开始

### 1. 环境配置

确保已设置 GLM API Key:

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑 .env 文件，设置您的 GLM_API_KEY
# GLM_API_KEY=your_api_key_here
```

### 2. 启动仪表板

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

### 3. 访问界面

启动后，在浏览器中访问: `http://localhost:8501`

## 配置选项

### Streamlit 配置

可以通过命令行参数自定义 Streamlit 配置:

```bash
uv run streamlit run ui/dashboard.py \
    --server.port=8501 \           # 端口
    --server.address=localhost \   # 绑定地址
    --theme.base=light \           # 主题
    --browser.gatherUsageStats=false
```

### 环境变量

在 `.env` 文件中配置:

```bash
# GLM API 配置
GLM_API_KEY=your_api_key_here
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4-plus
```

## 功能说明

### 选股筛选

支持基于以下指标进行筛选:

- **PE** (市盈率): 评估股票价值
- **PB** (市净率): 评估资产价值
- **ROE** (净资产收益率): 评估盈利能力
- **PS** (市销率): 评估销售收入
- **股息率**: 评估分红收益

### 市场分析

支持分析以下指数:

- 上证指数 (000001)
- 沪深300 (000300)
- 中证500 (000905)
- 深证成指 (399001)
- 创业板指 (399006)

### ETF 分析

- **单个 ETF 分析**: 输入 ETF 代码和名称进行详细分析
- **ETF 推荐**: 按类别智能推荐 ETF 基金

支持的类别:
- 宽基
- 行业
- 债券
- 商品
- 跨境

### 可转债分析

- **单个可转债分析**: 输入可转债代码和名称进行详细分析
- **双低策略筛选**: 筛选价格低、溢价率低的可转债

双低策略参数:
- 最大价格 (默认 110)
- 最大溢价率 (默认 30%)
- 返回数量 (默认 10)

## 项目结构

```
ui/
├── __init__.py          # 包初始化文件
├── dashboard.py         # Streamlit 主应用
└── README.md           # 本文档
```

## 技术栈

- **Web 框架**: Streamlit 1.31+
- **AI 模型**: GLM-4.7
- **数据源**: AKShare
- **开发工具**: Python 3.10+, UV

## 故障排除

### 1. 模块导入错误

如果出现模块导入错误，请确保在项目根目录运行:

```bash
cd /Users/zero/Project/money-agent
uv run streamlit run ui/dashboard.py
```

### 2. API Key 错误

确保 `.env` 文件中正确设置了 `GLM_API_KEY`:

```bash
GLM_API_KEY=your_actual_api_key_here
```

### 3. 数据获取失败

如果数据获取失败，可能是:
- 网络连接问题
- AKShare API 限制
- 数据源暂时不可用

请稍后重试。

### 4. Streamlit 缓存问题

如果遇到缓存问题，可以清除缓存:

```bash
# 清除 Streamlit 缓存
rm -rf ~/.streamlit/cache

# 或使用 --server.runOnSave=false 禁用缓存
uv run streamlit run ui/dashboard.py --server.runOnSave=false
```

## 开发说明

### 添加新功能

1. 在 `dashboard.py` 中添加新的页面函数
2. 在 `main()` 函数中添加导航选项
3. 使用 `@st.cache_resource` 或 `@st.cache_data` 优化性能

### 自定义样式

在 `dashboard.py` 中的 `<style>` 标签中修改 CSS:

```python
st.markdown("""
<style>
    /* 自定义 CSS */
</style>
""", unsafe_allow_html=True)
```

### 调试

启用调试模式:

```bash
uv run streamlit run ui/dashboard.py --logger.level=debug
```

## 性能优化

- 使用 `@st.cache_resource` 缓存资源密集型对象 (如 AI Agent)
- 使用 `@st.cache_data` 缓存数据计算结果
- 使用 `st.spinner` 显示加载状态
- 使用 `st.expander` 折叠大量内容

## 安全注意事项

- 不要在代码中硬编码 API Key
- 使用 `.env` 文件管理敏感信息
- 在生产环境中使用反向代理 (如 Nginx)
- 限制服务器访问地址 (`--server.address`)
- 启用 HTTPS (使用 SSL 证书)

## 许可证

本项目采用 MIT 许可证。详见项目根目录的 LICENSE 文件。

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
