"""
测试UI进度条功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Callable, Optional


class TestDashboardProgress:
    """测试仪表板进度条集成"""

    def test_screen_and_analyze_with_mode_with_progress_callback(self):
        """测试带进度回调的筛选模式"""
        # 导入必要模块
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from ui.dashboard import screen_and_analyze_with_mode, _screen_and_analyze_with_targets

        # 创建mock analyzer
        mock_analyzer = Mock()
        mock_fetcher = Mock()
        mock_analyzer.fetcher = mock_fetcher
        mock_analyzer.detector = Mock()

        # 模拟get_lof_etf_history返回数据
        mock_df = Mock()
        mock_df.__len__ = Mock(return_value=100)
        mock_df.close = Mock()
        mock_df.close.pct_change = Mock(return_value=Mock())

        # 模拟detect_sudden_moves返回空结果
        mock_analyzer.detector.detect_sudden_moves = Mock(return_value=([], None))

        mock_fetcher.get_lof_etf_history = Mock(return_value=mock_df)

        # 创建模拟的progress callback
        progress_updates = []
        def mock_callback(progress: float, message: str):
            progress_updates.append((progress, message))

        # 构建criteria
        criteria = {
            'window': 3,
            'threshold': 0.15,
            'fund_types': ['commodity']
        }

        # 调用函数
        try:
            result = _screen_and_analyze_with_targets(
                mock_analyzer,
                [{'code': '163415', 'name': '白银LOF', 'type': 'commodity'}],
                criteria,
                1,
                mock_callback
            )

            # 验证回调被调用
            assert len(progress_updates) > 0, "Progress callback should be called"

            # 验证进度值的合理性
            for progress, message in progress_updates:
                assert 0.0 <= progress <= 1.0, f"Progress should be between 0 and 1, got {progress}"
                assert isinstance(message, str), "Message should be a string"

            print(f"✓ Progress callback test passed with {len(progress_updates)} updates")
            print(f"  Progress updates: {progress_updates}")

        except Exception as e:
            pytest.fail(f"screen_and_analyze_with_mode raised exception: {e}")

    def test_progress_callback_optional(self):
        """测试进度回调是可选的"""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from ui.dashboard import _screen_and_analyze_with_targets

        # 创建mock analyzer
        mock_analyzer = Mock()
        mock_fetcher = Mock()
        mock_analyzer.fetcher = mock_fetcher
        mock_analyzer.detector = Mock()

        # 模拟数据
        mock_df = Mock()
        mock_df.__len__ = Mock(return_value=100)
        mock_df.close = Mock()
        mock_df.close.pct_change = Mock(return_value=Mock())

        mock_analyzer.detector.detect_sudden_moves = Mock(return_value=([], None))
        mock_fetcher.get_lof_etf_history = Mock(return_value=mock_df)

        # 构建criteria
        criteria = {
            'window': 3,
            'threshold': 0.15,
            'fund_types': ['commodity']
        }

        # 不传入progress_callback，应该正常工作
        try:
            result = _screen_and_analyze_with_targets(
                mock_analyzer,
                [{'code': '163415', 'name': '白银LOF', 'type': 'commodity'}],
                criteria,
                1
            )
            print("✓ Function works without progress callback")
        except Exception as e:
            pytest.fail(f"Function raised exception without progress_callback: {e}")

    def test_progress_callback_signature(self):
        """测试进度回调函数的签名"""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from ui.dashboard import screen_and_analyze_with_mode, _screen_and_analyze_with_targets
        import inspect

        # 检查screen_and_analyze_with_mode的签名
        sig = inspect.signature(screen_and_analyze_with_mode)
        params = sig.parameters

        assert 'progress_callback' in params, "screen_and_analyze_with_mode should have progress_callback parameter"
        # 默认值是None，所以参数是可选的
        assert params['progress_callback'].default is None, "progress_callback should default to None"

        # 检查_screen_and_analyze_with_targets的签名
        sig = inspect.signature(_screen_and_analyze_with_targets)
        params = sig.parameters

        assert 'progress_callback' in params, "_screen_and_analyze_with_targets should have progress_callback parameter"
        assert params['progress_callback'].default is None, "progress_callback should default to None"

        print("✓ Progress callback signature test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
