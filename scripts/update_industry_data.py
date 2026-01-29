"""
更新行业数据脚本
将 AKShare 行业数据保存到本地文件
"""

import akshare as ak
import pandas as pd
import json
from pathlib import Path


def update_industry_data():
    """更新行业数据到本地文件"""

    # 数据目录
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 获取行业列表
    print("正在获取行业列表...")
    df = ak.stock_board_industry_name_em()

    print(f"获取成功！共 {len(df)} 个行业")

    # 保存为 CSV（用于查看）
    csv_path = data_dir / "industries.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"已保存到: {csv_path}")

    # 保存为 JSON（用于程序读取）
    industries = []
    for _, row in df.iterrows():
        industries.append({
            'industry_code': str(row['板块代码']),
            'name': str(row['板块名称']),
        })

    json_path = data_dir / "industries.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(industries, f, ensure_ascii=False, indent=2)
    print(f"已保存到: {json_path}")

    print(f"\n行业列表前10个:")
    for ind in industries[:10]:
        print(f"  - {ind['name']} ({ind['industry_code']})")

    return industries


if __name__ == "__main__":
    update_industry_data()
    print("\n✅ 行业数据更新完成！")
