"""基金选择配置管理器 - 用于保存和加载用户自定义的基金组合配置"""
import json
import logging
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# 配置名称验证：只允许中文、字母、数字、下划线、连字符、空格
CONFIG_NAME_PATTERN = re.compile(r'^[\u4e00-\u9fff\w\- ]+$')
CONFIG_NAME_MAX_LENGTH = 50


@dataclass
class FundSelectionConfig:
    """基金选择配置"""
    name: str                  # 配置名称
    created_at: str            # 创建时间 (ISO 8601格式)
    updated_at: str            # 更新时间 (ISO 8601格式)
    funds: List[Dict[str, Any]]  # 基金列表，每项包含 code, name, type

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FundSelectionConfig':
        """从字典创建实例"""
        return cls(**data)


class FundSelectionManager:
    """基金选择配置管理器"""

    def __init__(self, cache_dir: Path):
        """
        初始化管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir
        self.config_dir = cache_dir / "fund_selections"
        self.config_index_file = self.config_dir / "configs.json"
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> Dict[str, Any]:
        """
        加载配置索引

        Returns:
            索引数据，格式为 {"configs": [...]}，出错时返回 {"configs": []}
        """
        if not self.config_index_file.exists():
            return {"configs": []}

        try:
            with open(self.config_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config index from {self.config_index_file}: {e}")
            return {"configs": []}

    def _save_index(self, data: Dict[str, Any]) -> bool:
        """
        保存配置索引

        Args:
            data: 索引数据

        Returns:
            是否保存成功
        """
        try:
            with open(self.config_index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save config index to {self.config_index_file}: {e}")
            return False

    def list_configs(self) -> List[Dict[str, Any]]:
        """
        列出所有配置的元数据

        Returns:
            配置元数据列表，每项包含 name, created_at, updated_at, fund_count, fund_types
        """
        index_data = self._load_index()
        return index_data.get("configs", [])

    def _validate_config_name(self, name: str) -> tuple[bool, Optional[str]]:
        """
        验证配置名称是否有效

        Args:
            name: 配置名称

        Returns:
            (是否有效, 错误信息)
        """
        if not name or not name.strip():
            return False, "配置名称不能为空"

        if len(name) > CONFIG_NAME_MAX_LENGTH:
            return False, f"配置名称不能超过 {CONFIG_NAME_MAX_LENGTH} 个字符"

        if not CONFIG_NAME_PATTERN.match(name):
            return False, "配置名称只能包含中文、字母、数字、下划线、连字符和空格"

        # 检查保留名称
        if name == "-- 新建配置 --":
            return False, "此名称为保留名称，请使用其他名称"

        return True, None

    def save_config(self, name: str, funds: List[Dict[str, Any]], overwrite: bool = False) -> bool:
        """
        保存配置

        Args:
            name: 配置名称
            funds: 基金列表，每项包含 code, name, type
            overwrite: 是否覆盖已存在的配置

        Returns:
            是否保存成功
        """
        # 验证配置名称
        is_valid, error_msg = self._validate_config_name(name)
        if not is_valid:
            logger.warning(f"Invalid config name '{name}': {error_msg}")
            return False

        # 检查配置是否已存在
        index_data = self._load_index()
        existing_config = next(
            (c for c in index_data["configs"] if c["name"] == name),
            None
        )

        if existing_config and not overwrite:
            return False

        # 获取当前时间
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # 提取基金类型（去重）
        fund_types = sorted(set(fund.get("type", "Unknown") for fund in funds))

        if existing_config:
            # 更新现有配置
            existing_config["updated_at"] = now
            existing_config["fund_count"] = len(funds)
            existing_config["fund_types"] = fund_types
        else:
            # 创建新配置元数据
            config_meta = {
                "name": name,
                "created_at": now,
                "updated_at": now,
                "fund_count": len(funds),
                "fund_types": fund_types
            }
            index_data["configs"].append(config_meta)

        # 保存索引
        if not self._save_index(index_data):
            return False

        # 保存配置文件
        config_file = self.config_dir / f"{name}.json"
        try:
            config = FundSelectionConfig(
                name=name,
                created_at=existing_config["created_at"] if existing_config else now,
                updated_at=now,
                funds=funds
            )
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save config to {config_file}: {e}")
            return False

    def load_config(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """
        加载配置

        Args:
            name: 配置名称

        Returns:
            基金列表，配置不存在时返回 None
        """
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = FundSelectionConfig.from_dict(data)
                return config.funds
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            return None

    def delete_config(self, name: str) -> bool:
        """
        删除配置

        Args:
            name: 配置名称

        Returns:
            是否删除成功
        """
        # 删除配置文件
        config_file = self.config_dir / f"{name}.json"
        if not config_file.exists():
            return False

        try:
            config_file.unlink()
        except IOError as e:
            logger.error(f"Failed to delete config file {config_file}: {e}")
            return False

        # 从索引中移除
        index_data = self._load_index()
        original_count = len(index_data["configs"])
        index_data["configs"] = [c for c in index_data["configs"] if c["name"] != name]

        if len(index_data["configs"]) < original_count:
            return self._save_index(index_data)

        return False

    def append_to_config(self, name: str, new_funds: List[Dict[str, Any]]) -> bool:
        """
        向配置追加基金（去重）

        Args:
            name: 配置名称
            new_funds: 要追加的基金列表

        Returns:
            是否追加成功
        """
        # 加载现有配置
        existing_funds = self.load_config(name)
        if existing_funds is None:
            return False

        # 按代码去重
        existing_codes = {fund["code"] for fund in existing_funds}
        funds_to_add = [fund for fund in new_funds if fund["code"] not in existing_codes]

        if not funds_to_add:
            # 没有新基金需要添加，但不算失败
            return True

        # 合并基金列表
        updated_funds = existing_funds + funds_to_add

        # 保存更新后的配置
        return self.save_config(name, updated_funds, overwrite=True)
