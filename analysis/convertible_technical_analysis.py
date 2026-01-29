"""
可转债技术面与条款分析模块
Convertible Bond Technical and Terms Analysis Module
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher


logger = logging.getLogger(__name__)


@dataclass
class ConvertibleTechnicalData:
    """可转债技术面数据"""

    # 基础信息
    cb_code: str
    cb_name: str

    # 基础行情
    price: float
    change_percent: float
    volume: float
    amount: float

    # 转股相关
    conversion_price: float      # 转股价
    conversion_value: float      # 转股价值
    premium_rate: float          # 转股溢价率

    # 债券属性
    bond_rating: str             # 评级
    pure_bond_value: float       # 纯债价值
    ytm: float                   # 到期收益率

    # 条款信息
    call_trigger_price: float    # 强赎触发价
    put_trigger_price: float     # 回售触发价
    conversion_trigger_price: float  # 下修触发价

    # 市场深度
    bid_price: List[float]       # 买一到买五
    ask_price: List[float]       # 卖一到卖五
    bid_volume: List[float]      # 买量
    ask_volume: List[float]      # 卖量

    # 技术指标
    ma5: float                   # 5日均线
    ma20: float                  # 20日均线
    volatility_20d: float        # 20日波动率
