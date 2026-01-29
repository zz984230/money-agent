import akshare as ak
import pandas as pd
import logging
from typing import List, Dict, Optional

# 配置日志
logger = logging.getLogger(__name__)


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

    def get_convertible_detail(self, cb_code: str) -> Optional[Dict]:
        """
        获取单个可转债详细信息

        Args:
            cb_code: 可转债代码（6位数字）

        Returns:
            包含条款、评级等信息的字典，如果获取失败返回None
        """
        try:
            import akshare as ak

            logger.debug(f"开始获取可转债 {cb_code} 的详细信息")

            # 获取可转债列表
            df = ak.bond_cb_jsl()

            if df is None or df.empty:
                logger.warning("获取可转债列表失败：返回数据为空")
                return None

            # 查找对应代码的可转债
            matching = df[df.iloc[:, 0].astype(str) == cb_code]

            if matching.empty:
                logger.warning(f"未找到可转债 {cb_code}")
                return None

            # 提取第一行数据
            row = matching.iloc[0]

            # 构建返回字典（使用位置索引访问列）
            result = {
                "cb_code": cb_code,
                "cb_name": str(row.iloc[1]) if len(row) > 1 else "",
                "price": float(row.iloc[2]) if len(row) > 2 else 0.0,
                "stock_code": str(row.iloc[4]) if len(row) > 4 else "",
                "stock_name": str(row.iloc[5]) if len(row) > 5 else "",
            }

            # 添加条款信息（如果存在）
            if len(row) > 13 and row.iloc[13] is not None:
                result["put_trigger_price"] = float(row.iloc[13])
            if len(row) > 14 and row.iloc[14] is not None:
                result["call_trigger_price"] = float(row.iloc[14])
            if len(row) > 9 and row.iloc[9] is not None:
                result["conversion_price"] = float(row.iloc[9])

            logger.debug(f"成功获取可转债 {cb_code} 的详细信息")
            return result

        except Exception as e:
            logger.error(f"获取可转债 {cb_code} 详情失败: {e}", exc_info=True)
            return None

    def get_convertible_realtime(self, cb_code: str) -> Optional[Dict]:
        """
        获取可转债实时行情和盘口数据

        Args:
            cb_code: 可转债代码

        Returns:
            包含实时行情和盘口数据的字典
        """
        try:
            import akshare as ak

            logger.debug(f"开始获取可转债 {cb_code} 的实时行情数据")

            # 获取沪深可转债现货数据
            df = ak.bond_zh_hs_cov_spot()

            if df is None or df.empty:
                logger.warning(f"获取可转债实时数据失败：返回数据为空")
                return None

            # 查找对应转债
            matching = df[df['code'].astype(str) == cb_code]

            if matching.empty:
                logger.warning(f"未找到可转债 {cb_code} 的实时数据")
                return None

            row = matching.iloc[0]

            result = {
                "cb_code": cb_code,
                "price": float(row.get('trade', 0)),
                "change": float(row.get('changepercent', 0)),
                "volume": float(row.get('volume', 0)),
                "amount": float(row.get('amount', 0)),
                "high": float(row.get('high', 0)),
                "low": float(row.get('low', 0)),
                "open": float(row.get('open', 0)),
            }

            # 盘口数据（如果AKShare提供）
            # 注意：bond_zh_hs_cov_spot 可能不提供五档盘口，需要探索其他接口

            logger.debug(f"成功获取可转债 {cb_code} 的实时行情数据")
            return result

        except Exception as e:
            logger.error(f"获取可转债 {cb_code} 实时数据失败: {e}", exc_info=True)
            return None

    def get_convertible_history(
        self,
        cb_code: str,
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取可转债历史价格数据

        Args:
            cb_code: 可转债代码
            days: 获取最近N天数据

        Returns:
            包含历史价格数据的DataFrame
        """
        # 输入验证
        if not cb_code or not isinstance(cb_code, str):
            logger.warning("可转债代码无效")
            return None
        if days <= 0:
            logger.warning(f"天数参数无效: {days}")
            return None

        try:
            logger.debug(f"开始获取可转债 {cb_code} 的历史价格数据（最近{days}天）")

            # AKShare的历史数据接口
            df = ak.bond_zh_hs_cov_daily(symbol=cb_code)

            if df is None or df.empty:
                logger.warning(f"获取可转债 {cb_code} 历史数据失败：返回数据为空")
                return None

            # 处理列名
            df = self._process_daily_data(df)

            # 筛选最近N天
            if 'date' in df.columns:
                df = df.sort_values('date').tail(days)

            logger.debug(f"成功获取可转债 {cb_code} 的历史价格数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取可转债 {cb_code} 历史数据失败: {e}", exc_info=True)
            return None

    def calculate_indicators(
        self,
        history_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        计算技术指标

        Args:
            history_df: 历史价格DataFrame

        Returns:
            包含技术指标的字典
        """
        if history_df is None or history_df.empty:
            logger.debug("历史数据为空，无法计算技术指标")
            return {}

        try:
            result = {}

            # 计算移动平均线
            if 'close' in history_df.columns and len(history_df) >= 5:
                result['ma5'] = history_df['close'].tail(5).mean()
                logger.debug(f"计算MA5: {result['ma5']:.2f}")

            if len(history_df) >= 20:
                result['ma20'] = history_df['close'].tail(20).mean()
                logger.debug(f"计算MA20: {result['ma20']:.2f}")

                # 计算20日波动率（标准差/均值）
                returns = history_df['close'].pct_change().dropna()
                if len(returns) > 0:
                    result['volatility_20d'] = returns.tail(20).std() * 100
                    logger.debug(f"计算20日波动率: {result['volatility_20d']:.2f}%")

            # 价格趋势
            if len(history_df) >= 5:
                recent = history_df['close'].tail(5).values
                if len(recent) >= 2:
                    result['trend_5d'] = (recent[-1] - recent[0]) / recent[0] * 100
                    logger.debug(f"计算5日涨跌幅: {result['trend_5d']:.2f}%")

            logger.debug(f"技术指标计算完成，共{len(result)}个指标")
            return result

        except Exception as e:
            logger.error(f"计算技术指标失败: {e}", exc_info=True)
            return {}
