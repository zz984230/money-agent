import akshare as ak
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime

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
                    '涨跌幅': float(row.get('changepercent', 0)) if pd.notna(row.get('changepercent')) else 0.0,
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
            # 沪市代码以 6, 11, 13 开头，使用 sh 前缀
            # 注意：要先匹配沪市的两位前缀（11, 13），再匹配深市的一位前缀
            original_symbol = symbol
            if not symbol.startswith(('sz', 'sh')):
                if symbol.startswith(('6', '11', '13')):
                    # 沪市：6xxx 或 11xxxx 或 13xxxx
                    symbol = 'sh' + symbol
                elif symbol.startswith(('0', '1', '2', '3')):
                    # 深市：0xxx 或 1xxx（非11开头）或 2xxx 或 3xxx
                    symbol = 'sz' + symbol
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

    def get_industry_index_hist(
        self,
        industry_symbol: str,
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取行业指数历史数据

        Args:
            industry_symbol: 行业指数代码（如 "new_energy" 对应新能源）
            days: 获取最近N天数据

        Returns:
            包含行业指数历史数据的DataFrame，包含 close 列用于计算涨跌幅
        """
        try:
            logger.debug(f"开始获取行业指数 {industry_symbol} 的历史数据（最近{days}天）")

            # 使用东方财富行业指数接口
            # industry_symbol 是行业中文名称（如 "贵金属"）
            df = ak.stock_board_industry_hist_em(symbol=industry_symbol)

            if df is None or df.empty:
                logger.warning(f"获取行业指数 {industry_symbol} 历史数据失败：返回数据为空")
                return pd.DataFrame()

            # 处理列名映射
            df = self._process_daily_data(df)

            # 筛选最近N天
            if 'date' in df.columns:
                df = df.sort_values('date').tail(days)

            logger.debug(f"成功获取行业指数 {industry_symbol} 的历史数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取行业指数 {industry_symbol} 历史数据失败: {e}", exc_info=True)
            return pd.DataFrame()

    def get_benchmark_index_hist(
        self,
        index_code: str = "000300",
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取基准指数历史数据（默认沪深300）

        Args:
            index_code: 指数代码（默认沪深300 000300）
            days: 获取最近N天数据

        Returns:
            包含基准指数历史数据的DataFrame
        """
        try:
            logger.debug(f"开始获取基准指数 {index_code} 的历史数据（最近{days}天）")

            # 确定市场前缀
            if index_code.startswith('00'):
                symbol = f"sh{index_code}"
            elif index_code.startswith('30') or index_code.startswith('39'):
                symbol = f"sz{index_code}"
            else:
                symbol = f"sh{index_code}"

            df = ak.stock_zh_index_daily(symbol=symbol)

            if df is None or df.empty:
                logger.warning(f"获取基准指数 {index_code} 历史数据失败：返回数据为空")
                return pd.DataFrame()

            # 处理列名
            df = self._process_daily_data(df)

            # 筛选最近N天
            if 'date' in df.columns:
                df = df.sort_values('date').tail(days)

            logger.debug(f"成功获取基准指数 {index_code} 的历史数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取基准指数 {index_code} 历史数据失败: {e}", exc_info=True)
            return pd.DataFrame()

    def get_industry_list(self) -> List[Dict]:
        """
        获取所有行业列表

        Returns:
            行业列表，每个元素为包含 industry_code 和 name 的字典
        """
        try:
            logger.debug("开始获取行业列表")

            # 获取东方财富行业板块信息
            df = ak.stock_board_industry_name_em()

            if df is None or df.empty:
                logger.warning("获取行业列表失败：返回数据为空")
                return []

            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                # 使用板块代码作为 industry_code
                result.append({
                    'industry_code': str(row.get('板块代码', '')),
                    'name': str(row.get('板块名称', '')),
                })

            logger.info(f"获取行业列表成功，共 {len(result)} 个行业")
            return result

        except Exception as e:
            logger.error(f"获取行业列表失败: {e}", exc_info=True)
            return []

    def get_convertible_by_industry(self, industry_name: str) -> List[Dict]:
        """
        获取指定行业的可转债列表

        Args:
            industry_name: 行业名称（如 "电子"）

        Returns:
            该行业内的可转债列表，每个元素包含 cb_code, cb_name, stock_code
        """
        try:
            logger.debug(f"开始获取行业 '{industry_name}' 的可转债列表")

            # 获取所有可转债
            all_bonds = self.get_convertible_list()
            if not all_bonds:
                return []

            # 获取行业内股票列表
            industry_stocks = self.get_stock_by_industry(industry_name)
            if not industry_stocks:
                logger.warning(f"行业 '{industry_name}' 中没有找到股票")
                return []

            # 提取行业股票代码集合
            stock_codes = {s.get('代码', '') for s in industry_stocks}

            # 筛选属于该行业的可转债
            result = []
            for bond in all_bonds:
                stock_code = bond.get('正股代码', '')
                if stock_code in stock_codes:
                    result.append({
                        'cb_code': bond.get('代码'),
                        'cb_name': bond.get('转债名称'),
                        'stock_code': stock_code,
                        'stock_name': bond.get('正股名称', ''),
                    })

            logger.info(f"行业 '{industry_name}' 中找到 {len(result)} 只可转债")
            return result

        except Exception as e:
            logger.error(f"获取行业 '{industry_name}' 可转债失败: {e}", exc_info=True)
            return []

    def get_stock_by_industry(self, industry_name: str) -> List[Dict]:
        """
        获取指定行业的股票列表

        Args:
            industry_name: 行业名称

        Returns:
            该行业内的股票列表
        """
        try:
            logger.debug(f"开始获取行业 '{industry_name}' 的股票列表")

            # 获取行业板块成分股
            df = ak.stock_board_industry_cons_em(symbol=industry_name)

            if df is None or df.empty:
                logger.warning(f"获取行业 '{industry_name}' 股票列表失败：返回数据为空")
                return []

            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                result.append({
                    '代码': str(row.get('代码', '')),
                    '名称': str(row.get('名称', '')),
                })

            logger.info(f"行业 '{industry_name}' 中找到 {len(result)} 只股票")
            return result

        except Exception as e:
            logger.error(f"获取行业 '{industry_name}' 股票列表失败: {e}", exc_info=True)
            return []

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

    def get_lof_list(self) -> pd.DataFrame:
        """
        获取所有LOF基金列表

        Returns:
            DataFrame with columns: code, name, fund_type
        """
        try:
            # 使用基金搜索接口获取LOF列表
            # 先获取开放式基金列表，然后筛选LOF
            df = ak.fund_open_fund_info_em(fund="LOF", indicator="单位净值走势")

            if df is None or df.empty:
                # 备用方法：尝试使用其他接口
                logger.warning("fund_open_fund_info_em接口失败，尝试备用方法")
                return pd.DataFrame(columns=['code', 'name', 'fund_type'])

            # 提取LOF基金代码和名称
            lof_list = []
            # 常见LOF代码前缀和知名LOF（包含更多商品LOF）
            known_lof = [
                # 商品类LOF - 黄金/贵金属
                ('161116', '黄金基金'),
                ('518880', '黄金ETF'),
                ('159998', '黄金ETF'),
                ('159937', '黄金ETF'),

                # 商品类LOF - 白银/有色
                ('163415', '白银LOF'),
                ('161226', '白银LOF'),
                ('161215', '白银基金'),

                # 商品类LOF - 油气/能源
                ('162411', '华宝油气'),
                ('160416', '油气基金'),
                ('162719', '石油基金'),
                ('160613', '鹏华钢铁'),
                ('165513', '信诚商品'),

                # 商品类LOF - 大宗商品/资源
                ('160723', '大宗商品'),
                ('161217', '国泰商品'),
                ('161025', '大宗商品'),
                ('163812', '资源LOF'),
                ('161815', '资源优选'),

                # 海外指数LOF
                ('164901', '海外中国'),
                ('162715', '纳指LOF'),
                ('165510', '标普LOF'),
                ('166105', '海外科技'),
                ('166106', '海外消费'),

                # 其他常见LOF
                ('160716', '嘉实沪深300ETF联接'),
                ('163407', '兴全合润'),
            ]

            for code, name in known_lof:
                lof_list.append({
                    'code': code,
                    'name': name,
                    'fund_type': 'LOF'
                })

            lof_df = pd.DataFrame(lof_list)
            logger.info(f"获取LOF列表成功，共 {len(lof_df)} 只")
            return lof_df

        except Exception as e:
            logger.error(f"获取LOF列表失败: {e}", exc_info=True)
            # 返回预设的LOF列表作为备用（扩展版）
            lof_list = [
                # 商品类LOF - 黄金/贵金属
                ('161116', '黄金基金'),
                ('518880', '黄金ETF'),
                ('159998', '黄金ETF'),
                ('159937', '黄金ETF'),

                # 商品类LOF - 白银/有色
                ('163415', '白银LOF'),
                ('161226', '白银LOF'),
                ('161215', '白银基金'),

                # 商品类LOF - 油气/能源
                ('162411', '华宝油气'),
                ('160416', '油气基金'),
                ('162719', '石油基金'),
                ('160613', '鹏华钢铁'),
                ('165513', '信诚商品'),

                # 商品类LOF - 大宗商品/资源
                ('160723', '大宗商品'),
                ('161217', '国泰商品'),
                ('161025', '大宗商品'),
                ('163812', '资源LOF'),
                ('161815', '资源优选'),

                # 海外指数LOF
                ('164901', '海外中国'),
                ('162715', '纳指LOF'),
                ('165510', '标普LOF'),
                ('166105', '海外科技'),
                ('166106', '海外消费'),

                # 其他常见LOF
                ('160716', '嘉实300'),
                ('163407', '兴全合润'),
            ]
            lof_df = pd.DataFrame([
                {'code': code, 'name': name, 'fund_type': 'LOF'}
                for code, name in lof_list
            ])
            logger.info(f"使用备用LOF列表，共 {len(lof_df)} 只")
            return lof_df

    def get_commodity_lof_list(self) -> List[Dict]:
        """
        获取大宗商品LOF列表

        Returns:
            List of dict: [{'code': 'xxx', 'name': 'xxx', 'type': 'LOF'}]
        """
        try:
            lof_df = self.get_lof_list()
            commodity_keywords = ['商品', '黄金', '原油', '石油', '白银', '油气',
                                  '有色金属', '能源', '农产品', '豆粕', '煤炭',
                                  '钢铁', '资源', '华宝', '国泰', '信诚']

            commodity_lof = []
            for _, row in lof_df.iterrows():
                name = row['name']
                if any(keyword in name for keyword in commodity_keywords):
                    commodity_lof.append({
                        'code': row['code'],
                        'name': name,
                        'type': 'LOF'
                    })

            logger.info(f"找到{len(commodity_lof)}个大宗商品LOF")
            return commodity_lof
        except Exception as e:
            logger.error(f"获取大宗商品LOF列表失败: {e}", exc_info=True)
            return []

    def get_overseas_etf_list(self) -> List[Dict]:
        """
        获取海外相关ETF列表

        Returns:
            List of dict: [{'code': 'xxx', 'name': 'xxx', 'type': 'ETF'}]
        """
        try:
            # 获取ETF列表
            etf_df = ak.fund_etf_category_sina(symbol="ETF基金")

            # 扩充关键词列表，涵盖更多国家和地区
            overseas_keywords = [
                # 地区/市场
                '美股', '港股', '德国', '日本', '美国', '纳斯达克',
                '标普', '恒生', '欧洲', '亚太', '全球',
                '英国', '法国', '沙特', '巴西', '印度', '越南',
                '澳洲', '澳大利亚', '韩国', '台湾', '意大利', '西班牙',
                '加拿大', '墨西哥', '印尼', '泰国', '马来西亚', '新加坡',

                # 指数名称
                '标普500', '纳斯达克100', '恒生', 'H股', '红筹', '国企',
                '日经', '德国DAX', '英国富时', '法国CAC', '富时',
                '印度SENSEX', '越南VN', '韩国KOSPI', '标普',

                # 投资主题
                '跨境', 'QDII', '海外', '国际', '出境',

                # 行业/商品类（可能有海外属性）
                '油气', '原油', '生物', '医药', '科技', '半导体', '消费'
            ]

            overseas_etf = []
            for _, row in etf_df.iterrows():
                # 兼容中文列名
                name = row.get('name') or row.get('名称', '')
                code = row.get('code') or row.get('代码', '')
                # 去除代码前缀（如sz159998 -> 159998）
                clean_code = code.replace('sz', '').replace('sh', '') if code else ''

                if any(keyword in name for keyword in overseas_keywords):
                    overseas_etf.append({
                        'code': clean_code,
                        'name': name,
                        'type': 'ETF'
                    })

            logger.info(f"找到{len(overseas_etf)}个海外ETF")
            return overseas_etf
        except Exception as e:
            logger.error(f"获取海外ETF列表失败: {e}", exc_info=True)
            # 返回预设的海外ETF列表作为备用
            overseas_etf = [
                # 日本 - 波动较大
                ('513350', '日经225ETF'),
                ('513000', '日经225ETF'),
                ('513280', '日经225ETF'),
                ('513300', '东京证券指数'),

                # 美国科技股 - 波动较大
                ('513100', '纳斯达克ETF'),
                ('159941', '纳斯达克100'),
                ('513500', '标普500ETF'),
                ('513680', '标普科技ETF'),

                # 亚洲市场
                ('513600', '南方恒生ETF'),
                ('159920', '恒生ETF'),
                ('513650', '恒生科技ETF'),
                ('513180', '恒生互联网'),
                ('159760', '港股科技ETF'),

                # 欧洲
                ('513030', '德国DAX'),
                ('513020', '欧洲股票'),

                # 全球/新兴市场
                ('513900', '香港证券ETF'),
                ('513800', '亚洲精选'),
                ('513200', '亚太股票'),

                # 黄金/贵金属ETF
                ('518880', '黄金ETF'),
                ('159998', '黄金ETF'),
                ('159937', '黄金ETF'),
                ('159934', '白银ETF'),

                # 商品/原油ETF
                ('162411', '华宝油气'),
                ('160416', '油气基金'),
            ]
            return [
                {'code': code, 'name': name, 'type': 'ETF'}
                for code, name in overseas_etf
            ]

    def get_lof_etf_history(self, symbol: str, period: int = 100) -> Optional[pd.DataFrame]:
        """
        获取LOF/ETF历史行情数据（带分层缓存）

        分层缓存策略：
        - 超过30天的历史数据：按月缓存，长期有效
        - 7-30天的数据：按周缓存，每周更新
        - 最近7天的数据：按天缓存，每日更新

        Args:
            symbol: 基金代码
            period: 获取天数，默认100天

        Returns:
            DataFrame with columns: date, open, close, high, low, volume, amount
            or None if failed
        """
        import time
        import os
        from datetime import datetime, timedelta

        cache_dir = os.path.expanduser("~/.cache/money-agent/etf_data")
        os.makedirs(cache_dir, exist_ok=True)

        now = datetime.now()
        end_date = now
        start_date = now - timedelta(days=period)

        # 尝试从分层缓存加载数据
        cached_data = self._load_tiered_cache(symbol, start_date, end_date, cache_dir)
        if cached_data is not None and len(cached_data) > 0:
            # 检查缓存数据是否足够
            cached_start = cached_data.index.min()
            if cached_start <= start_date:
                logger.info(f"使用分层缓存数据 {symbol}，共{len(cached_data)}条记录")
                return cached_data
            else:
                # 缓存数据不足，需要获取更多历史数据
                needed_start_date = cached_start - timedelta(days=30)
                logger.info(f"缓存数据不足，需要获取 {needed_start_date.strftime('%Y-%m-%d')} 至今的数据")

        # 从网络获取数据
        df_fresh = self._fetch_from_network(symbol, period, cache_dir)
        if df_fresh is not None and len(df_fresh) > 0:
            # 保存到分层缓存
            self._save_to_tiered_cache(symbol, df_fresh, cache_dir)
            return df_fresh

        return None

    def _load_tiered_cache(self, symbol: str, start_date: datetime, end_date: datetime, cache_dir: str) -> Optional[pd.DataFrame]:
        """
        从分层缓存加载数据

        Returns:
            合并后的DataFrame，或None
        """
        import time
        from datetime import timedelta
        import os

        dfs = []
        now = end_date if isinstance(end_date, datetime) else datetime.now()

        # 1. 检查最近周缓存（最近7天，24小时有效）
        week_cache = os.path.join(cache_dir, f"{symbol}_week.csv")
        if os.path.exists(week_cache):
            cache_time = os.path.getmtime(week_cache)
            age_hours = (time.time() - cache_time) / 3600
            if age_hours < 24:
                try:
                    df = pd.read_csv(week_cache, index_col=0, parse_dates=True)
                    dfs.append(df)
                    logger.debug(f"加载最近周缓存 {symbol}")
                except Exception as e:
                    logger.warning(f"读取周缓存失败: {e}")

        # 2. 检查周度缓存（7-30天）
        week_iter_start = now - timedelta(days=7)
        week_iter_end = now - timedelta(days=30)
        current_date = week_iter_start
        while current_date > week_iter_end:
            week_num = current_date.isocalendar()[1]
            year = current_date.year
            week_file = os.path.join(cache_dir, f"{symbol}_w{year}_{week_num:02d}.csv")
            if os.path.exists(week_file):
                try:
                    df = pd.read_csv(week_file, index_col=0, parse_dates=True)
                    dfs.append(df)
                except Exception:
                    pass
            current_date = current_date - timedelta(days=7)

        # 3. 检查月度缓存（30天以前）
        month_iter_end = start_date
        current_month = now.replace(day=1)
        while current_month > month_iter_end:
            month_file = os.path.join(cache_dir, f"{symbol}_m{current_month.year}_{current_month.month:02d}.csv")
            if os.path.exists(month_file):
                try:
                    df = pd.read_csv(month_file, index_col=0, parse_dates=True)
                    dfs.append(df)
                except Exception:
                    pass
            # 移动到上个月
            if current_month.month == 1:
                current_month = current_month.replace(year=current_month.year - 1, month=12)
            else:
                current_month = current_month.replace(month=current_month.month - 1)

        # 合并所有缓存数据
        if dfs:
            try:
                merged = pd.concat(dfs)
                merged = merged[~merged.index.duplicated(keep='last')]
                merged = merged.sort_index()
                # 只返回需要的时间范围
                merged = merged[(merged.index >= start_date) & (merged.index <= end_date)]
                return merged
            except Exception as e:
                logger.warning(f"合并缓存数据失败: {e}")

        return None

    def _save_to_tiered_cache(self, symbol: str, df: pd.DataFrame, cache_dir: str):
        """
        将数据保存到分层缓存
        """
        from datetime import timedelta
        import os

        now = datetime.now()

        # 按时间分割数据
        recent_week = df[df.index >= (now - timedelta(days=7))]
        recent_month = df[(df.index >= (now - timedelta(days=30))) & (df.index < (now - timedelta(days=7)))]
        older = df[df.index < (now - timedelta(days=30))]

        # 保存最近周数据（每日更新）
        if len(recent_week) > 0:
            week_file = os.path.join(cache_dir, f"{symbol}_week.csv")
            recent_week.to_csv(week_file)
            logger.debug(f"保存最近周数据 {symbol}，{len(recent_week)}条")

        # 保存最近月数据（按周分割）
        if len(recent_month) > 0:
            week_start = now - timedelta(days=7)
            for week_offset in range(0, 4):
                w_start = week_start - timedelta(days=week_offset * 7)
                w_end = w_start + timedelta(days=7)
                week_data = recent_month[(recent_month.index >= w_start) & (recent_month.index < w_end)]
                if len(week_data) > 0:
                    week_num = w_start.isocalendar()[1]
                    year = w_start.year
                    week_file = os.path.join(cache_dir, f"{symbol}_w{year}_{week_num:02d}.csv")
                    # 如果文件已存在，不覆盖（周度数据相对稳定）
                    if not os.path.exists(week_file):
                        week_data.to_csv(week_file)

        # 保存更早的数据（按月分割）
        if len(older) > 0:
            for month_key, month_data in older.groupby([older.index.year, older.index.month]):
                year, month = month_key
                month_file = os.path.join(cache_dir, f"{symbol}_m{year}_{month:02d}.csv")
                # 如果文件已存在，不覆盖（历史数据稳定）
                if not os.path.exists(month_file):
                    month_data.to_csv(month_file)
                    logger.debug(f"保存月度数据 {symbol} {year}-{month:02d}，{len(month_data)}条")

    def _fetch_from_network(self, symbol: str, period: int, cache_dir: str) -> Optional[pd.DataFrame]:
        """
        从网络获取数据（内部方法）
        """
        import time
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')

        # 方法1: 尝试使用日线数据接口
        for attempt in range(2):
            try:
                time.sleep(1)

                df = ak.fund_etf_hist_em(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=""
                )

                if df is not None and len(df) > 0:
                    # 标准化列名
                    df = df[['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']].copy()
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)

                    # 确保数据类型正确
                    for col in ['open', 'close', 'high', 'low']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

                    logger.info(f"从网络获取{symbol}历史数据成功，共{len(df)}条记录")
                    return df

            except Exception as e:
                logger.error(f"获取{symbol}历史数据失败 (尝试 {attempt+1}/2): {e}")
                time.sleep(2)

        # 方法2: 使用分钟数据备用方案
        try:
            logger.info(f"尝试使用分钟数据接口获取 {symbol}...")
            time.sleep(1)

            df_min = ak.fund_etf_hist_min_em(symbol=symbol, period='1', adjust='')
            if df_min is not None and len(df_min) > 0:
                df_min.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'avg_price']
                df_min['date'] = pd.to_datetime(df_min['date'])

                df_min.set_index('date', inplace=True)
                df_daily = df_min.resample('D').agg({
                    'open': 'first',
                    'close': 'last',
                    'high': 'max',
                    'low': 'min',
                    'volume': 'sum',
                    'amount': 'sum'
                }).dropna()

                cutoff_date = datetime.now() - timedelta(days=period)
                df_daily = df_daily[df_daily.index >= cutoff_date]

                logger.info(f"通过分钟数据获取{symbol}成功，共{len(df_daily)}条记录")
                return df_daily

        except Exception as e:
            logger.error(f"分钟数据接口失败: {e}")

        # 方法3: sina备用接口
        try:
            df = ak.fund_etf_hist_sina(symbol=symbol)
            if df is not None and len(df) > 0:
                df.index = pd.to_datetime(df.index)
                column_mapping = {
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume'
                }
                df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
                required_cols = ['open', 'close', 'high', 'low']
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = df['close']
                if 'volume' not in df.columns:
                    df['volume'] = 0

                logger.info(f"通过sina接口获取{symbol}成功")
                return df
        except Exception as e:
            logger.error(f"sina接口失败: {e}")

        return None
