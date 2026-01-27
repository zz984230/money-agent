import pytest
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

def test_settings_load():
    """测试配置加载"""
    assert settings.glm_api_base == "https://open.bigmodel.cn/api/paas/v4"
    assert settings.glm_model == "glm-4-plus"

def test_paths_exist():
    """测试路径创建"""
    assert settings.data_path.exists()
    assert settings.log_path.exists()