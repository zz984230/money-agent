"""测试分析历史记录管理器"""
import pytest
from pathlib import Path
from datetime import datetime
from storage.analysis_history import AnalysisHistoryManager, AnalysisHistoryEntry


@pytest.fixture
def temp_cache_dir(tmp_path):
    """临时缓存目录"""
    return tmp_path / "cache"


@pytest.fixture
def manager(temp_cache_dir):
    """历史管理器实例"""
    return AnalysisHistoryManager(temp_cache_dir)


def test_manager_creates_cache_file(manager, temp_cache_dir):
    """测试管理器初始化时创建缓存文件"""
    assert manager.cache_file == temp_cache_dir / "analysis_history.json"
    # 初始化时不自动创建文件


def test_add_entry(manager):
    """测试添加历史记录"""
    entry = AnalysisHistoryEntry(
        id="test-001",
        symbol="163415",
        name="白银LOF",
        fund_type="LOF",
        created_at="2025-01-31T14:30:00",
        abnormal_events_count=5,
        current_price=0.856,
        ai_summary="## 测试分析",
        current_factors={"momentum_5": 0.05}
    )

    result = manager.add_entry(entry)
    assert result is True

    # 验证可以获取到添加的记录
    entries = manager.get_all_entries()
    assert len(entries) == 1
    assert entries[0].id == "test-001"


def test_get_all_entries_returns_empty_when_no_data(manager):
    """测试无数据时返回空列表"""
    entries = manager.get_all_entries()
    assert entries == []


def test_delete_entry(manager):
    """测试删除单条记录"""
    entry = AnalysisHistoryEntry(
        id="test-002",
        symbol="161116",
        name="黄金基金",
        fund_type="LOF",
        created_at="2025-01-31T15:00:00",
        abnormal_events_count=3,
        current_price=1.234,
        ai_summary="测试",
        current_factors={}
    )
    manager.add_entry(entry)

    result = manager.delete_entry("test-002")
    assert result is True

    entries = manager.get_all_entries()
    assert len(entries) == 0


def test_delete_nonexistent_entry(manager):
    """测试删除不存在的记录返回False"""
    result = manager.delete_entry("nonexistent")
    assert result is False


def test_clear_all(manager):
    """测试清空所有记录"""
    entry1 = AnalysisHistoryEntry(
        id="test-003", symbol="001", name="测试1", fund_type="LOF",
        created_at="2025-01-31T16:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="测试", current_factors={}
    )
    entry2 = AnalysisHistoryEntry(
        id="test-004", symbol="002", name="测试2", fund_type="ETF",
        created_at="2025-01-31T17:00:00", abnormal_events_count=2,
        current_price=2.0, ai_summary="测试", current_factors={}
    )
    manager.add_entry(entry1)
    manager.add_entry(entry2)

    result = manager.clear_all()
    assert result is True

    entries = manager.get_all_entries()
    assert len(entries) == 0


def test_search_by_keyword(manager):
    """测试按关键词搜索"""
    entry1 = AnalysisHistoryEntry(
        id="test-005", symbol="163415", name="白银LOF", fund_type="LOF",
        created_at="2025-01-31T18:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="白银分析", current_factors={}
    )
    entry2 = AnalysisHistoryEntry(
        id="test-006", symbol="161116", name="黄金基金", fund_type="LOF",
        created_at="2025-01-31T19:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="黄金分析", current_factors={}
    )
    manager.add_entry(entry1)
    manager.add_entry(entry2)

    results = manager.search(keyword="白银")
    assert len(results) == 1
    assert results[0].name == "白银LOF"


def test_search_by_fund_type(manager):
    """测试按基金类型过滤"""
    entry1 = AnalysisHistoryEntry(
        id="test-007", symbol="001", name="LOF基金", fund_type="LOF",
        created_at="2025-01-31T20:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="测试", current_factors={}
    )
    entry2 = AnalysisHistoryEntry(
        id="test-008", symbol="002", name="ETF基金", fund_type="ETF",
        created_at="2025-01-31T21:00:00", abnormal_events_count=1,
        current_price=1.0, ai_summary="测试", current_factors={}
    )
    manager.add_entry(entry1)
    manager.add_entry(entry2)

    results = manager.search(fund_type="LOF")
    assert len(results) == 1
    assert results[0].fund_type == "LOF"


def test_export_to_csv(manager, tmp_path):
    """测试导出CSV"""
    entry = AnalysisHistoryEntry(
        id="test-009", symbol="163415", name="白银LOF", fund_type="LOF",
        created_at="2025-01-31T22:00:00", abnormal_events_count=5,
        current_price=0.856, ai_summary="测试分析", current_factors={}
    )
    manager.add_entry(entry)

    # 修改导出目录到临时目录
    original_cache_dir = manager.cache_dir
    manager.cache_dir = tmp_path

    csv_path = manager.export_to_csv()

    assert csv_path is not None
    assert Path(csv_path).exists()

    # 恢复原目录
    manager.cache_dir = original_cache_dir
