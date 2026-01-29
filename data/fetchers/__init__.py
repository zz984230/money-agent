# Data fetchers module for Money Agent project

from .akshare_fetcher import AKShareFetcher
from .akshare_financial_fetcher import AKShareFinancialFetcher

__all__ = ['AKShareFetcher', 'AKShareFinancialFetcher']
