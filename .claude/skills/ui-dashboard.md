---
name: money-agent-ui
description: Streamlit UI Dashboard for Money-Agent. Use when working with the Streamlit web interface, adding new pages, understanding caching patterns, or modifying dashboard components. Covers page structure, sidebar navigation, custom CSS, and analyzer integration.
---

# UI Dashboard Module

## Overview

The UI module provides a Streamlit-based web interface for all Money-Agent features. It uses caching for performance and organizes functionality into separate pages.

## Architecture

```
ui/
└── dashboard.py    # Main Streamlit application
```

## Application Structure

### Main Entry Point

```python
def main():
    # Initialize agent and analyzers (cached)
    agent = initialize_agent()
    screener, market_analyzer, etf_analyzer, cb_analyzer = get_analyzers(agent)

    # Sidebar navigation
    with st.sidebar:
        page = st.radio("选择功能", ["首页", "选股筛选", "市场分析", "ETF 分析", "可转债分析"])

    # Route to page renderers
    if page == "首页":
        render_home_page()
    elif page == "选股筛选":
        render_stock_screening_page(screener)
    # ... etc
```

## Caching Strategy

### Resource Caching (@st.cache_resource)

Used for expensive objects that should persist across reruns:

```python
@st.cache_resource
def initialize_agent():
    """Initialize AI Agent (cached to improve performance)"""
    try:
        agent = GLMAgent()
        return agent
    except Exception as e:
        st.error(f"初始化 AI Agent 失败: {str(e)}")
        return None
```

Use `@st.cache_resource` for:
- AI Agent instances
- Database connections
- Machine learning models

### Data Caching (@st.cache_data)

Used for data that changes infrequently:

```python
@st.cache_data
def get_analyzers(_agent):
    """Get analyzer instances (cached to improve performance)"""
    if _agent is None:
        return None, None, None, None
    screener = StockScreener(_agent)
    market_analyzer = MarketAnalyzer(_agent)
    etf_analyzer = ETFAnalyzer(_agent)
    cb_analyzer = ConvertibleBondAnalyzer(_agent)
    return screener, market_analyzer, etf_analyzer, cb_analyzer
```

Use `@st.cache_data` for:
- Analyzer instances
- Data fetch results
- Computed results

**Important**: Pass mutable dependencies (like `_agent`) with underscore prefix to avoid hash errors.

## Page Structure

Each page follows this pattern:

```python
def render_xxx_page(analyzer):
    """Render XXX analysis page"""

    # Page header
    st.markdown('<div class="sub-header">🔍 XXX 分析</div>', unsafe_allow_html=True)

    # Info box
    st.markdown('<div class="info-box">Description...</div>', unsafe_allow_html=True)

    # Input form
    with st.form("xxx_form"):
        # Input widgets
        submitted = st.form_submit_button("开始分析", use_container_width=True)

    # Process on submit
    if submitted:
        with st.spinner("AI 正在分析，请稍候..."):
            try:
                result = analyzer.analyze_xxx(...)
                # Display results
            except Exception as e:
                st.error(f"分析失败: {e}")
```

## Custom CSS Styles

Defined at top of dashboard.py:

```python
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1f77b4; }
    .sub-header { font-size: 1.5rem; color: #2c3e50; }
    .info-box { background: #f0f8ff; border-left: 4px solid #1f77b4; }
    .success-box { background: #d4edda; border-left: 4px solid #28a745; }
    .warning-box { background: #fff3cd; border-left: 4px solid #ffc107; }
    .error-box { background: #f8d7da; border-left: 4px solid #dc3545; }
</style>
""", unsafe_allow_html=True)
```

### Usage

```python
st.markdown('<div class="info-box">Message here</div>', unsafe_allow_html=True)
```

## Sidebar Components

### Navigation

```python
with st.sidebar:
    st.markdown("# 📈 A股投研竞技场")
    st.markdown("---")

    page = st.radio(
        "选择功能",
        ["首页", "选股筛选", "市场分析", "ETF 分析", "可转债分析"],
        label_visibility="collapsed"
    )
```

### System Status Indicators

