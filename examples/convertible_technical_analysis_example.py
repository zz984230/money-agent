"""
可转债技术面分析示例
Convertible Bond Technical Analysis Example
"""

from core.agent.glm_agent import GLMAgent
from analysis.convertible_technical_analysis import ConvertibleBondTechnicalAnalyzer


def main():
    """主函数"""
    # 初始化
    agent = GLMAgent()
    analyzer = ConvertibleBondTechnicalAnalyzer(agent)

    print("=" * 60)
    print("可转债技术面分析示例")
    print("=" * 60)

    # 示例1: 单券技术面分析
    print("\n【示例1】单券技术面分析")
    print("-" * 60)

    result = analyzer.analyze_technical('113527')

    if result:
        print(f"\n转债: {result.cb_name} ({result.cb_code})")
        print(f"价格: {result.technical_data.price}元")
        print(f"涨跌幅: {result.technical_data.change_percent}%")
        print(f"类型: {result.signals.get('type') if isinstance(result.signals, dict) else 'N/A'}")
        print(f"\nAI分析:\n{result.analysis}")
        print(f"\n建议: {result.recommendation}")
    else:
        print("分析失败")

    # 示例2: 条款博弈分析
    print("\n" + "=" * 60)
    print("【示例2】条款博弈分析")
    print("-" * 60)

    terms_result = analyzer.analyze_terms(
        cb_code='113527',
        stock_price=125.0,
        stock_name='利民股份'
    )

    if terms_result:
        print(f"\n转债: {terms_result['cb_name']} ({terms_result['cb_code']})")
        print(f"正股价格: {terms_result['stock_price']}元")
        print(f"强赎距离: {terms_result['call_distance']:.2f}%")
        print(f"回售距离: {terms_result['put_distance']:.2f}%")
        print(f"\n分析:\n{terms_result['full_analysis']}")
    else:
        print("分析失败")

    # 示例3: 技术面筛选
    print("\n" + "=" * 60)
    print("【示例3】技术面筛选")
    print("-" * 60)

    screen_results = analyzer.screen_by_technical(
        criteria={"price_range": (100, 110), "premium_max": 20},
        top_n=5
    )

    if screen_results:
        print(f"\n找到 {len(screen_results)} 只转债:")
        for i, r in enumerate(screen_results, 1):
            print(f"  {i}. {r['cb_name']} ({r['cb_code']}): {r['price']:.2f}元, 评分:{r['score']:.1f}")
    else:
        print("未找到符合条件的转债")


if __name__ == '__main__':
    main()
