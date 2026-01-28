"""
AKShare Financial Data Fetcher
AKShare 财务数据获取器
使用 AKShare 免费接口获取财务数据，无需 Token
"""

import logging
from typing import Dict, Optional
import akshare as ak


# 配置日志
logger = logging.getLogger(__name__)


class AKShareFinancialFetcher:
    """AKShare 财务数据获取器 - 免费无需Token"""

    def __init__(self):
        """初始化 AKShare 财务数据获取器"""
        logger.info("AKShare Financial Fetcher 初始化成功（无需Token）")

    def get_financial_abstract(self, stock_code: str) -> Optional[Dict]:
        """
        获取财务摘要数据（包含主要财务指标）

        Args:
            stock_code: 股票代码（6位数字，如 688798）

        Returns:
            包含财务数据的字典：
            {
                "report_date": "20250930",  # 最新报告期
                "net_profit": "...",        # 净利润
                "revenue": "...",           # 营业总收入
                "total_assets": "...",      # 资产总计
                "total_liabilities": "...", # 负债合计
                "operating_cost": "...",    # 营业成本
                "dataframe": DataFrame      # 完整数据
            }
            如果获取失败则返回 None

        Raises:
            RuntimeError: 当 API 调用失败时
        """
        try:
            logger.debug(f"开始获取 {stock_code} 的财务摘要数据")

            # 调用 AKShare 财务摘要接口
            df = ak.stock_financial_abstract(symbol=stock_code)

            if df is None or df.empty:
                raise RuntimeError(f"未能获取 {stock_code} 的财务摘要数据")

            # 提取最新报告期（第3列开始是各报告期的数据）
            latest_period = df.columns[2] if len(df.columns) > 2 else "N/A"

            # 提取关键财务指标
            result = {
                "report_date": latest_period,
                "dataframe": df
            }

            # 从 DataFrame 中提取关键指标
            metrics_map = {
                "净利润": "net_profit",
                "营业总收入": "revenue",
                "资产总计": "total_assets",
                "负债合计": "total_liabilities",
                "营业成本": "operating_cost",
                "销售费用": "selling_expense",
                "管理费用": "admin_expense",
                "财务费用": "finance_expense",
                "投资收益": "investment_income",
                "经营活动产生的现金流量净额": "operating_cash_flow"
            }

            for _, row in df.iterrows():
                metric_name = row.get("指标", "")
                if metric_name in metrics_map:
                    latest_value = row.iloc[2]  # 最新报告期的值
                    result[metrics_map[metric_name]] = latest_value

            logger.info(f"成功获取 {stock_code} 财务摘要，报告期: {latest_period}")
            return result

        except Exception as e:
            logger.error(f"获取 {stock_code} 财务摘要失败: {e}", exc_info=True)
            raise RuntimeError(f"获取 AKShare 财务数据失败: {e}")

    def get_financial_indicator(self, stock_code: str) -> Optional[Dict]:
        """
        获取财务指标数据

        Args:
            stock_code: 股票代码（6位数字，如 688798）

        Returns:
            包含财务指标的字典
        """
        try:
            logger.debug(f"开始获取 {stock_code} 的财务指标数据")

            # 调用 AKShare 财务指标接口
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)

            if df is None or df.empty:
                logger.warning(f"未能获取 {stock_code} 的财务指标数据")
                return None

            logger.info(f"成功获取 {stock_code} 财务指标，共 {len(df)} 行")
            return {"dataframe": df}

        except Exception as e:
            logger.warning(f"获取 {stock_code} 财务指标失败: {e}")
            return None

    def format_financial_data(self, financial_data: Dict) -> str:
        """
        格式化财务数据用于显示

        Args:
            financial_data: get_financial_abstract() 返回的数据

        Returns:
            格式化的财务数据字符串
        """
        if not financial_data:
            return "无财务数据"

        lines = []
        lines.append(f"报告期: {financial_data.get('report_date', 'N/A')}")

        # 主要财务指标
        lines.append("\n主要财务指标:")

        if financial_data.get('revenue'):
            lines.append(f"  营业总收入: {financial_data['revenue']}")
        if financial_data.get('operating_cost'):
            lines.append(f"  营业成本: {financial_data['operating_cost']}")
        if financial_data.get('net_profit'):
            lines.append(f"  净利润: {financial_data['net_profit']}")

        # 资产负债
        if financial_data.get('total_assets') or financial_data.get('total_liabilities'):
            lines.append("\n资产负债:")
            if financial_data.get('total_assets'):
                lines.append(f"  资产总计: {financial_data['total_assets']}")
            if financial_data.get('total_liabilities'):
                lines.append(f"  负债合计: {financial_data['total_liabilities']}")

        # 费用
        expenses = []
        if financial_data.get('selling_expense'):
            expenses.append(f"销售费用: {financial_data['selling_expense']}")
        if financial_data.get('admin_expense'):
            expenses.append(f"管理费用: {financial_data['admin_expense']}")
        if financial_data.get('finance_expense'):
            expenses.append(f"财务费用: {financial_data['finance_expense']}")
        if expenses:
            lines.append("\n期间费用:")
            lines.extend([f"  {e}" for e in expenses])

        # 现金流
        if financial_data.get('operating_cash_flow'):
            lines.append("\n现金流量:")
            lines.append(f"  经营活动现金流: {financial_data['operating_cash_flow']}")

        return "\n".join(lines)
