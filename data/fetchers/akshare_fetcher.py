import akshare as ak
import pandas as pd
from typing import List, Dict, Optional


class AKShareFetcher:
    """AKShare数据获取类"""

    def __init__(self):
        """初始化AKShare数据获取器"""
        pass

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
        # 重命名列为英文
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        }

        # 只重命名存在的列
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_columns)

        # 转换日期列为datetime类型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

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
        # 重命名列为英文
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        }

        # 只重命名存在的列
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_columns)

        # 转换日期列为datetime类型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

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
        df = ak.bond_cb_hist(symbol=symbol, start_date=start_date, end_date=end_date)
        # 重命名列为英文
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        }

        # 只重命名存在的列
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_columns)

        # 转换日期列为datetime类型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

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