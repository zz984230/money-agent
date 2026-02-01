"""Tests for screening history management in dashboard"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.etf_lof_gamble import GambleAnalysisResult
from storage.analysis_history import AnalysisHistoryManager


def test_batch_save_screening_results():
    """Test batch save screening results to history"""
    # Create mock results
    mock_result = Mock(spec=GambleAnalysisResult)
    mock_result.symbol = "163415"
    mock_result.name = "白银LOF"
    mock_result.fund_type = "LOF"
    mock_result.abnormal_events_count = 3
    mock_result.ai_summary = "Test AI summary"
    mock_result.current_factors = {"price_trend": 100.5}

    results = [mock_result]

    # Patch the history manager
    with patch('ui.dashboard.get_history_manager') as mock_get_manager:
        mock_manager = Mock(spec=AnalysisHistoryManager)
        mock_manager.add_entry.return_value = True
        mock_get_manager.return_value = mock_manager

        # Import after patching
        from ui.dashboard import batch_save_screening_results

        # Call function
        count = batch_save_screening_results(results)

        # Verify
        assert count == 1
        mock_manager.add_entry.assert_called_once()
        call_args = mock_manager.add_entry.call_args
        entry = call_args[0][0]
        assert entry.symbol == "163415"
        assert entry.name == "白银LOF"


def test_batch_save_with_partial_failure():
    """Test batch save when some entries fail"""
    mock_result1 = Mock(spec=GambleAnalysisResult)
    mock_result1.symbol = "163415"
    mock_result1.name = "白银LOF"
    mock_result1.fund_type = "LOF"
    mock_result1.abnormal_events_count = 3
    mock_result1.ai_summary = "Test AI summary 1"
    mock_result1.current_factors = {"price_trend": 100.5}

    mock_result2 = Mock(spec=GambleAnalysisResult)
    mock_result2.symbol = "161116"
    mock_result2.name = "黄金基金"
    mock_result2.fund_type = "LOF"
    mock_result2.abnormal_events_count = 2
    mock_result2.ai_summary = "Test AI summary 2"
    mock_result2.current_factors = {"price_trend": 200.5}

    results = [mock_result1, mock_result2]

    with patch('ui.dashboard.get_history_manager') as mock_get_manager:
        mock_manager = Mock(spec=AnalysisHistoryManager)
        mock_manager.add_entry.side_effect = [True, False]  # First succeeds, second fails
        mock_get_manager.return_value = mock_manager

        from ui.dashboard import batch_save_screening_results

        count = batch_save_screening_results(results)

        # Only first should succeed
        assert count == 1
