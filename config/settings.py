from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    """应用配置"""

    # GLM API 配置
    glm_api_key: str = Field(default="", env="GLM_API_KEY")
    glm_api_base: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        env="GLM_API_BASE"
    )
    glm_model: str = "glm-4-plus"

    # 路径配置
    project_root: Path = Field(default=Path(__file__).parent.parent)
    data_path: Path = Field(default=Path("./data"))
    log_path: Path = Field(default=Path("./logs"))

    # 数据库配置
    db_path: Path = Field(default=Path("./data/money_agent.db"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

# 全局配置实例
settings = Settings()