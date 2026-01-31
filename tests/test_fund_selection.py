"""Tests for fund selection configuration manager"""
import pytest
from pathlib import Path
from datetime import datetime
from storage.fund_selection import FundSelectionConfig, FundSelectionManager


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory for testing"""
    return tmp_path / "cache"


@pytest.fixture
def manager(temp_cache_dir):
    """FundSelectionManager instance with temp directory"""
    return FundSelectionManager(temp_cache_dir)


@pytest.fixture
def sample_funds():
    """Sample fund list for testing"""
    return [
        {"code": "161226", "name": "国投白银LOF", "type": "LOF"},
        {"code": "163415", "name": "白银LOF", "type": "LOF"},
        {"code": "161116", "name": "黄金基金", "type": "LOF"}
    ]


def test_save_new_config(manager, temp_cache_dir, sample_funds):
    """Test saving a new config creates config file and index"""
    # Save a new config
    result = manager.save_config("白银精选", sample_funds)

    # Verify save was successful
    assert result is True

    # Verify config directory exists
    config_dir = temp_cache_dir / "fund_selections"
    assert config_dir.exists()

    # Verify index file exists
    index_file = config_dir / "configs.json"
    assert index_file.exists()

    # Verify individual config file exists
    config_file = config_dir / "白银精选.json"
    assert config_file.exists()

    # Verify index contains the config metadata
    index_data = manager._load_index()
    assert len(index_data["configs"]) == 1
    config_meta = index_data["configs"][0]
    assert config_meta["name"] == "白银精选"
    assert "created_at" in config_meta
    assert "updated_at" in config_meta
    assert config_meta["fund_count"] == 3
    assert config_meta["fund_types"] == ["LOF"]

    # Verify config file contains the funds
    loaded_funds = manager.load_config("白银精选")
    assert loaded_funds is not None
    assert len(loaded_funds) == 3
    assert loaded_funds[0]["code"] == "161226"


def test_save_duplicate_config_without_overwrite(manager, sample_funds):
    """Test saving duplicate config without overwrite returns False"""
    # Save initial config
    result1 = manager.save_config("白银精选", sample_funds)
    assert result1 is True

    # Try to save duplicate without overwrite flag
    result2 = manager.save_config("白银精选", sample_funds, overwrite=False)
    assert result2 is False

    # Verify original config is unchanged
    loaded_funds = manager.load_config("白银精选")
    assert len(loaded_funds) == 3


def test_list_configs(manager, sample_funds):
    """Test listing all configs"""
    # Save multiple configs
    manager.save_config("白银精选", sample_funds[:2])
    manager.save_config("黄金基金", [sample_funds[2]])

    # List all configs
    configs = manager.list_configs()
    assert len(configs) == 2

    # Verify metadata structure
    config_names = [c["name"] for c in configs]
    assert "白银精选" in config_names
    assert "黄金基金" in config_names

    # Verify fund counts
    silver_config = next(c for c in configs if c["name"] == "白银精选")
    assert silver_config["fund_count"] == 2


def test_load_config(manager, sample_funds):
    """Test loading a config by name"""
    # Save a config
    manager.save_config("测试配置", sample_funds)

    # Load the config
    loaded_funds = manager.load_config("测试配置")
    assert loaded_funds is not None
    assert len(loaded_funds) == 3
    assert loaded_funds[0]["code"] == "161226"
    assert loaded_funds[0]["name"] == "国投白银LOF"
    assert loaded_funds[0]["type"] == "LOF"


def test_load_nonexistent_config(manager):
    """Test loading a nonexistent config returns None"""
    result = manager.load_config("不存在的配置")
    assert result is None


def test_delete_config(manager, sample_funds):
    """Test deleting a config"""
    # Save a config
    manager.save_config("待删除", sample_funds)

    # Verify it exists
    assert manager.load_config("待删除") is not None

    # Delete it
    result = manager.delete_config("待删除")
    assert result is True

    # Verify it's gone
    assert manager.load_config("待删除") is None

    # Verify it's removed from index
    configs = manager.list_configs()
    assert len(configs) == 0


def test_delete_nonexistent_config(manager):
    """Test deleting a nonexistent config returns False"""
    result = manager.delete_config("不存在的配置")
    assert result is False


def test_append_to_config(manager, sample_funds):
    """Test appending funds to an existing config"""
    # Save initial config with 2 funds
    manager.save_config("白银组合", sample_funds[:2])

    # Append a third fund
    new_funds = [sample_funds[2]]
    result = manager.append_to_config("白银组合", new_funds)
    assert result is True

    # Verify we now have 3 funds
    loaded_funds = manager.load_config("白银组合")
    assert len(loaded_funds) == 3

    # Verify appended fund is present
    assert any(f["code"] == "161116" for f in loaded_funds)


def test_append_to_config_deduplication(manager, sample_funds):
    """Test appending funds deduplicates by code"""
    # Save initial config
    manager.save_config("去重测试", sample_funds[:2])

    # Try to append a duplicate fund (same code)
    duplicate_fund = [{"code": "161226", "name": "白银LOF Duplicate", "type": "LOF"}]
    result = manager.append_to_config("去重测试", duplicate_fund)
    assert result is True

    # Verify still only 2 funds (duplicate was ignored)
    loaded_funds = manager.load_config("去重测试")
    assert len(loaded_funds) == 2

    # Verify original fund is kept (not replaced)
    original_fund = next(f for f in loaded_funds if f["code"] == "161226")
    assert original_fund["name"] == "国投白银LOF"


def test_append_to_nonexistent_config(manager, sample_funds):
    """Test appending to a nonexistent config returns False"""
    result = manager.append_to_config("不存在的配置", sample_funds)
    assert result is False


def test_save_config_with_overwrite(manager, sample_funds):
    """Test saving config with overwrite=True updates existing config"""
    # Save initial config
    manager.save_config("可更新配置", sample_funds[:2])

    # Save with overwrite and different funds
    result = manager.save_config("可更新配置", [sample_funds[2]], overwrite=True)
    assert result is True

    # Verify config was updated
    loaded_funds = manager.load_config("可更新配置")
    assert len(loaded_funds) == 1
    assert loaded_funds[0]["code"] == "161116"

    # Verify updated_at timestamp changed
    configs = manager.list_configs()
    config_meta = next(c for c in configs if c["name"] == "可更新配置")
    assert config_meta["fund_count"] == 1


def test_fund_selection_config_dataclass():
    """Test FundSelectionConfig dataclass methods"""
    funds = [
        {"code": "161226", "name": "白银LOF", "type": "LOF"},
        {"code": "163415", "name": "白银LOF2", "type": "LOF"}
    ]

    config = FundSelectionConfig(
        name="测试",
        created_at="2025-01-31T10:00:00",
        updated_at="2025-01-31T10:00:00",
        funds=funds
    )

    # Test to_dict
    data = config.to_dict()
    assert data["name"] == "测试"
    assert len(data["funds"]) == 2

    # Test from_dict
    recreated = FundSelectionConfig.from_dict(data)
    assert recreated.name == "测试"
    assert len(recreated.funds) == 2
    assert recreated.funds[0]["code"] == "161226"
