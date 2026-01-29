"""
Streamlit Dashboard for Money-Agent
A股 AI 投研竞技场 - Streamlit 仪表板
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

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

    with st.form("abnormal_screening_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            window = st.selectbox(
                "时间窗口",
                options=[2, 3, 5],
                format_func=lambda x: f"{x}天",
                index=1  # 默认3天
            )

        with col2:
            threshold = st.slider(
                "波动阈值",
                min_value=5,
                max_value=30,
                value=15,
                help="累计涨跌幅超过此百分比视为异常"
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

        criteria = {
            'window': window,
            'threshold': threshold / 100,  # 转换为小数
            'fund_types': criteria_types
        }

        # 显示筛选条件
        st.markdown("### 筛选条件")
        criteria_df = pd.DataFrame([
            {"参数": "时间窗口", "值": f"{window}天"},
            {"参数": "波动阈值", "值": f"≥ ±{threshold}%"},
            {"参数": "标的类型", "值": ", ".join(fund_types)},
            {"参数": "返回数量", "值": top_n}
        ])
        st.dataframe(criteria_df, use_container_width=True, hide_index=True)

        # 执行筛选
        with st.spinner("正在筛选分析，请稍候..."):
            try:
                results = gamble_analyzer.screen_and_analyze(criteria, top_n)

                if results:
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>筛选完成！找到 {len(results)} 个异常波动标的</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    # 显示结果列表
                    display_screening_results(results)

                else:
                    st.markdown("""
                    <div class="warning-box">
                        <h4>未找到符合条件的标的</h4>
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
            with st.expander(f"📊 {selected_result.name} ({selected_result.symbol}) - AI分析", expanded=True):
                st.markdown(selected_result.ai_summary)


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
                result = gamble_analyzer.analyze_single(
                    analysis_code,
                    f"基金{analysis_code}",  # 简化名称
                    "LOF"  # 默认类型
                )

                if result:
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

    st.info("因子分析汇总功能开发中，敬请期待...")
    # TODO: 实现跨标的因子重要性排名页面


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
