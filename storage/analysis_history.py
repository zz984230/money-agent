"""分析历史记录管理器"""
import json
import csv
import logging
import textwrap
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AnalysisHistoryEntry:
    """单条分析历史记录"""
    id: str                    # 唯一ID (时间戳+基金代码)
    symbol: str                # 基金代码
    name: str                  # 基金名称
    fund_type: str             # 基金类型 (LOF/ETF)
    created_at: str            # 创建时间 (ISO 8601格式)

    # 分析结果快照
    abnormal_events_count: int
    current_price: float
    ai_summary: str            # AI分析完整内容
    current_factors: Dict[str, Any]      # 当前因子数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisHistoryEntry':
        """从字典创建实例"""
        return cls(**data)


class AnalysisHistoryManager:
    """分析历史记录管理器"""

    def __init__(self, cache_dir: Path):
        """
        初始化管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "analysis_history.json"
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict[str, Any]:
        """加载JSON数据"""
        if not self.cache_file.exists():
            return {"entries": []}

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load analysis history from {self.cache_file}: {e}")
            return {"entries": []}

    def _save_data(self, data: Dict[str, Any]) -> bool:
        """保存JSON数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save analysis history to {self.cache_file}: {e}")
            return False

    def add_entry(self, entry: AnalysisHistoryEntry) -> bool:
        """
        添加历史记录

        Args:
            entry: 历史记录条目

        Returns:
            是否成功添加
        """
        data = self._load_data()
        data["entries"].insert(0, entry.to_dict())  # 最新的在前
        return self._save_data(data)

    def get_all_entries(self) -> List[AnalysisHistoryEntry]:
        """
        获取所有历史记录

        Returns:
            历史记录列表（按时间倒序）
        """
        data = self._load_data()
        return [AnalysisHistoryEntry.from_dict(e) for e in data.get("entries", [])]

    def delete_entry(self, entry_id: str) -> bool:
        """
        删除单条历史记录

        Args:
            entry_id: 记录ID

        Returns:
            是否成功删除
        """
        data = self._load_data()
        original_count = len(data["entries"])
        data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]

        if len(data["entries"]) < original_count:
            return self._save_data(data)
        return False

    def clear_all(self) -> bool:
        """
        清空所有历史记录

        Returns:
            是否成功清空
        """
        data = {"entries": []}
        return self._save_data(data)

    def search(self, keyword: str = "", fund_type: Optional[str] = None) -> List[AnalysisHistoryEntry]:
        """
        搜索历史记录

        Args:
            keyword: 搜索关键词（匹配代码或名称）
            fund_type: 基金类型过滤

        Returns:
            匹配的历史记录列表
        """
        entries = self.get_all_entries()

        if keyword:
            keyword_lower = keyword.lower()
            entries = [
                e for e in entries
                if keyword_lower in e.symbol.lower() or keyword_lower in e.name.lower()
            ]

        if fund_type:
            entries = [e for e in entries if e.fund_type == fund_type]

        return entries

    def export_to_csv(self) -> Optional[str]:
        """
        导出历史记录为CSV

        Returns:
            CSV文件路径，失败返回None
        """
        entries = self.get_all_entries()
        if not entries:
            return None

        csv_file = self.cache_dir / f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow([
                    "ID", "基金代码", "基金名称", "类型", "创建时间",
                    "异常事件数", "当前价格", "AI分析摘要"
                ])

                # 写入数据
                for entry in entries:
                    # 使用textwrap智能截断AI摘要，避免在单词中间截断
                    summary = textwrap.shorten(
                        entry.ai_summary,
                        width=100,
                        placeholder="...",
                        break_long_words=True,
                        break_on_hyphens=False
                    )
                    writer.writerow([
                        entry.id,
                        entry.symbol,
                        entry.name,
                        entry.fund_type,
                        entry.created_at,
                        entry.abnormal_events_count,
                        entry.current_price,
                        summary
                    ])

            return str(csv_file)
        except IOError:
            return None
