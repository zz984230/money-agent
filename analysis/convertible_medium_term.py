"""
可转债中期量化分析模块
Convertible Bond Medium-Term Quantitative Analysis Module
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from core.agent.base_agent import BaseAgent
from core.agent.prompts import PromptBuilder
from data.fetchers.akshare_fetcher import AKShareFetcher
from analysis.convertible_medium_term_factors import (
    MediumTermFactorCalculator,
    IndustryFactorResult,
    BondFactorResult
)


logger = logging.getLogger(__name__)


@dataclass
class MediumTermScreenResult:
    """中期量化筛选结果"""
    industries: List[IndustryFactorResult]
    bonds: List[Dict]
    ai_analysis: str


class ConvertibleBondMediumTermAnalyzer:
    """可转债中期量化分析器"""

    def __init__(self, agent: BaseAgent):
        """
        初始化分析器

        Args:
            agent: AI Agent实例
        """
        self.agent = agent
        self.prompt_builder = PromptBuilder()
        self.fetcher = AKShareFetcher()
        self.factor_calculator = MediumTermFactorCalculator()

    def screen_top_industries(
        self,
        top_n: int = 5,
        benchmark_code: str = "000300"
    ) -> List[IndustryFactorResult]:
        """
        筛选强势行业

        Args:
            top_n: 返回前N个强势行业
            benchmark_code: 基准指数代码（默认沪深300）

        Returns:
            按综合评分排序的强势行业列表
        """
        try:
            logger.info(f"开始筛选前{top_n}个强势行业")

            # 1. 获取所有行业
            industries = self.fetcher.get_industry_list()
            if not industries:
                logger.warning("获取行业列表失败")
                return []

            # 2. 获取基准指数数据
            benchmark_df = self.fetcher.get_benchmark_index_hist(benchmark_code, days=120)

            # 3. 计算每个行业的因子
            industry_results = []

            for industry in industries[:30]:  # 限制处理数量避免超时
                industry_code = industry.get('industry_code', '')
                industry_name = industry.get('name', '')

                if not industry_code:
                    continue

                try:
                    # 获取行业指数数据
                    industry_df = self.fetcher.get_industry_index_hist(
                        f"_{industry_code}",
                        days=120
                    )

                    if industry_df is None or industry_df.empty:
                        continue

                    # 计算因子
                    momentum_60d = self.factor_calculator.calculate_industry_momentum(industry_df, 60)
                    momentum_120d = self.factor_calculator.calculate_industry_momentum(industry_df, 120)
                    relative_strength = self.factor_calculator.calculate_industry_relative_strength(
                        industry_df,
                        benchmark_df,
                        60
                    )

                    # 成交额占比暂时设为0（需要额外数据源）
                    volume_ratio = 0.0

                    result = IndustryFactorResult(
                        industry_code=industry_code,
                        industry_name=industry_name,
                        momentum_60d=momentum_60d,
                        momentum_120d=momentum_120d,
                        relative_strength=relative_strength,
                        volume_ratio=volume_ratio
                    )

                    industry_results.append(result)

                except Exception as e:
                    logger.warning(f"处理行业 {industry_name} 失败: {e}")
                    continue

            # 4. 综合评分并排序
            industry_results.sort(
                key=lambda x: self._calculate_industry_score(x),
                reverse=True
            )

            # 5. 返回Top N
            result = industry_results[:top_n]

            logger.info(f"筛选完成，识别出{len(result)}个强势行业")
            return result

        except Exception as e:
            logger.error(f"筛选强势行业失败: {e}", exc_info=True)
            return []

    def _calculate_industry_score(self, industry: IndustryFactorResult) -> float:
        """
        计算行业综合评分

        Args:
            industry: 行业因子结果

        Returns:
            综合评分
        """
        # 权重：相对强弱50%，60日动量30%，120日动量20%
        score = (
            industry.relative_strength * 0.5 +
            industry.momentum_60d * 0.3 +
            industry.momentum_120d * 0.2
        )
        return score

    def medium_term_screen(
        self,
        top_n_industries: int = 5,
        top_n_bonds: int = 5,
        premium_max: float = 20.0,
        bond_type_filter: Optional[str] = None
    ) -> Optional[MediumTermScreenResult]:
        """
        完整的中期量化筛选流程

        Args:
            top_n_industries: 筛选前N个强势行业
            top_n_bonds: 每个行业筛选前N只转债
            premium_max: 最大溢价率
            bond_type_filter: 转债类型过滤（None/偏股型/平衡型/偏债型）

        Returns:
            MediumTermScreenResult对象
        """
        try:
            logger.info("开始中期量化筛选")

            # 1. 筛选强势行业
            industries = self.screen_top_industries(top_n=top_n_industries)

            if not industries:
                logger.warning("未识别出强势行业")
                return None

            # 2. 对每个行业筛选转债
            all_bonds = []

            for industry in industries:
                bonds = self._screen_bonds_in_industry(
                    industry,
                    top_n=top_n_bonds,
                    premium_max=premium_max,
                    bond_type_filter=bond_type_filter
                )
                all_bonds.extend(bonds)

            # 3. 按综合评分排序
            all_bonds.sort(key=lambda x: x.get('score', 0), reverse=True)

            # 4. AI分析
            ai_analysis = self._generate_ai_analysis(industries, all_bonds[:10])

            result = MediumTermScreenResult(
                industries=industries,
                bonds=all_bonds,
                ai_analysis=ai_analysis
            )

            logger.info(f"中期量化筛选完成，共筛选出{len(all_bonds)}只转债")
            return result

        except Exception as e:
            logger.error(f"中期量化筛选失败: {e}", exc_info=True)
            return None

    def _screen_bonds_in_industry(
        self,
        industry: IndustryFactorResult,
        top_n: int,
        premium_max: float,
        bond_type_filter: Optional[str]
    ) -> List[Dict]:
        """
        筛选行业内的转债

        Args:
            industry: 行业因子结果
            top_n: 返回前N只
            premium_max: 最大溢价率
            bond_type_filter: 类型过滤

        Returns:
            转债列表
        """
        try:
            # 获取行业内转债
            bonds = self.fetcher.get_convertible_by_industry(industry.industry_name)

            if not bonds:
                return []

            scored_bonds = []

            for bond in bonds:
                try:
                    cb_code = bond.get('cb_code')
                    if not cb_code:
                        continue

                    # 获取详细信息
                    detail = self.fetcher.get_convertible_detail(cb_code)
                    if not detail:
                        continue

                    # 应用筛选条件
                    premium_rate = detail.get('premium_rate', 100)

                    if premium_rate > premium_max:
                        continue

                    # 计算转债类型
                    conversion_value = detail.get('conversion_value', 0)
                    pure_value = 100.0  # 默认纯债价值

                    bond_type = self.factor_calculator.determine_bond_type(
                        conversion_value,
                        pure_value
                    )

                    if bond_type_filter and bond_type != bond_type_filter:
                        continue

                    # 计算综合评分
                    score = self._calculate_bond_score(
                        bond,
                        detail,
                        industry
                    )

                    scored_bonds.append({
                        'cb_code': cb_code,
                        'cb_name': bond.get('cb_name'),
                        'industry': industry.industry_name,
                        'premium_rate': premium_rate,
                        'bond_type': bond_type,
                        'score': score,
                        'industry_score': self._calculate_industry_score(industry)
                    })

                except Exception as e:
                    logger.warning(f"处理转债 {bond.get('cb_code')} 失败: {e}")
                    continue

            # 排序并返回Top N
            scored_bonds.sort(key=lambda x: x['score'], reverse=True)
            return scored_bonds[:top_n]

        except Exception as e:
            logger.error(f"筛选行业内转债失败: {e}", exc_info=True)
            return []

    def _calculate_bond_score(
        self,
        bond: Dict,
        detail: Dict,
        industry: IndustryFactorResult
    ) -> float:
        """
        计算个券综合评分

        Args:
            bond: 转债基础信息
            detail: 转债详细信息
            industry: 所属行业信息

        Returns:
            综合评分
        """
        score = 0.0

        # 行业强度 40%
        industry_score = self._calculate_industry_score(industry)
        score += industry_score * 0.4

        # 估值优势 30% (溢价率越低越好)
        premium_rate = detail.get('premium_rate', 50)
        valuation_score = max(0, 30 - premium_rate)
        score += valuation_score * 0.3

        # 转债类型 20%
        conversion_value = detail.get('conversion_value', 0)
        if conversion_value > 130:
            type_score = 100
        elif conversion_value > 100:
            type_score = 70
        else:
            type_score = 40
        score += type_score * 0.2

        # YTM 10%
        ytm = detail.get('ytm', 0)
        score += min(ytm * 10, 10) * 0.1

        return score

    def _generate_ai_analysis(
        self,
        industries: List[IndustryFactorResult],
        top_bonds: List[Dict]
    ) -> str:
        """
        生成AI分析报告

        Args:
            industries: 强势行业列表
            top_bonds: Top转债列表

        Returns:
            AI分析文本
        """
        try:
            prompt = self.prompt_builder.build_medium_term_analysis_prompt(
                industries,
                top_bonds
            )

            analysis = self.agent.chat(prompt)
            return analysis or "暂无AI分析"

        except Exception as e:
            logger.error(f"生成AI分析失败: {e}", exc_info=True)
            return "AI分析暂不可用"
