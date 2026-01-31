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


def test_validate_config_name_valid(manager, sample_funds):
    """Test validation accepts valid config names"""
    # Valid names
    valid_names = [
        "白银精选",
        "Silver Fund",
        "silver-fund",
        "silver_fund",
        "白银基金123"
    ]

    for name in valid_names:
        is_valid, error = manager._validate_config_name(name)
        assert is_valid is True, f"Name '{name}' should be valid: {error}"
        assert error is None


def test_validate_config_name_invalid(manager):
    """Test validation rejects invalid config names"""
    # Invalid: empty
    is_valid, error = manager._validate_config_name("")
    assert is_valid is False
    assert "不能为空" in error

    # Invalid: whitespace only
    is_valid, error = manager._validate_config_name("   ")
    assert is_valid is False
    assert "不能为空" in error

    # Invalid: special characters
    invalid_names = [
        "白银/精选",  # slash
        "白银:精选",  # colon
        "白银*精选",  # asterisk
        "白银?精选",  # question mark
        "白银<精选",  # angle bracket
        "白银>精选",  # angle bracket
        "白银|精选",  # pipe
        '白银"精选',  # quote
    ]

    for name in invalid_names:
        is_valid, error = manager._validate_config_name(name)
        assert is_valid is False, f"Name '{name}' should be invalid"
        assert "只能包含" in error

    # Invalid: reserved name
    is_valid, error = manager._validate_config_name("-- 新建配置 --")
    assert is_valid is False
    assert "保留名称" in error


def test_validate_config_name_too_long(manager):
    """Test validation rejects names exceeding max length"""
    # Create a name that exceeds CONFIG_NAME_MAX_LENGTH (50)
    long_name = "a" * 51
    is_valid, error = manager._validate_config_name(long_name)
    assert is_valid is False
    assert "不能超过" in error
    assert "50" in error


def test_save_config_with_invalid_name(manager, sample_funds):
    """Test saving config with invalid name returns False"""
    # Try to save with invalid name
    result = manager.save_config("白银/精选", sample_funds)
    assert result is False

    # Verify no config was created
    configs = manager.list_configs()
    assert len(configs) == 0


# ==================== Integration Tests ====================
# These tests require real file I/O and test broader workflows

@pytest.mark.integration
def test_save_and_load_config_workflow(manager, temp_cache_dir):
    """Test full workflow: save, list, load, append, delete"""
    # Step 1: Save a config with funds
    initial_funds = [
        {"code": "161226", "name": "国投白银LOF", "type": "LOF"},
        {"code": "163415", "name": "白银LOF", "type": "LOF"}
    ]
    save_result = manager.save_config("白银精选", initial_funds)
    assert save_result is True, "Failed to save initial config"

    # Step 2: Verify it appears in list_configs()
    configs = manager.list_configs()
    assert len(configs) == 1, "Config count should be 1"
    config_names = [c["name"] for c in configs]
    assert "白银精选" in config_names, "Config name should be in list"

    # Step 3: Load the config and verify funds
    loaded_funds = manager.load_config("白银精选")
    assert loaded_funds is not None, "Failed to load config"
    assert len(loaded_funds) == 2, "Should have 2 initial funds"
    assert loaded_funds[0]["code"] == "161226", "First fund code mismatch"
    assert loaded_funds[1]["code"] == "163415", "Second fund code mismatch"

    # Step 4: Append new funds (with dedup)
    additional_funds = [
        {"code": "161116", "name": "黄金基金", "type": "LOF"},
        {"code": "161226", "name": "白银LOF Duplicate", "type": "LOF"}  # Duplicate
    ]
    append_result = manager.append_to_config("白银精选", additional_funds)
    assert append_result is True, "Failed to append funds"

    # Step 5: Verify updated count (should be 3, not 4, due to dedup)
    updated_funds = manager.load_config("白银精选")
    assert len(updated_funds) == 3, "Should have 3 funds after append (dedup)"
    fund_codes = [f["code"] for f in updated_funds]
    assert "161116" in fund_codes, "New fund should be added"
    assert "161226" in fund_codes, "Original fund should be preserved"
    # Verify the original fund was kept (not replaced by duplicate)
    original_fund = next(f for f in updated_funds if f["code"] == "161226")
    assert original_fund["name"] == "国投白银LOF", "Original fund name should be kept"

    # Step 6: Delete the config
    delete_result = manager.delete_config("白银精选")
    assert delete_result is True, "Failed to delete config"

    # Step 7: Verify it's gone
    final_configs = manager.list_configs()
    assert len(final_configs) == 0, "Config should be deleted"
    deleted_funds = manager.load_config("白银精选")
    assert deleted_funds is None, "Deleted config should return None"


