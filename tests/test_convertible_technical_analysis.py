"""
测试可转债技术面分析模块
"""

import pytest
from dataclasses import asdict
from analysis.convertible_technical_analysis import ConvertibleTechnicalData

class TestConvertibleTechnicalData:
    """测试ConvertibleTechnicalData数据类"""

    def test_create_minimal_data(self):
        """测试创建最小数据集"""
        data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[],
            ask_price=[],
            bid_volume=[],
            ask_volume=[],
            ma5=0.0,
            ma20=0.0,
            volatility_20d=0.0,
        )

        assert data.cb_code == "113527"
        assert data.price == 105.5
        assert data.premium_rate == 15.5

    def test_data_serialization(self):
        """测试数据序列化"""
        data = ConvertibleTechnicalData(
            cb_code="113527",
            cb_name="利民转债",
            price=105.5,
            change_percent=1.2,
            volume=1000000,
            amount=105500000,
            conversion_price=20.5,
            conversion_value=102.0,
            premium_rate=15.5,
            bond_rating="AA",
            pure_bond_value=95.0,
            ytm=-2.5,
            call_trigger_price=130.0,
            put_trigger_price=90.0,
            conversion_trigger_price=20.5,
            bid_price=[104.5, 104.4],
            ask_price=[105.5, 105.6],
            bid_volume=[1000, 2000],
            ask_volume=[1000, 2000],
            ma5=104.5,
            ma20=103.0,
            volatility_20d=2.5,
        )

        result = asdict(data)

        assert isinstance(result, dict)
        assert result['cb_code'] == "113527"
        assert len(result['bid_price']) == 2
