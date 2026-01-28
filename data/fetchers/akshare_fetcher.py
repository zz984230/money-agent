import akshare as ak
import pandas as pd
from typing import List, Dict, Optional


class AKShareFetcher:
    """AKShare数据获取类"""

    # 列映射字典
    COLUMN_MAPPING = {
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount'
    }

    def __init__(self):
        """初始化AKShare数据获取器"""
        pass

    def _process_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理日线数据：列名转换和日期处理

        Args:
            df: 原始数据DataFrame

        Returns:
            DataFrame: 处理后的DataFrame
        """
        # 重命名列为英文
        existing_columns = {k: v for k, v in self.COLUMN_MAPPING.items() if k in df.columns}
        df = df.rename(columns=existing_columns)

        # 转换日期列为datetime类型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def get_stock_list(self) -> List[Dict]:
        """获取 A 股列表"""
        stock_list = ak.stock_zh_a_spot_em()
        # 转换为字典列表
        result = stock_list.to_dict('records')
        return result

    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票日线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD

        Returns:
            DataFrame: 包含日线数据的DataFrame
        """
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="")
        return self._process_daily_data(df)

    def get_etf_list(self) -> List[Dict]:
        """获取 ETF 列表"""
        etf_list = ak.fund_etf_category_sina(symbol="ETF基金")
        return etf_list.to_dict('records')

    def get_etf_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取 ETF 日线数据

        Args:
            symbol: ETF代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD

        Returns:
            DataFrame: 包含ETF日线数据的DataFrame
        """
        df = ak.fund_etf_hist_sina(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
        return self._process_daily_data(df)

    def get_convertible_list(self) -> List[Dict]:
        """获取可转债列表"""
        cb_list = ak.bond_cb_jsl()
        return cb_list.to_dict('records')

    def get_convertible_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取可转债日线数据

        Args:
            symbol: 可转债代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD

        Returns:
            DataFrame: 包含可转债日线数据的DataFrame
        """
        # akshare的可转债函数不支持start_date和end_date参数
        df = ak.bond_zh_hs_cov_daily(symbol=symbol)
        # 筛选日期范围
        if 'date' in df.columns:
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        return self._process_daily_data(df)

    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            Dict: 股票基本信息字典
        """
        stock_info = ak.stock_individual_info_em(symbol=symbol)
        if not stock_info.empty:
            return stock_info.iloc[0].to_dict()
        return {}

    def get_index_daily(self, index_code: str, date: str) -> pd.DataFrame:
        """获取指数日线数据

        Args:
            index_code: 指数代码（如 000001）
            date: 目标日期，格式：YYYY-MM-DD

        Returns:
            DataFrame: 包含指数日线数据的DataFrame
        """
        # 根据指数代码确定市场前缀
        if index_code.startswith('00'):
            symbol = f"sh{index_code}"
        elif index_code.startswith('30') or index_code.startswith('39'):
            symbol = f"sz{index_code}"
        else:
            symbol = f"sh{index_code}"

        df = ak.stock_zh_index_daily(symbol=symbol)

        # 过滤日期范围
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)
            df = df[df['date'] <= date]
            if len(df) > 30:
                df = df.tail(30)

        return df

    def get_market_stats(self) -> Optional[Dict]:
        """获取市场统计数据

        Returns:
            Dict: 包含市场统计数据的字典，如果获取失败则返回None
        """
        try:
            # 获取A股市场概况
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                return None

            # 统计涨跌情况
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            unchanged_count = len(df[df['涨跌幅'] == 0])

            # 统计涨跌停（假设涨跌停为9.9%以上）
            limit_up_count = len(df[df['涨跌幅'] >= 9.9])
            limit_down_count = len(df[df['涨跌幅'] <= -9.9])

            # 计算总成交额
            total_amount = df['成交额'].sum() if '成交额' in df.columns else 0

            return {
                "up_count": up_count,
                "down_count": down_count,
                "unchanged_count": unchanged_count,
                "limit_up_count": limit_up_count,
                "limit_down_count": limit_down_count,
                "total_amount": total_amount
            }

        except Exception:
            return None