"""
可转债分析示例脚本
演示如何使用 ConvertibleBondAnalyzer 进行可转债分析
"""

import asyncio
from core.agent.glm_agent import GLMAgent
from analysis.convertible_analysis import ConvertibleBondAnalyzer


async def main():
    """主函数"""
    # 初始化 Agent
    agent = GLMAgent()

    # 创建可转债分析器
    analyzer = ConvertibleBondAnalyzer(agent)

    # 示例1：分析单个可转债
    print("=" * 60)
    print("示例1：分析单个可转债")
    print("=" * 60)

    result = analyzer.analyze_convertible(
        cb_code="113527",
        cb_name="兴业转债"
    )

    if result:
        print(f"\n可转债代码：{result['cb_code']}")
        print(f"可转债名称：{result['cb_name']}")
        print(f"\n分析摘要：\n{result['summary']}")
        print(f"\n完整分析：\n{result['analysis']}")
    else:
        print("分析失败")

    # 示例2：获取可转债列表
    print("\n" + "=" * 60)
    print("示例2：获取可转债列表")
    print("=" * 60)

    cb_list = analyzer.get_convertible_list()

    if cb_list:
        print(f"\n共获取到 {len(cb_list)} 只可转债")
        print("\n前5只可转债：")
        for i, cb in enumerate(cb_list[:5], 1):
            print(f"{i}. {cb['cb_name']} ({cb['cb_code']}) - 价格: {cb.get('price', 'N/A')}")
    else:
        print("获取可转债列表失败")

    # 示例3：双低策略筛选
    print("\n" + "=" * 60)
    print("示例3：双低策略筛选")
    print("=" * 60)

    screened = analyzer.screen_double_low(
        max_price=110.0,
        max_premium=30.0,
        top_n=5
    )

    if screened:
        print(f"\n筛选出 {len(screened)} 只双低可转债：")
        for i, cb in enumerate(screened, 1):
            print(
                f"{i}. {cb['cb_name']} ({cb['cb_code']}) - "
                f"价格: {cb['price']:.2f}, "
                f"溢价率: {cb['premium']:.2f}%, "
                f"双低值: {cb['double_low']:.2f}"
            )
    else:
        print("筛选失败或没有符合条件的可转债")


if __name__ == "__main__":
    asyncio.run(main())