@pytest.mark.integration
def test_append_funds_and_analyze():
    """Test UI integration: selected_funds passed correctly to analysis"""
    # This test verifies the integration between fund selection config
    # and the screen_and_analyze_with_mode function
    import sys
    from pathlib import Path
    from unittest.mock import Mock, patch, call

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    from ui.dashboard import screen_and_analyze_with_mode, _screen_and_analyze_with_targets

    # Mock the analyzer
    mock_analyzer = Mock()
    mock_analyzer.detect_sudden_moves.return_value = []
    mock_analyzer.calculate_all_factors.return_value = {}
    mock_analyzer.build_prediction_model.return_value = []

    # Mock fetcher to avoid real API calls
    mock_fetcher = Mock()

    # Sample selected funds from config
    selected_funds = [
        {"code": "161226", "name": "国投白银LOF", "type": "LOF"},
        {"code": "163415", "name": "白银LOF", "type": "LOF"}
    ]

    criteria = {
        'window': 3,
        'threshold': 0.15,
        'fund_types': ['commodity']
    }
    top_n = 10

    # Test with selected_funds mode
    with patch('ui.dashboard.cached_get_fund_list') as mock_cached_list:
        # Mock screen_and_analyze_with_mode
        with patch('ui.dashboard._screen_and_analyze_with_targets') as mock_screen_targets:
            # Call with selected_funds (should skip cache/rescan logic)
            result = screen_and_analyze_with_mode(
                mock_analyzer, criteria, top_n, 'use_cache',
                selected_funds=selected_funds,
                progress_callback=None
            )

            # Verify _screen_and_analyze_with_targets was called
            assert mock_screen_targets.called, "_screen_and_analyze_with_targets should be called"

            # Verify selected_funds was passed correctly
            call_args = mock_screen_targets.call_args
            args, kwargs = call_args

            # First positional arg should be analyzer
            assert args[0] == mock_analyzer, "Analyzer should be passed"

            # Second positional arg should be target_list (our selected_funds)
            target_list = args[1]
            assert len(target_list) == 2, "Target list should have 2 funds"
            assert target_list[0]["code"] == "161226", "First fund should match"
            assert target_list[1]["code"] == "163415", "Second fund should match"

            # Verify cached_get_fund_list was NOT called (since we provided selected_funds)
            assert not mock_cached_list.called, "cached_get_fund_list should not be called when selected_funds provided"

    # Test without selected_funds (should use cache)
    with patch('ui.dashboard.cached_get_fund_list') as mock_cached_list:
        mock_cached_list.return_value = selected_funds  # Return same funds

        with patch('ui.dashboard._screen_and_analyze_with_targets') as mock_screen_targets:
            # Call without selected_funds (should use cache)
            result = screen_and_analyze_with_mode(
                mock_analyzer, criteria, top_n, 'use_cache',
                selected_funds=None,
                progress_callback=None
            )

            # Verify cached_get_fund_list WAS called
            assert mock_cached_list.called, "cached_get_fund_list should be called when selected_funds is None"

            # Verify it was called with correct fund_types
            call_args = mock_cached_list.call_args
            args, kwargs = call_args
            assert args[1] == 'commodity', "Should fetch commodity funds"