```python
with st.sidebar:
    st.markdown("### 系统状态")

    if agent is not None:
        st.success("✅ AI Agent 已连接")
    else:
        st.error("❌ AI Agent 未连接")

    if screener is not None:
        st.success("✅ 选股模块就绪")
    else:
        st.error("❌ 选股模块未就绪")
```

## Page Examples

### Home Page

```python
def render_home_page():
    st.markdown('<div class="main-header">📈 A 股 AI 投研竞技场</div>', unsafe_allow_html=True)

    # Feature cards in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="选股筛选", value="AI 驱动", delta="智能推荐")
        st.info("基于财务指标进行股票筛选")

    # ... more columns
```

### Form Page Pattern

```python
def render_stock_screening_page(screener):
    with st.form("stock_screening_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            pe_max = st.number_input("PE 最大值", value=30.0, min_value=0.0)
            pb_max = st.number_input("PB 最大值", value=3.0, min_value=0.0)

        with col2:
            roe_min = st.number_input("ROE 最小值", value=15.0)
            ps_max = st.number_input("PS 最大值", value=5.0)

        with col3:
            top_n = st.slider("返回数量", min_value=1, max_value=20, value=10)

        submitted = st.form_submit_button("开始筛选", use_container_width=True)

    if submitted:
        # Process and display results
        result = screener.screen_stocks(criteria, top_n)

        if result["stocks"]:
            st.markdown(f'<div class="success-box">找到 {result["count"]} 只股票</div>', unsafe_allow_html=True)

            # Display as dataframe
            stocks_df = pd.DataFrame(result["stocks"])
            st.dataframe(stocks_df, use_container_width=True, hide_index=True)
```

### Tabbed Page Pattern

```python
def render_market_analysis_page(market_analyzer):
    tab1, tab2 = st.tabs(["指数分析", "市场情绪"])

    with tab1:
        with st.form("market_analysis_form"):
            index_code = st.selectbox("选择指数", [...])
            submitted = st.form_submit_button("开始分析")

        if submitted:
            result = market_analyzer.analyze_index(index_code, date)
            # Display results

    with tab2:
        st.info("点击按钮分析市场情绪")
        if st.button("分析市场情绪"):
            result = market_analyzer.analyze_sentiment()
            # Display results
```

## Adding New Pages

1. Create renderer function:

```python
def render_new_page(analyzer):
    st.markdown('<div class="sub-header">🆕 新功能</div>', unsafe_allow_html=True)

    with st.form("new_form"):
        # Input widgets
        submitted = st.form_submit_button("提交", use_container_width=True)

    if submitted:
        with st.spinner("处理中..."):
            try:
                result = analyzer.new_method(...)
                # Display results
            except Exception as e:
                st.markdown(f'<div class="error-box">错误: {e}</div>', unsafe_allow_html=True)
```

2. Add to sidebar:

```python
page = st.radio(
    "选择功能",
    ["首页", "选股筛选", "新功能", ...],  # Add new page
    label_visibility="collapsed"
)
```

3. Add routing in main():

```python
if page == "新功能":
    if analyzer is None:
        st.error("模块未初始化")
    else:
        render_new_page(analyzer)
```

## DataFrame Display

### Basic

```python
st.dataframe(df, use_container_width=True, hide_index=True)
```

### With Column Config

```python
st.dataframe(
    df,
    column_config={
        "symbol": st.column_config.TextColumn("代码", width="short"),
        "name": st.column_config.TextColumn("名称", width="medium"),
        "pe": st.column_config.NumberColumn("PE", format="%.2f")
    },
    use_container_width=True,
    hide_index=True
)
```

## Expander for Detailed Content

```python
with st.expander("查看完整分析报告", expanded=False):
    st.markdown("### AI 分析报告")
    st.markdown(result["analysis"])
```

## Running the Dashboard

```bash
# Direct
uv run streamlit run ui/dashboard.py

# With custom port
uv run streamlit run ui/dashboard.py --server.port=8502

# With theme
uv run streamlit run ui/dashboard.py --theme.base=dark
```

## Page Config

```python
st.set_page_config(
    page_title="A股 AI 投研竞技场",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

## Project Path Setup

```python
# Add project root to Python path
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

This ensures imports work correctly when running from the ui directory.
