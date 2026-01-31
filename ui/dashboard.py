"""
Streamlit Dashboard for Money-Agent
A股 AI 投研竞技场 - Streamlit 仪表板
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
from typing import List, Dict, Callable, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent.modelscope_agent import ModelScopeAgent
from analysis.screening import StockScreener
from analysis.market_analysis import MarketAnalyzer
from analysis.etf_analysis import ETFAnalyzer
from analysis.convertible_technical_analysis import (
    ConvertibleBondTechnicalAnalyzer,
    TechnicalAnalysisResult
)
from analysis.etf_lof_gamble import LOFETFGambleAnalyzer
from storage.analysis_history import AnalysisHistoryEntry
from storage.fund_selection import FundSelectionManager

# 基金配置UI常量
NEW_CONFIG_OPTION = "-- 新建配置 --"

# 页面配置
st.set_page_config(
    page_title="A股 AI 投研竞技场",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f8ff;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_agent():
    """初始化 AI Agent（缓存以提高性能）"""
    try:
        agent = ModelScopeAgent()
        return agent
    except Exception as e:
        st.error(f"初始化 AI Agent 失败: {str(e)}")
        st.error("请确保已设置 MODELSCOPE_API_KEY 环境变量")
        return None


@st.cache_resource
def get_analyzers(_agent):
    """获取分析器实例（缓存以提高性能）"""
    if _agent is None:
        return None, None, None, None, None

    try:
        screener = StockScreener(_agent)
        market_analyzer = MarketAnalyzer(_agent)
        etf_analyzer = ETFAnalyzer(_agent)
        cb_technical_analyzer = ConvertibleBondTechnicalAnalyzer(_agent)
        gamble_analyzer = LOFETFGambleAnalyzer(_agent)
        return screener, market_analyzer, etf_analyzer, cb_technical_analyzer, gamble_analyzer
    except Exception as e:
        st.error(f"初始化分析器失败: {str(e)}")
        return None, None, None, None, None


def render_home_page():
    """渲染首页"""
    st.markdown('<div class="main-header">📈 A 股 AI 投研竞技场</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <h3>欢迎使用 A 股 AI 投研竞技场平台！</h3>
        <p>本平台基于 GLM-4.7 AI 模型，提供专业的 A 股市场投资研究工具。</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="选股筛选", value="AI 驱动", delta="智能推荐")
        st.info("基于财务指标进行股票筛选，AI 分析推荐优质标的")

    with col2:
        st.metric(label="市场分析", value="大盘指数", delta="实时监控")
        st.info("分析主要指数走势，评估市场情绪和趋势")

    with col3:
        st.metric(label="ETF 分析", value="基金筛选", delta="资产配置")
        st.info("ETF 基金分析和推荐，辅助资产配置决策")

    with col4:
        st.metric(label="可转债", value="技术面", delta="深度分析")
        st.info("可转债技术面分析，基于价格和成交量等指标")

    st.markdown("---")

    st.markdown("""
    ### 平台特色

    - **AI 驱动**：基于 GLM-4.7 大模型，提供专业的投资分析
    - **多维分析**：覆盖股票、ETF、可转债等多个投资品种
    - **实时数据**：通过 AKShare 获取最新市场数据
    - **智能推荐**：AI 智能筛选和推荐投资标的
    - **策略工具**：提供双低策略等经典投资策略工具

    ### 使用说明

    1. 在左侧选择功能模块
    2. 输入相应的查询条件
    3. 点击分析按钮获取 AI 报告
    4. 查看分析结果和投资建议

    ### 技术栈

    - **AI 模型**：GLM-4.7 (智谱 AI)
    - **数据源**：AKShare
    - **Web 框架**：Streamlit
    - **开发工具**：Python 3.10+, UV
    """)


def render_stock_screening_page(screener):
    """渲染选股筛选页面"""
    st.markdown('<div class="sub-header">🔍 选股筛选</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        基于财务指标进行股票筛选，AI 将为您分析推荐符合条件的优质标的。
    </div>
    """, unsafe_allow_html=True)

    with st.form("stock_screening_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            pe_max = st.number_input("PE（市盈率）最大值", value=30.0, min_value=0.0, step=1.0, help="市盈率越低，股票越便宜")
            pb_max = st.number_input("PB（市净率）最大值", value=3.0, min_value=0.0, step=0.1, help="市净率越低，估值越低")

        with col2:
            roe_min = st.number_input("ROE（净资产收益率）最小值 (%)", value=15.0, min_value=0.0, max_value=100.0, step=1.0, help="ROE 越高，盈利能力越强")
            ps_max = st.number_input("PS（市销率）最大值", value=5.0, min_value=0.0, step=0.1, help="市销率越低，估值越低")

        with col3:
            dividend_min = st.number_input("股息率最小值 (%)", value=2.0, min_value=0.0, max_value=20.0, step=0.5, help="股息率越高，分红收益越高")
            top_n = st.slider("返回股票数量", min_value=1, max_value=20, value=10, help="最多返回的股票数量")

        submitted = st.form_submit_button("开始筛选", use_container_width=True)

    if submitted:
        # 构建筛选条件
        criteria = {}
        if pe_max > 0:
            criteria["pe"] = {"max": pe_max}
        if pb_max > 0:
            criteria["pb"] = {"max": pb_max}
        if roe_min > 0:
            criteria["roe"] = {"min": roe_min}
        if ps_max > 0:
            criteria["ps"] = {"max": ps_max}
        if dividend_min > 0:
            criteria["dividend_yield"] = {"min": dividend_min}

        if not criteria:
            st.error("请至少设置一个筛选条件！")
            return

        # 显示筛选条件
        st.markdown("### 筛选条件")
        criteria_df = pd.DataFrame([
            {"指标": "PE 最大值", "值": f"≤ {pe_max}"},
            {"指标": "PB 最大值", "值": f"≤ {pb_max}"},
            {"指标": "ROE 最小值", "值": f"≥ {roe_min}%"},
            {"指标": "PS 最大值", "值": f"≤ {ps_max}"},
            {"指标": "股息率最小值", "值": f"≥ {dividend_min}%"},
        ])
        st.dataframe(criteria_df, use_container_width=True, hide_index=True)

        # 执行筛选
        with st.spinner("AI 正在筛选股票，请稍候..."):
            try:
                result = screener.screen_stocks(criteria, top_n)

                if result["stocks"]:
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>筛选完成！找到 {result['count']} 只符合条件的股票</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    # 显示股票列表
                    stocks_df = pd.DataFrame(result["stocks"])
                    st.markdown("### 筛选结果")
                    st.dataframe(
                        stocks_df[["symbol", "name", "pe", "roe"]],
                        column_config={
                            "symbol": st.column_config.TextColumn("股票代码", width="medium"),
                            "name": st.column_config.TextColumn("股票名称", width="medium"),
                            "pe": st.column_config.NumberColumn("PE", format="%.2f"),
                            "roe": st.column_config.NumberColumn("ROE (%)", format="%.2f")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                    # 显示 AI 分析
                    with st.expander("查看 AI 分析详情", expanded=False):
                        st.markdown("### AI 分析报告")
                        st.markdown(result["reasoning"])
                else:
                    st.markdown("""
                    <div class="warning-box">
                        <h4>未找到符合条件的股票</h4>
                        <p>请尝试调整筛选条件...</p>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                    <h4>筛选失败</h4>
                    <p>错误信息: {str(e)}</p>
                </div>
                """, unsafe_allow_html=True)


def render_market_analysis_page(market_analyzer):
    """渲染市场分析页面"""
    st.markdown('<div class="sub-header">📊 市场分析</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        分析大盘指数走势，评估市场情绪和趋势，为投资决策提供参考。
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["指数分析", "市场情绪"])

    with tab1:
        with st.form("market_analysis_form"):
            col1, col2 = st.columns(2)

            with col1:
                index_code = st.selectbox(
                    "选择指数",
                    options=["000001", "000300", "000905", "399001", "399006"],
                    format_func=lambda x: {
                        "000001": "上证指数",
                        "000300": "沪深300",
                        "000905": "中证500",
                        "399001": "深证成指",
                        "399006": "创业板指"
                    }.get(x, x),
                    index=0
                )

            with col2:
                # 默认日期为昨天
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                analysis_date = st.date_input("分析日期", value=datetime.strptime(yesterday, "%Y-%m-%d"))

            submitted = st.form_submit_button("开始分析", use_container_width=True)

        if submitted:
            date_str = analysis_date.strftime("%Y-%m-%d")

            with st.spinner("AI 正在分析市场，请稍候..."):
                try:
                    result = market_analyzer.analyze_index(index_code, date_str)

                    if result:
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>分析完成！</h4>
                            <p>指数代码: {result['index_code']}</p>
                            <p>分析日期: {result['date']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # 显示指数数据
                        if result["data"]:
                            st.markdown("### 指数数据")
                            data_df = pd.DataFrame([result["data"]])
                            st.dataframe(data_df, use_container_width=True, hide_index=True)

                        # 显示分析摘要
                        if result["summary"]:
                            st.markdown("### 分析摘要")
                            st.info(result["summary"])

                        # 显示完整分析
                        with st.expander("查看完整分析报告", expanded=True):
                            st.markdown("### AI 分析报告")
                            st.markdown(result["analysis"])
                    else:
                        st.markdown("""
                        <div class="warning-box">
                            <h4>分析失败</h4>
                            <p>未能获取到该指数的数据，请检查日期是否正确...</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>分析出错</h4>
                        <p>错误信息: {str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### 市场情绪分析")
        st.info("点击下方按钮分析当前市场情绪")

        if st.button("分析市场情绪", use_container_width=True):
            with st.spinner("AI 正在分析市场情绪，请稍候..."):
                try:
                    result = market_analyzer.analyze_sentiment()

                    if result:
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>情绪分析完成！</h4>
                            <p>分析时间: {result['timestamp']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("### 情绪分析报告")
                        st.markdown(result["sentiment"])
                    else:
                        st.markdown("""
                        <div class="warning-box">
                            <h4>分析失败</h4>
                            <p>未能获取到市场数据，请稍后重试...</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>分析出错</h4>
                        <p>错误信息: {str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)


def render_etf_analysis_page(etf_analyzer):
    """渲染 ETF 分析页面"""
    st.markdown('<div class="sub-header">💰 ETF 分析</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        ETF 基金分析和推荐，辅助资产配置决策。支持单个 ETF 分析和智能推荐。
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["ETF 分析", "ETF 推荐"])

    with tab1:
        with st.form("etf_analysis_form"):
            col1, col2 = st.columns(2)

            with col1:
                etf_code = st.text_input("ETF 代码", value="510300", max_chars=6, help="6位数字代码，如 510300")

            with col2:
                etf_name = st.text_input("ETF 名称", value="沪深300ETF", help="如沪深300ETF")

            submitted = st.form_submit_button("开始分析", use_container_width=True)

        if submitted:
            if not etf_code or not etf_name:
                st.error("请输入 ETF 代码和名称！")
                return

            with st.spinner("AI 正在分析 ETF，请稍候..."):
                try:
                    result = etf_analyzer.analyze_etf(etf_code, etf_name)

                    if result:
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>分析完成！</h4>
                            <p>ETF 代码: {result['etf_code']}</p>
                            <p>ETF 名称: {result['etf_name']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # 显示 ETF 数据
                        if result["data"]:
                            st.markdown("### ETF 数据")
                            data_df = pd.DataFrame([result["data"]])
                            st.dataframe(data_df, use_container_width=True, hide_index=True)

                        # 显示分析摘要
                        if result["summary"]:
                            st.markdown("### 分析摘要")
                            st.info(result["summary"])

                        # 显示完整分析
                        with st.expander("查看完整分析报告", expanded=True):
                            st.markdown("### AI 分析报告")
                            st.markdown(result["analysis"])
                    else:
                        st.markdown("""
                        <div class="warning-box">
                            <h4>分析失败</h4>
                            <p>未能获取到该 ETF 的数据，请检查代码是否正确...</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>分析出错</h4>
                        <p>错误信息: {str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### ETF 智能推荐")

        with st.form("etf_recommend_form"):
            category = st.selectbox(
                "ETF 类别",
                options=["宽基", "行业", "债券", "商品", "跨境"],
                index=0
            )
            top_n = st.slider("推荐数量", min_value=1, max_value=10, value=5)

            submitted = st.form_submit_button("获取推荐", use_container_width=True)

        if submitted:
            with st.spinner("AI 正在为您推荐 ETF，请稍候..."):
                try:
                    result = etf_analyzer.recommend_etfs(category, top_n)

                    if result and len(result) > 0:
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>推荐完成！为您推荐 {len(result)} 只 {category} 类 ETF</h4>
                        </div>
                        """, unsafe_allow_html=True)

                        # 显示推荐列表
                        result_df = pd.DataFrame(result)
                        st.markdown("### 推荐列表")
                        st.dataframe(
                            result_df[["etf_code", "etf_name", "category"]],
                            column_config={
                                "etf_code": st.column_config.TextColumn("代码", width="short"),
                                "etf_name": st.column_config.TextColumn("名称", width="medium"),
                                "category": st.column_config.TextColumn("类别", width="short")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.markdown(f"""
                        <div class="warning-box">
                            <h4>未找到推荐</h4>
                            <p>未找到 {category} 类别的 ETF，请尝试其他类别...</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>推荐出错</h4>
                        <p>错误信息: {str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)


def render_convertible_analysis_page(cb_technical_analyzer, agent=None):
    """渲染可转债分析页面（包含子菜单）"""
    st.markdown('<div class="sub-header">🎫 可转债分析</div>', unsafe_allow_html=True)

    # 子菜单导航（使用tabs实现）
    tab1, tab2 = st.tabs(["分析概览", "量化因子"])

    with tab1:
        render_convertible_overview_page(cb_technical_analyzer)

    with tab2:
        render_convertible_factors_page(agent)


@st.cache_data(ttl=3600)
def get_cached_industries(_fetcher):
    """缓存行业列表数据（1小时）"""
    return _fetcher.get_industry_list()


@st.cache_data(ttl=1800)
def get_cached_convertible_by_industry(_fetcher, industry_name):
    """缓存行业转债映射（30分钟）"""
    return _fetcher.get_convertible_by_industry(industry_name)


def render_convertible_factors_page(agent):
    """渲染可转债量化因子页面"""

    st.markdown("""
    <div class="info-box">
        可转债中期量化分析，基于行业趋势自上而下筛选优质标的。
        <br><small>支持快速筛选和行业探索两种模式。</small>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["快速筛选", "行业探索"])

    with tab1:
        render_medium_term_quick_screen(agent)

    with tab2:
        render_medium_term_industry_explore()


def render_medium_term_quick_screen(agent):
    """渲染中期量化快速筛选页面"""
    st.subheader("快速筛选")

    # 检查agent是否可用
    if agent is None:
        st.warning("⚠️ AI Agent 未连接，数据筛选功能可用，但AI分析将不可用")

    # 筛选参数配置
    with st.form("medium_term_screen_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            top_n_industries = st.slider(
                "强势行业数量",
                min_value=3,
                max_value=10,
                value=5,
                help="筛选出的强势行业数量"
            )

        with col2:
            top_n_bonds = st.slider(
                "每行业转债数量",
                min_value=3,
                max_value=10,
                value=5,
                help="每个行业返回的转债数量"
            )

        with col3:
            premium_max = st.slider(
                "溢价率上限(%)",
                min_value=0,
                max_value=50,
                value=20,
                help="只显示溢价率低于此值的转债"
            )

        with col4:
            bond_type = st.selectbox(
                "转债类型",
                options=["全部", "偏股型", "平衡型", "偏债型"],
                index=0,
                help="筛选指定类型的转债"
            )

        enable_signals = st.checkbox("启用止盈止损提醒", value=True)

        submitted = st.form_submit_button("开始筛选", use_container_width=True)

    if submitted:
        # 如果没有agent，先创建一个用于数据筛选（AI分析会失败）
        if agent is None:
            try:
                from core.agent.base_agent import BaseAgent
                from unittest.mock import Mock

                # 创建一个mock agent用于数据筛选
                agent = Mock()
                agent.chat = Mock(return_value="AI分析暂不可用（未配置API Key）")
            except Exception as e:
                st.error(f"无法初始化分析器: {str(e)}")
                return

        try:
            from analysis.convertible_medium_term import ConvertibleBondMediumTermAnalyzer
            from data.fetchers.akshare_fetcher import AKShareFetcher

            # 创建fetcher实例
            fetcher = AKShareFetcher()

            # 使用缓存函数替换fetcher方法
            original_get_industry_list = fetcher.get_industry_list
            original_get_convertible_by_industry = fetcher.get_convertible_by_industry

            fetcher.get_industry_list = lambda: get_cached_industries(fetcher)
            fetcher.get_convertible_by_industry = lambda name: get_cached_convertible_by_industry(fetcher, name)

            analyzer = ConvertibleBondMediumTermAnalyzer(agent)
            analyzer.fetcher = fetcher  # 使用带缓存的fetcher

            # 执行筛选
            with st.spinner("正在筛选，请稍候..."):
                bond_type_filter = None if bond_type == "全部" else bond_type

                result = analyzer.medium_term_screen(
                    top_n_industries=top_n_industries,
                    top_n_bonds=top_n_bonds,
                    premium_max=premium_max,
                    bond_type_filter=bond_type_filter
                )

            if result and result.bonds:
                # 显示筛选摘要
                st.success(f"筛选完成！识别出 {len(result.industries)} 个强势行业，共 {len(result.bonds)} 只转债")

                # 视图切换
                view_mode = st.radio(
                    "展示视图",
                    options=["按行业分组", "统一排名"],
                    horizontal=True
                )

                if view_mode == "按行业分组":
                    render_grouped_view(result, enable_signals)
                else:
                    render_ranked_view(result, enable_signals)

                # AI分析
                if result.ai_analysis:
                    with st.expander("查看AI投资建议", expanded=True):
                        st.markdown(result.ai_analysis)

            else:
                st.warning("未找到符合条件的转债，请尝试调整筛选条件")

        except Exception as e:
            st.error(f"筛选失败: {str(e)}")


def render_medium_term_industry_explore():
    """渲染行业探索页面"""
    st.subheader("行业探索")

    st.info("行业探索功能开发中，敬请期待...")

    # TODO: 实现行业排行榜和点击展开功能


def render_grouped_view(result, enable_signals):
    """渲染按行业分组的视图"""
    # 按行业分组
    from collections import defaultdict
    grouped = defaultdict(list)
    for bond in result.bonds:
        grouped[bond['industry']].append(bond)

    for industry in result.industries:
        bonds = grouped.get(industry.industry_name, [])
        if not bonds:
            continue

        with st.expander(
            f"📊 {industry.industry_name} "
            f"(相对强弱: {industry.relative_strength:.1f}%, "
            f"行业排名: {result.industries.index(industry)+1}/{len(result.industries)})"
        ):
            # 显示该行业的转债
            for bond in bonds:
                signals = []
                if enable_signals:
                    if bond.get('score', 0) > 70:
                        signals.append("✅强")
                    if bond['premium_rate'] > 15:
                        signals.append("⚠️溢价高")

                signal_text = " ".join(signals) if signals else ""

                st.markdown(
                    f"**{bond['cb_name']}** ({bond['cb_code']}) - "
                    f"溢价率 {bond['premium_rate']:.1f}% - "
                    f"评分 {bond['score']:.1f} {signal_text}"
                )


def render_ranked_view(result, enable_signals):
    """渲染统一排名视图"""
    import pandas as pd

    df = pd.DataFrame(result.bonds)

    # 添加信号列
    if enable_signals:
        df['信号'] = df.apply(
            lambda row: "✅强势" if row['score'] > 70 else ("⚠️关注" if row['score'] > 60 else ""),
            axis=1
        )

    st.dataframe(
        df[['cb_code', 'cb_name', 'industry', 'premium_rate', 'bond_type', 'score', '信号']] if enable_signals
        else df[['cb_code', 'cb_name', 'industry', 'premium_rate', 'bond_type', 'score']],
        column_config={
            "cb_code": st.column_config.TextColumn("代码", width="short"),
            "cb_name": st.column_config.TextColumn("名称", width="medium"),
            "industry": st.column_config.TextColumn("行业", width="medium"),
            "premium_rate": st.column_config.NumberColumn("溢价率", format="%.1f"),
            "bond_type": st.column_config.TextColumn("类型", width="short"),
            "score": st.column_config.NumberColumn("评分", format="%.1f"),
            "信号": st.column_config.TextColumn("信号", width="short")
        },
        use_container_width=True,
        hide_index=True
    )


def render_convertible_overview_page(cb_technical_analyzer):
    """渲染可转债分析概览页面（技术面分析）"""
    st.markdown("""
    <div class="info-box">
        可转债技术面分析，基于价格、成交量、技术指标等数据进行深度分析。
        <br><small>支持单券详细分析和批量技术面筛选。</small>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["单券分析", "技术面筛选"])

    with tab1:
        st.subheader("单券技术面分析")

        col1, col2 = st.columns([2, 1])

        with col1:
            cb_name = st.text_input(
                "转债名称",
                placeholder="如利民转债",
                help="输入可转债名称，支持模糊匹配",
                key="technical_cb_name"
            )

        with col2:
            st.write("")  # 占位
            analyze_btn = st.button("开始分析", type="primary", key="technical_analyze_btn")

        if analyze_btn and cb_name:
            with st.spinner("正在分析..."):
                try:
                    result = cb_technical_analyzer.analyze_technical(cb_name)

                    if result:
                        # 显示基础信息
                        st.success(f"分析完成：{result.technical_data.cb_name}")

                        # 基础信息卡片
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("当前价格", f"{result.technical_data.price:.2f}元")
                        with col2:
                            st.metric("涨跌幅", f"{result.technical_data.change_percent:.2f}%")
                        with col3:
                            st.metric("溢价率", f"{result.technical_data.premium_rate:.2f}%")
                        with col4:
                            # 显示信号类型
                            signal_type = "技术面"
                            if result.signals and isinstance(result.signals, list) and len(result.signals) > 0:
                                signal_type = result.signals[0] if len(result.signals[0]) < 10 else "技术信号"
                            st.metric("类型", signal_type)

                        # AI分析结果
                        st.subheader("AI分析")
                        st.markdown(result.analysis)

                        # 投资建议
                        if result.recommendation:
                            st.info(f"💡 投资建议：{result.recommendation}")
                    else:
                        st.error("分析失败，请检查转债代码或稍后重试")
                except Exception as e:
                    st.error(f"分析出错：{str(e)}")

    with tab2:
        st.subheader("技术面筛选")

        col1, col2, col3 = st.columns(3)

        with col1:
            price_min = st.number_input("最低价格", value=90, min_value=0, max_value=300, key="screen_price_min")
            price_max = st.number_input("最高价格", value=110, min_value=0, max_value=300, key="screen_price_max")

        with col2:
            premium_max = st.number_input("最大溢价率(%)", value=30, min_value=0, max_value=100, key="screen_premium_max")

        with col3:
            top_n = st.number_input("返回数量", value=20, min_value=1, max_value=100, key="screen_top_n")

        if st.button("开始筛选", key="screen_start_btn"):
            with st.spinner("正在筛选..."):
                try:
                    criteria = {
                        "price_range": (price_min, price_max),
                        "premium_max": premium_max,
                    }

                    results = cb_technical_analyzer.screen_by_technical(criteria, top_n=top_n)

                    if results and len(results) > 0:
                        st.success(f"筛选完成，找到 {len(results)} 只转债")

                        # 转换为DataFrame显示
                        results_df = pd.DataFrame(results)

                        st.dataframe(
                            results_df[['cb_code', 'cb_name', 'price', 'premium', 'score']],
                            column_config={
                                "cb_code": "代码",
                                "cb_name": "名称",
                                "price": st.column_config.NumberColumn("价格", format="%.2f"),
                                "premium": st.column_config.NumberColumn("溢价率", format="%.2f"),
                                "score": st.column_config.NumberColumn("评分", format="%.2f")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.warning("未找到符合条件的转债")
                except Exception as e:
                    st.error(f"筛选出错：{str(e)}")


def render_etf_lof_gamble_page(gamble_analyzer):
    """渲染ETF/LOF投机分析页面"""
    st.markdown('<div class="sub-header">🎰 ETF/LOF 投机分析</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        识别大宗商品LOF和海外ETF的异常波动（2-3天突增突降），计算预测因子，AI分析并给出操作建议。
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["异常波动筛选", "AI深度分析", "因子分析汇总"])

    with tab1:
        render_abnormal_screening_page(gamble_analyzer)

    with tab2:
        render_ai_analysis_page(gamble_analyzer)

    with tab3:
        render_factor_summary_page(gamble_analyzer)


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
            config_names = [NEW_CONFIG_OPTION] + [c["name"] for c in config_manager.list_configs()]
            selected_config_name = st.selectbox("加载配置", options=config_names, key="abnormal_config_selector")

        with col_config2:
            config_name_input = st.text_input("配置名称", placeholder="输入配置名称（如：白银LOF组合）", key="abnormal_config_name_input")

        with col_config3:
            st.markdown("&nbsp;")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                save_btn = st.button("💾 保存配置", key="abnormal_save_config", disabled=not config_name_input)
            with col_btn2:
                load_btn = st.button("📂 加载配置", key="abnormal_load_config", disabled=(selected_config_name == NEW_CONFIG_OPTION))

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
            if load_btn and selected_config_name != NEW_CONFIG_OPTION:
                loaded_funds = config_manager.load_config(selected_config_name)
                if loaded_funds is not None:
                    st.session_state.abnormal_selected_funds = loaded_funds
                    st.success(f"✅ 已加载配置：{selected_config_name}（{len(loaded_funds)}只基金）")
                else:
                    st.error(f"❌ 加载配置失败：{selected_config_name}")

            # 处理保存配置
            if save_btn and config_name_input:
                if st.session_state.abnormal_selected_funds:
                    existing = config_manager.load_config(config_name_input)
                    overwrite = False
                    if existing is not None:
                        overwrite = st.checkbox(f"配置 '{config_name_input}' 已存在，是否覆盖？", key="abnormal_overwrite_config")

                    result = config_manager.save_config(config_name_input, st.session_state.abnormal_selected_funds, overwrite=overwrite)
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
        col1, col2, col3 = st.columns(3)

        with col1:
            # 多窗口模式开关
            multi_window_mode = st.checkbox(
                "多窗口检测",
                value=True,
                help="开启后同时检测2/3/5天窗口，任意满足即触发"
            )

            if multi_window_mode:
                window = None
                st.info("将同时检测 2/3/5 天窗口")
            else:
                window = st.selectbox(
                    "时间窗口",
                    options=[2, 3, 5],
                    format_func=lambda x: f"{x}天",
                    index=1  # 默认3天
                )

        with col2:
            threshold = st.slider(
                "波动阈值 (%)",
                min_value=3,
                max_value=30,
                value=8,
                help="累计涨跌幅超过此百分比视为异常（建议：市场平稳时用3-8%，波动大时用10%+）"
            )

        with col3:
            fund_types = st.multiselect(
                "标的选择",
                options=["大宗商品LOF", "海外ETF"],
                default=["大宗商品LOF", "海外ETF"]
            )

        top_n = st.slider("返回数量", min_value=5, max_value=50, value=20)

        submitted = st.form_submit_button("开始筛选", use_container_width=True)

    if submitted:
        if not fund_types:
            st.error("请至少选择一种标的类型！")
            return

        # 转换fund_types
        fund_type_map = {
            "大宗商品LOF": "commodity",
            "海外ETF": "overseas"
        }
        criteria_types = [fund_type_map[t] for t in fund_types]

        # 构建筛选条件
        criteria = {
            'threshold': threshold / 100,  # 转换为小数
            'fund_types': criteria_types
        }

        # 多窗口模式或单窗口
        if multi_window_mode:
            criteria['windows'] = [2, 3, 5]
            window_desc = "2/3/5天（多窗口）"
        else:
            criteria['window'] = window
            window_desc = f"{window}天"

        # 显示筛选条件
        st.markdown("### 筛选条件")
        mode_desc = "使用缓存重新计算" if scan_mode == "use_cache" else "重新扫描计算（更新缓存）"
        criteria_df = pd.DataFrame([
            {"参数": "筛选模式", "值": mode_desc},
            {"参数": "时间窗口", "值": window_desc},
            {"参数": "波动阈值", "值": f"≥ ±{threshold}%"},
            {"参数": "标的类型", "值": ", ".join(fund_types)},
            {"参数": "返回数量", "值": top_n}
        ])
        st.dataframe(criteria_df, use_container_width=True, hide_index=True)

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
                if detail and current and total:
                    detail_text.markdown(f"**{message}: {detail} ({current}/{total})**")
                elif current is not None and total is not None:
                    detail_text.markdown(f"**{message} ({current}/{total})**")
                elif detail:
                    detail_text.markdown(f"**{message}: {detail}**")

            results = screen_and_analyze_with_mode(
                gamble_analyzer, criteria, top_n, scan_mode,
                selected_funds=user_selected_funds if user_selected_funds else None,
                progress_callback=update_progress
            )

            # 完成状态
            if results:
                status_container.update(
                    label=f"✅ 筛选完成！找到 {len(results)} 个异常波动标的",
                    state="complete",
                    expanded=False
                )
                # 显示结果列表
                display_screening_results(results)
            else:
                status_container.update(
                    label="⚠️ 未找到符合条件的标的",
                    state="complete",
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


def display_screening_results(results):
    """显示筛选结果"""
    # 准备数据
    result_data = []
    for r in results:
        # 获取最近异常事件
        recent_event = r.abnormal_events[-1] if r.abnormal_events else None
        recent_change = recent_event['return_pct'] * 100 if recent_event else 0
        current_price = r.current_factors.get('price_trend', 0)  # 简化处理

        result_data.append({
            "代码": r.symbol,
            "名称": r.name,
            "类型": r.fund_type,
            "异常事件数": r.abnormal_events_count,
            "最近波动": f"{recent_change:.1f}%"
        })

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

    # 选择查看详情
    st.markdown("---")
    st.subheader("查看AI分析详情")

    selected_code = st.selectbox(
        "选择标的查看详情",
        options=[r.symbol for r in results],
        format_func=lambda x: next((r.name for r in results if r.symbol == x), x)
    )

    if selected_code:
        selected_result = next((r for r in results if r.symbol == selected_code), None)
        if selected_result:
            # 使用完整的分析结果展示
            display_ai_analysis_result(selected_result)


def render_ai_analysis_page(gamble_analyzer):
    """渲染AI深度分析页面"""
    st.subheader("AI深度分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        analysis_code = st.text_input(
            "基金代码",
            placeholder="如 163415",
            help="输入6位基金代码"
        )

    with col2:
        st.write("")  # 占位
        analyze_btn = st.button("开始分析", type="primary")

    if analyze_btn and analysis_code:
        with st.spinner("正在分析，请稍候..."):
            try:
                result = cached_analyze_single(
                    gamble_analyzer,
                    analysis_code,
                    f"基金{analysis_code}",  # 简化名称
                    "LOF"  # 默认类型
                )

                if result:
                    # 保存到历史记录
                    try:
                        save_analysis_to_history(result)
                    except Exception as save_error:
                        st.warning(f"保存历史记录失败: {str(save_error)}")

                    display_ai_analysis_result(result)
                else:
                    st.warning("""
                    **分析未完成**

                    可能原因：
                    1. 数据不足（需要至少100天历史数据）
                    2. 未发现异常波动事件
                    3. 无法获取数据

                    请尝试其他代码或调整筛选条件。
                    """)

            except Exception as e:
                st.error(f"分析失败: {str(e)}")

    # 渲染历史记录区域
    render_history_section()

    # 使用说明
    with st.expander("💡 使用说明"):
        st.markdown("""
        ### 常见LOF/ETF代码参考

        **大宗商品LOF：**
        - 163415: 白银LOF
        - 161116: 黄金基金
        - 162411: 华宝油气
        - 160716: 有色金属

        **海外ETF：**
        - 513100: 纳斯达克100
        - 513500: 标普500
        - 513660: 恒生ETF

        ### 分析内容

        AI将为您分析：
        1. **因子解读** - 当前关键因子说明了什么
        2. **历史规律** - 该标的异常波动的特点
        3. **时机判断** - 是否适合买入
        4. **操作建议** - 买入点位、止盈止损
        5. **风险提示** - 主要风险点
        """)


def display_ai_analysis_result(result):
    """显示AI分析结果"""
    # 基础信息卡片
    st.markdown(f"""
    <div class="success-box">
        <h4>📊 {result.name} ({result.symbol})</h4>
        <p>类型: {result.fund_type} | 异常事件: {result.abnormal_events_count}次</p>
    </div>
    """, unsafe_allow_html=True)

    # AI分析
    st.markdown(result.ai_summary)

    # 关键因子展示
    if result.feature_importance is not None and len(result.feature_importance) > 0:
        with st.expander("📈 关键因子排名"):
            st.dataframe(
                result.feature_importance.head(10),
                column_config={
                    "feature": "因子",
                    "importance": st.column_config.NumberColumn("重要性", format="%.3f")
                },
                use_container_width=True,
                hide_index=True
            )

    # 异常事件历史
    if result.abnormal_events:
        with st.expander("📜 异常波动历史"):
            events_df = pd.DataFrame(result.abnormal_events)
            events_df['date'] = events_df['date'].dt.strftime('%Y-%m-%d')
            events_df['return_pct'] = (events_df['return_pct'] * 100).round(1).astype(str) + '%'

            st.dataframe(
                events_df[['date', 'return_pct']],
                column_config={
                    "date": "日期",
                    "return_pct": "涨跌幅"
                },
                use_container_width=True,
                hide_index=True
            )


def render_factor_summary_page(gamble_analyzer):
    """渲染因子分析汇总页面"""
    st.subheader("因子分析汇总")

    st.markdown("""
    <div class="info-box">
        对多个标的进行批量分析后，查看跨标的因子重要性排名。
    </div>
    """, unsafe_allow_html=True)

    with st.form("factor_summary_form"):
        col1, col2 = st.columns(2)

        with col1:
            summary_window = st.selectbox("时间窗口", [2, 3, 5], index=1)

        with col2:
            summary_threshold = st.slider("波动阈值 (%)", 3, 30, 8)
            summary_fund_types = st.multiselect(
                "标的",
                ["大宗商品LOF", "海外ETF"],
                default=["大宗商品LOF", "海外ETF"]
            )

        summary_top_n = st.slider("分析数量", 10, 50, 20)

        submitted = st.form_submit_button("开始分析", use_container_width=True)

    if submitted:
        if not summary_fund_types:
            st.error("请选择标的类型")
            return

        with st.spinner("正在分析多个标的，请稍候..."):
            try:
                fund_type_map = {"大宗商品LOF": "commodity", "海外ETF": "overseas"}
                criteria_types = [fund_type_map[t] for t in summary_fund_types]

                criteria = {
                    'window': summary_window,
                    'threshold': summary_threshold / 100,
                    'fund_types': criteria_types
                }

                results = gamble_analyzer.screen_and_analyze(criteria, summary_top_n)

                if results:
                    st.success(f"分析完成！共分析 {len(results)} 个标的")

                    # 获取因子排名
                    factor_ranking = gamble_analyzer.get_top_factors_across_funds(results)

                    if len(factor_ranking) > 0:
                        st.markdown("### 跨标的因子重要性排名")

                        st.dataframe(
                            factor_ranking,
                            column_config={
                                "feature": st.column_config.TextColumn("因子", width="medium"),
                                "mean_importance": st.column_config.NumberColumn("平均重要性", format="%.3f"),
                                "occurrence_count": st.column_config.NumberColumn("出现次数")
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                        # 因子说明
                        st.markdown("---")
                        st.markdown("### 因子说明")

                        factor_descriptions = {
                            'momentum_5': '5日价格动量 - 反映短期价格趋势',
                            'momentum_10': '10日价格动量 - 反映中期价格趋势',
                            'momentum_20': '20日价格动量 - 反映长期价格趋势',
                            'volatility_20': '20日波动率 - 反映价格波动程度',
                            'atr_14': 'ATR(14) - 平均真实波幅',
                            'volume_ratio': '量比 - 当前成交量/20日平均成交量',
                            'volume_ma_5': '5日/20日成交量比',
                            'rsi_14': 'RSI(14) - 相对强弱指标',
                            'macd': 'MACD - 指数平滑异同移动平均线',
                            'bollinger_bandwidth': '布林带带宽 - 反映价格波动范围',
                            'pv_divergence': '价量背离 - 价格与成交量变化差异',
                            'spread_pct': '买卖价差百分比',
                            'liquidity_impact': '流动性冲击',
                            'price_trend': '价格趋势方向',
                            'vol_clustering': '波动聚集性'
                        }

                        for _, row in factor_ranking.head(10).iterrows():
                            factor = row['feature']
                            desc = factor_descriptions.get(factor, '暂无说明')
                            st.markdown(f"**{factor}**: {desc}")

                else:
                    st.warning("未找到符合条件的标的")

            except Exception as e:
                st.error(f"分析失败: {str(e)}")


import hashlib
import json
import pickle
from pathlib import Path

# 项目缓存目录
PROJECT_CACHE_DIR = Path(__file__).parent.parent / ".cache" / "streamlit"
PROJECT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_cache_key(func_name, *args, **kwargs):
    """生成缓存键"""
    key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cache_file(cache_key):
    """获取缓存文件路径"""
    return PROJECT_CACHE_DIR / f"{cache_key}.pkl"


def _is_cache_valid(cache_file, ttl_seconds=3600):
    """检查缓存是否有效"""
    if not cache_file.exists():
        return False
    import time
    return time.time() - cache_file.stat().st_mtime < ttl_seconds


def _load_from_cache(cache_key, ttl_seconds=3600):
    """从缓存加载"""
    cache_file = _get_cache_file(cache_key)
    if _is_cache_valid(cache_file, ttl_seconds):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            pass
    return None


def _save_to_cache(cache_key, data):
    """保存到缓存"""
    cache_file = _get_cache_file(cache_key)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception:
        pass


@st.cache_data  # 默认一直缓存，直到手动清除
def cached_get_fund_list(_fetcher, fund_type: str, _force_refresh: bool = False) -> List[Dict]:
    """
    缓存基金列表（只缓存代码和名称，不缓存时序数据）
    默认一直缓存，直到手动清除缓存或重启应用

    Args:
        _fetcher: AKShareFetcher实例
        fund_type: 'commodity' 或 'overseas'
        _force_refresh: 强制刷新缓存（内部使用）

    Returns:
        基金列表 [{'code': 'xxx', 'name': 'xxx', 'type': 'xxx'}]
    """
    if fund_type == 'commodity':
        return _fetcher.get_commodity_lof_list()
    elif fund_type == 'overseas':
        return _fetcher.get_overseas_etf_list()
    else:
        return []


def render_fund_selection_box(all_funds: List[Dict], key_prefix: str = "fund_select") -> List[Dict]:
    """
    渲染双栏穿梭框组件用于基金选择

    Args:
        all_funds: 全部可选基金列表 [{"code": "xxx", "name": "xxx", "type": "xxx"}]
        key_prefix: 组件key前缀，用于避免冲突

    Returns:
        List[Dict]: 用户选中的基金列表

    Raises:
        ValueError: 如果 all_funds 为空或缺少必需的键
    """
    # 输入验证
    if not all_funds:
        raise ValueError("all_funds 不能为空")

    # 验证必需的键
    required_keys = {'code', 'name', 'type'}
    for i, fund in enumerate(all_funds):
        if not isinstance(fund, dict):
            raise ValueError(f"all_funds[{i}] 必须是字典")
        if not required_keys.issubset(fund.keys()):
            missing = required_keys - fund.keys()
            raise ValueError(f"all_funds[{i}] 缺少必需的键: {missing}")

    # 初始化 session state
    state_key = f"{key_prefix}_selected"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    # 创建字符串到基金的映射（移除未使用的 fund_options）
    str_to_fund = {}
    for fund in all_funds:
        option_str = f"{fund['code']} - {fund['name']} ({fund['type']})"
        str_to_fund[option_str] = fund

    # 三栏布局
    col_left, col_mid, col_right = st.columns([2, 1, 2])

    with col_left:
        st.markdown("##### 可选标的")
        search_term = st.text_input(
            "搜索基金",
            key=f"{key_prefix}_search",
            placeholder="输入代码或名称搜索..."
        )

        # 根据搜索词过滤选项
        if search_term:
            filtered_options = {
                k: v for k, v in str_to_fund.items()
                if search_term.lower() in k.lower()
            }
        else:
            filtered_options = str_to_fund

        selected_from_left = st.multiselect(
            "选择基金",
            options=list(filtered_options.keys()),
            key=f"{key_prefix}_left_select",
            label_visibility="collapsed"
        )

    with col_mid:
        st.markdown("")  # 占位对齐
        st.markdown("")  # 占位对齐

        # 向右移动按钮
        if st.button("→", key=f"{key_prefix}_move_right", help="添加选中项"):
            # 使用 set 进行 O(1) 查重检查
            selected_set = {tuple(sorted(fund.items())) for fund in st.session_state[state_key]}
            for option_str in selected_from_left:
                fund = str_to_fund.get(option_str)
                if fund:
                    fund_tuple = tuple(sorted(fund.items()))
                    if fund_tuple not in selected_set:
                        st.session_state[state_key].append(fund)
                        selected_set.add(fund_tuple)
            st.rerun()

        # 向左移动按钮（简化处理，直接重新运行）
        if st.button("←", key=f"{key_prefix}_move_left", help="重新选择"):
            st.rerun()

        # 全部移动按钮
        if st.button("»", key=f"{key_prefix}_move_all", help="添加全部"):
            # 使用 set 进行 O(1) 查重检查
            selected_set = {tuple(sorted(fund.items())) for fund in st.session_state[state_key]}
            for fund in all_funds:
                fund_tuple = tuple(sorted(fund.items()))
                if fund_tuple not in selected_set:
                    st.session_state[state_key].append(fund)
                    selected_set.add(fund_tuple)
            st.rerun()

        # 清空按钮
        if st.button("«", key=f"{key_prefix}_clear_all", help="清空全部"):
            st.session_state[state_key] = []
            st.rerun()

    with col_right:
        st.markdown("##### 已选标的")

        if st.session_state[state_key]:
            # 转换为 DataFrame 用于显示
            selected_data = []
            for fund in st.session_state[state_key]:
                selected_data.append({
                    "代码": fund['code'],
                    "名称": fund['name'],
                    "类型": fund['type']
                })

            df = pd.DataFrame(selected_data)
            st.data_editor(
                df,
                column_config={
                    "代码": st.column_config.TextColumn("代码", width="small"),
                    "名称": st.column_config.TextColumn("名称", width="medium"),
                    "类型": st.column_config.TextColumn("类型", width="small")
                },
                hide_index=True,
                use_container_width=True
            )

            if st.button("🗑️ 清空全部", key=f"{key_prefix}_delete", help="清空全部已选标的"):
                st.session_state[state_key] = []
                st.rerun()
        else:
            st.info("暂无已选标的，请从左侧选择")

    return st.session_state[state_key]


def screen_and_analyze_with_mode(_analyzer, criteria: Dict, top_n: int, scan_mode: str, selected_funds: Optional[List[Dict]] = None, progress_callback: Optional[Callable[[float, str, Optional[str], Optional[int], Optional[int]], None]] = None) -> List:
    """
    根据筛选模式执行分析

    Args:
        _analyzer: LOFETFGambleAnalyzer实例
        criteria: 筛选条件
        top_n: 返回数量
        scan_mode: 'use_cache'（使用缓存）或 'rescan'（重新扫描）
        selected_funds: 用户预选的基金列表（可选，如果提供则跳过缓存/重扫逻辑）
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
    if selected_funds is not None:
        # 使用用户预选的基金
        target_list = selected_funds
        if progress_callback:
            progress_callback(0.0, f"📋 使用配置中的 {len(selected_funds)} 只基金...", None, None, None)
        else:
            st.info(f"📋 使用配置中的 {len(selected_funds)} 只基金...")
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


def _screen_and_analyze_with_targets(_analyzer, target_list: List[Dict], criteria: Dict, top_n: int, progress_callback: Optional[Callable[[float, str, Optional[str], Optional[int], Optional[int]], None]] = None) -> List:
    """
    使用给定的目标列表进行筛选分析（内部函数）

    Args:
        _analyzer: LOFETFGambleAnalyzer实例
        target_list: 预先获取的基金列表
        criteria: 筛选条件
        top_n: 返回数量
        progress_callback: 进度回调函数，接收 (progress: float, message: str, name: Optional[str], current: Optional[int], total: Optional[int])

    Returns:
        分析结果列表
    """
    windows = criteria.get('windows', None)
    if windows is None:
        window = criteria.get('window', 3)
        windows = [window]

    threshold = criteria.get('threshold', 0.15)
    use_multi_window = len(windows) > 1

    import logging
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    logger = logging.getLogger(__name__)
    logger.info(f"开始筛选分析，使用{len(target_list)}个目标标的，阈值={threshold*100}%")

    # 快速筛选：检测异常波动（使用并发加速）
    screened = []
    items_to_scan = list(enumerate(target_list[:top_n * 3]))
    total_to_scan = len(items_to_scan)
    completed_count = [0]  # 使用列表以便在闭包中修改
    progress_lock = threading.Lock()

    def scan_single_item(idx_item):
        """扫描单个标的"""
        idx, item = idx_item
        symbol = item['code']
        name = item['name']
        fund_type = item['type']

        try:
            df = _analyzer.fetcher.get_lof_etf_history(symbol, period=100)
            if df is None or len(df) < 50:
                return None

            if use_multi_window:
                abnormal_dates, _ = _analyzer.detector.detect_sudden_moves_multi_window(
                    df['close'], windows=windows, threshold=threshold
                )
            else:
                abnormal_dates, _ = _analyzer.detector.detect_sudden_moves(
                    df['close'], window=windows[0], threshold=threshold
                )

            if len(abnormal_dates) > 0:
                return {
                    'symbol': symbol,
                    'name': name,
                    'fund_type': fund_type,
                    'events_count': len(abnormal_dates),
                    'recent_change': df['close'].pct_change(windows[0]).iloc[-1]
                }
            return None

        except Exception as e:
            logger.error(f"筛选 {symbol} 失败: {e}")
            return None

    # 使用线程池并发扫描（最大3个并发，避免API过载）
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scan_single_item, item): item for item in items_to_scan}

        for future in as_completed(futures):
            idx, item = futures[future]
            result = future.result()

            # 更新进度
            with progress_lock:
                completed_count[0] += 1
                if progress_callback and total_to_scan > 0:
                    progress = 0.1 + completed_count[0] / total_to_scan * 0.4
                    detail_text = f"{item['name']} ({item['code']})"
                    progress_callback(progress, "📊 筛选中...", detail_text, completed_count[0], total_to_scan)

            if result is not None:
                screened.append(result)

    # 按异常事件数量排序，取前top_n个
    screened.sort(key=lambda x: x['events_count'], reverse=True)
    top_targets = screened[:top_n]

    logger.info(f"筛选出 {len(top_targets)} 个目标进行深度分析")

    if progress_callback:
        progress_callback(0.5, "🔍 深度分析", None, None, None)

    # 深度分析（使用并发加速）
    results = []
    analysis_completed = [0]
    total_to_analyze = len(top_targets)

    def analyze_single_target(target):
        """分析单个标的"""
        try:
            result = _analyzer.analyze_single(
                target['symbol'],
                target['name'],
                target['fund_type']
            )
            return result
        except Exception as e:
            logger.error(f"分析 {target['symbol']} 失败: {e}")
            return None

    # 使用线程池并发分析（最大3个并发，避免API过载）
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(analyze_single_target, target): target for target in top_targets}

        for future in as_completed(futures):
            target = futures[future]
            result = future.result()

            # 更新进度
            with progress_lock:
                analysis_completed[0] += 1
                if progress_callback and total_to_analyze > 0:
                    progress = 0.5 + analysis_completed[0] / total_to_analyze * 0.5
                    detail_text = f"{target['name']} ({target['symbol']})"
                    progress_callback(progress, "🤖 分析中...", detail_text, analysis_completed[0], total_to_analyze)

            if result is not None:
                results.append(result)

    if progress_callback:
        progress_callback(1.0, "✅ 分析完成", None, None, None)

    logger.info(f"完成 {len(results)} 个标的的分析")
    return results


def cached_screen_and_analyze(_analyzer, criteria, top_n):
    """
    筛选分析（不缓存时序数据和AI分析结果，只缓存基金列表）

    注意：不再缓存完整的分析结果，因为时序数据每天变化
    """
    # 直接调用分析器，不缓存结果
    result = _analyzer.screen_and_analyze(criteria, top_n)
    return result


def cached_analyze_single(_analyzer, symbol, name, fund_type):
    """
    单个分析（不缓存时序数据和AI分析结果）

    注意：不再缓存分析结果，因为时序数据每天变化
    """
    # 直接调用分析器，不缓存结果
    result = _analyzer.analyze_single(symbol, name, fund_type)
    return result


def get_history_manager():
    """获取历史记录管理器实例（缓存）"""
    cache_dir = Path(__file__).parent.parent / ".cache" / "streamlit"

    if 'history_manager' not in st.session_state:
        from storage.analysis_history import AnalysisHistoryManager
        st.session_state.history_manager = AnalysisHistoryManager(cache_dir)

    return st.session_state.history_manager


def save_analysis_to_history(result):
    """保存分析结果到历史"""
    import time

    manager = get_history_manager()

    # 尝试从 current_factors 中获取价格信息，如果没有则使用默认值
    # current_factors 包含技术因子，不直接包含价格
    # 使用 0.0 作为占位值，实际价格需要从数据源重新获取
    current_price = 0.0

    entry = AnalysisHistoryEntry(
        id=f"{int(time.time()*1000)}-{result.symbol}",
        symbol=result.symbol,
        name=result.name,
        fund_type=result.fund_type,
        created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        abnormal_events_count=result.abnormal_events_count,
        current_price=current_price,
        ai_summary=result.ai_summary,
        current_factors=result.current_factors
    )

    manager.add_entry(entry)


def render_history_section():
    """渲染历史记录区域"""
    manager = get_history_manager()

    st.markdown("---")

    with st.expander("📜 分析历史记录", expanded=False):
        # 搜索和过滤控件
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            search_keyword = st.text_input("搜索", placeholder="输入代码或名称", key="history_search")
        with col2:
            filter_type = st.selectbox("类型", options=["全部", "LOF", "ETF"], key="history_filter_type")
        with col3:
            st.write("")
            refresh_btn = st.button("刷新", key="history_refresh")

        # 获取历史记录
        fund_type_filter = None if filter_type == "全部" else filter_type
        entries = manager.search(keyword=search_keyword, fund_type=fund_type_filter)

        if not entries:
            st.info("暂无历史记录")
        else:
            # 显示历史记录列表
            for entry in entries:
                col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
                with col1:
                    st.markdown(f"**{entry.symbol}**")
                with col2:
                    st.markdown(f"{entry.name}")
                with col3:
                    st.caption(entry.created_at.replace('T', ' '))
                with col4:
                    view_btn = st.button("查看", key=f"view_{entry.id}")
                    delete_btn = st.button("删除", key=f"delete_{entry.id}")

                    if view_btn:
                        st.markdown(f"""<div class="success-box"><h4>{entry.name} ({entry.symbol})</h4><p>类型: {entry.fund_type} | 异常事件: {entry.abnormal_events_count}次</p></div>""", unsafe_allow_html=True)
                        st.markdown(entry.ai_summary)
                    if delete_btn:
                        if manager.delete_entry(entry.id):
                            st.rerun()
                        else:
                            st.error("删除失败")

            # 底部操作按钮
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("清空全部", key="history_clear_all"):
                    if manager.clear_all():
                        st.rerun()
                    else:
                        st.error("清空失败")
            with col2:
                if st.button("导出CSV", key="history_export"):
                    csv_path = manager.export_to_csv()
                    if csv_path:
                        st.success(f"已导出到: {csv_path}")
                    else:
                        st.error("导出失败")


def main():
    """主函数"""
    # 初始化 Agent 和分析器
    agent = initialize_agent()
    screener, market_analyzer, etf_analyzer, cb_technical_analyzer, gamble_analyzer = get_analyzers(agent)

    # 侧边栏导航
    with st.sidebar:
        st.markdown("# 📈 A股投研竞技场")
        st.markdown("---")

        page = st.radio(
            "选择功能",
            ["首页", "选股筛选", "市场分析", "ETF 分析", "可转债分析", "ETF/LOF投机"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # 显示系统状态
        st.markdown("### 系统状态")
        if agent is not None:
            st.success("✅ AI Agent 已连接")
        else:
            st.error("❌ AI Agent 未连接")

        if screener is not None:
            st.success("✅ 选股模块就绪")
        else:
            st.error("❌ 选股模块未就绪")

        if market_analyzer is not None:
            st.success("✅ 市场分析模块就绪")
        else:
            st.error("❌ 市场分析模块未就绪")

        if etf_analyzer is not None:
            st.success("✅ ETF 模块就绪")
        else:
            st.error("❌ ETF 模块未就绪")

        if cb_technical_analyzer is not None:
            st.success("✅ 可转债分析模块就绪")
        else:
            st.error("❌ 可转债分析模块未就绪")

        if gamble_analyzer is not None:
            st.success("✅ 投机分析模块就绪")
        else:
            st.error("❌ 投机分析模块未就绪")

        st.markdown("---")

        # 帮助信息
        st.markdown("### 使用帮助")
        st.markdown("""
        <style>
        .help-text {
            font-size: 0.85rem;
            color: #666;
        }
        </style>
        <p class="help-text">
        如有问题，请查看项目文档或提交 Issue。
        </p>
        """, unsafe_allow_html=True)

    # 根据选择的页面渲染内容
    if page == "首页":
        render_home_page()

    elif page == "选股筛选":
        if screener is None:
            st.error("选股模块未初始化，请检查配置！")
        else:
            render_stock_screening_page(screener)

    elif page == "市场分析":
        if market_analyzer is None:
            st.error("市场分析模块未初始化，请检查配置！")
        else:
            render_market_analysis_page(market_analyzer)

    elif page == "ETF 分析":
        if etf_analyzer is None:
            st.error("ETF 模块未初始化，请检查配置！")
        else:
            render_etf_analysis_page(etf_analyzer)

    elif page == "可转债分析":
        if cb_technical_analyzer is None:
            st.error("可转债分析模块未初始化，请检查配置！")
        else:
            render_convertible_analysis_page(cb_technical_analyzer, agent)

    elif page == "ETF/LOF投机":
        if gamble_analyzer is None:
            st.error("投机分析模块未初始化，请检查配置！")
        else:
            render_etf_lof_gamble_page(gamble_analyzer)


if __name__ == "__main__":
    main()
