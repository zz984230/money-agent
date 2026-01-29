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
        try:
            # 使用新浪财经-沪深可转债实时行情数据接口，返回所有沪深可转债
            df = ak.bond_zh_hs_cov_spot()

            if df is None or df.empty:
                logger.warning("获取可转债列表为空")
                return []

            # 重命名列为统一格式
            result = []
            for _, row in df.iterrows():
                # 从 symbol 字段提取纯数字代码（去掉 sh/sz 前缀）
                symbol = str(row.get('symbol', ''))
                code = symbol.replace('sh', '').replace('sz', '') if symbol else ''

                result.append({
                    '代码': code,
                    '转债名称': str(row.get('name', '')),
                    '现价': float(row.get('trade', 0)) if pd.notna(row.get('trade')) else 0.0,
                    '涨跌幅': float(row.get('pricechange', 0)) if pd.notna(row.get('pricechange')) else 0.0,
                    '正股代码': '',
                    '正股名称': '',
                    '转股价': 0.0,
                    '转股价值': 0.0,
                    '转股溢价率': 0.0,
                    '回售触发价': 0.0,
                    '强赎触发价': 0.0,
                    '成交额': float(row.get('amount', 0)) if pd.notna(row.get('amount')) else 0.0,
                })

            logger.info(f"获取可转债列表成功，共 {len(result)} 只")
            return result

        except Exception as e:
            logger.error(f"获取可转债列表失败: {e}", exc_info=True)
            return []

    def get_convertible_by_name(self, cb_name: str) -> Optional[str]:
        """
        根据可转债名称查找可转债代码

        Args:
            cb_name: 可转债名称（支持模糊匹配）

        Returns:
            可转债代码（6位数字），如果未找到返回None
        """
        try:
            cb_list = self.get_convertible_list()

            if not cb_list:
                logger.warning("获取可转债列表为空")
                return None

            # 精确匹配（使用中文字段名）
            for cb in cb_list:
                if cb.get('转债名称') == cb_name:
                    return cb.get('代码')

            # 模糊匹配
            for cb in cb_list:
                name = cb.get('转债名称', '')
                if cb_name in name:
                    logger.info(f"模糊匹配: '{cb_name}' -> '{name}' ({cb.get('代码')})")
                    return cb.get('代码')

            logger.warning(f"未找到可转债: {cb_name}")
            return None

        except Exception as e:
            logger.error(f"根据名称查找可转债失败: {e}", exc_info=True)
            return None

    def get_convertible_name_by_code(self, cb_code: str) -> Optional[str]:
        """
        根据可转债代码查找可转债名称

        Args:
            cb_code: 可转债代码（6位数字）

        Returns:
            可转债名称，如果未找到返回None
        """
        try:
            cb_list = self.get_convertible_list()

            if not cb_list:
                logger.warning("获取可转债列表为空")
                return None

            # 精确匹配（使用中文字段名）
            for cb in cb_list:
                if cb.get('代码') == cb_code:
                    return cb.get('转债名称')

            logger.warning(f"未找到可转债代码: {cb_code}")
            return None

        except Exception as e:
            logger.error(f"根据代码查找可转债名称失败: {e}", exc_info=True)
            return None

    def get_convertible_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取可转债日线数据

        Args:
            symbol: 可转债代码
            start_date: 开始日期，格式：YYYYMMDD
            end_date: 结束日期，格式：YYYYMMDD

        Returns:
            DataFrame: 包含可转债日线数据的DataFrame
        """
        try:
            # bond_zh_hs_cov_daily 需要带市场前缀的完整代码
            # 深市代码以 0, 1, 2, 3 开头，使用 sz 前缀
            # 沪市代码以 6, 11 开头，使用 sh 前缀
            original_symbol = symbol
            if not symbol.startswith(('sz', 'sh')):
                if symbol.startswith(('0', '1', '2', '3')):
                    symbol = 'sz' + symbol
                elif symbol.startswith(('6', '11')):
                    symbol = 'sh' + symbol
                else:
                    # 默认使用深市
                    symbol = 'sz' + symbol

            # akshare的可转债函数不支持start_date和end_date参数
            df = ak.bond_zh_hs_cov_daily(symbol=symbol)

            if df is None or df.empty:
                logger.debug(f"可转债 {original_symbol} 历史数据为空")
                return pd.DataFrame()

            # 将日期字符串转换为 YYYY-MM-DD 格式以便比较
            start_date_formatted = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end_date_formatted = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

            # 先筛选日期范围（在date列还是字符串的时候）
            if 'date' in df.columns:
                # 将 date 列转为字符串格式进行比较
                df['date_str'] = df['date'].astype(str)
                df = df[(df['date_str'] >= start_date_formatted) & (df['date_str'] <= end_date_formatted)]
                df = df.drop(columns=['date_str'])

            # 再进行数据处理（转换日期为datetime）
            return self._process_daily_data(df)

        except Exception as e:
            logger.error(f"获取可转债 {original_symbol} 历史数据失败: {e}")
            return pd.DataFrame()

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
            # 使用 bond_zh_cov 接口获取详细信息（更稳定）
            df = ak.bond_zh_cov()

            if df is None or df.empty:
                logger.warning("获取可转债数据一览表失败")
                return None

            # 查找对应代码的可转债
            matching = df[df['债券代码'] == cb_code]

            if matching.empty:
                logger.warning(f"未找到可转债 {cb_code}")
                return None

            # 提取第一行数据
            row = matching.iloc[0]

            # 构建返回字典
            result = {
                "cb_code": cb_code,
                "cb_name": str(row.get('债券简称', '')),
                "conversion_price": float(row.get('转股价', 0)) if pd.notna(row.get('转股价')) else 0.0,
                "conversion_value": float(row.get('转股价值', 0)) if pd.notna(row.get('转股价值')) else 0.0,
                "premium_rate": float(row.get('转股溢价率', 0)) if pd.notna(row.get('转股溢价率')) else 0.0,
                "stock_code": str(row.get('正股代码', '')),
                "stock_name": str(row.get('正股简称', '')),
                "stock_price": float(row.get('正股价', 0)) if pd.notna(row.get('正股价')) else 0.0,
            }

            # 注意：bond_zh_cov 返回的是发行数据，转股价值和溢价值可能不是实时数据
            # 如果需要实时数据，应该根据实时价格重新计算

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
