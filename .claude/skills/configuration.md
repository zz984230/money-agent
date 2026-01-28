---
name: money-agent-config
description: Configuration module for Money-Agent. Use when managing environment variables via Pydantic Settings, understanding GLM API configuration, or working with project path configuration. Covers Settings class, .env file setup, and runtime configuration access patterns.
---

# Configuration Module

## Overview

The configuration module provides centralized settings management using Pydantic. It reads from `.env` file and environment variables, with type validation and default values.

## Architecture

```
config/
└── settings.py    # Pydantic-based Settings class
```

## Settings Class

Location: `config/settings.py`

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    # GLM API Configuration
    glm_api_key: str = Field(default="", env="GLM_API_KEY")
    glm_api_base: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        env="GLM_API_BASE"
    )
    glm_model: str = "glm-4-plus"

    # Path Configuration
    project_root: Path = Field(default=Path(__file__).parent.parent)
    data_path: Path = Field(default=Path("./data"))
    log_path: Path = Field(default=Path("./logs"))

    # Database Configuration
    db_path: Path = Field(default=Path("./data/money_agent.db"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `GLM_API_KEY` | Zhipu AI API key | `your_api_key_here` |

Get API key from: https://open.bigmodel.cn/

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `GLM_API_BASE` | API endpoint URL | `https://open.bigmodel.cn/api/paas/v4` |
| `GLM_MODEL` | Model name | `glm-4-plus` |
| `DATA_PATH` | Data directory path | `./data` |
| `LOG_PATH` | Log directory path | `./logs` |

## .env File

Create `.env` file in project root:

```bash
# GLM-4.7 API Configuration
GLM_API_KEY=your_glm_api_key_here
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4

# Data Storage Paths
DATA_PATH=./data
LOG_PATH=./logs
```

Copy from template:

```bash
cp .env.example .env
# Then edit .env with your API key
```

## Usage

### Import Settings

```python
from config.settings import settings

# Access configuration
api_key = settings.glm_api_key
model = settings.glm_model
data_dir = settings.data_path
```

### In Agent Classes

```python
from config.settings import settings
from zhipuai import ZhipuAI

class GLMAgent(BaseAgent):
    def __init__(self, model_name: str = None, ...):
        model_name = model_name or settings.glm_model
        api_key = settings.glm_api_key or os.getenv('GLM_API_KEY')
        api_base = settings.glm_api_base or os.getenv('GLM_API_BASE')

        if not api_key:
            raise ValueError("GLM_API_KEY is required")

        self.client = ZhipuAI(api_key=api_key, base_url=api_base)
```

### Path Configuration

```python
# Use configured paths
data_file = settings.data_path / "stocks.csv"
log_file = settings.log_path / "app.log"

# Directories are auto-created on Settings init
settings.data_path.mkdir(parents=True, exist_ok=True)
settings.log_path.mkdir(parents=True, exist_ok=True)
```

## Adding New Settings

To add new configuration options:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # New field
    new_feature_enabled: bool = Field(default=False, env="NEW_FEATURE_ENABLED")
    new_api_key: str = Field(default="", env="NEW_API_KEY")
    new_timeout: int = Field(default=30, env="NEW_TIMEOUT")
```

Then add to `.env`:

```bash
NEW_FEATURE_ENABLED=true
NEW_API_KEY=your_key_here
NEW_TIMEOUT=60
```

## Configuration Precedence

1. Environment variables (highest priority)
2. `.env` file values
3. Default values in Field() (lowest priority)

## Validation

Pydantic automatically validates types:

```python
# This will raise ValidationError if NEW_TIMEOUT is not an int
new_timeout: int = Field(default=30, env="NEW_TIMEOUT")
```

For custom validation:

```python
from pydantic import field_validator

class Settings(BaseSettings):
    timeout: int = Field(default=30, env="TIMEOUT")

    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('timeout must be between 1 and 300')
        return v
```

## Testing with Mock Settings

```python
from unittest.mock import patch
from config.settings import Settings

@patch('config.settings.Settings')
def test_with_mock_settings(mock_settings):
    mock_settings_instance = Mock()
    mock_settings_instance.glm_api_key = "test_key"
    mock_settings_instance.glm_model = "test_model"
    mock_settings.return_value = mock_settings_instance

    # Your test code here
    agent = GLMAgent()
    assert agent.model_name == "test_model"
```

Or use environment variables:

```python
import os
os.environ['GLM_API_KEY'] = 'test_key'
from config.settings import settings
assert settings.glm_api_key == 'test_key'
```

## Security Notes

- **Never commit `.env` file** to version control
- Add `.env` to `.gitignore`
- Use `.env.example` as a template with placeholder values
- Keep API keys secure in production (use secret management)
