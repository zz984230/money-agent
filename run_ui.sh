#!/bin/bash

# Streamlit Dashboard Startup Script
# Streamlit 仪表板启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  A 股 AI 投研竞技场 - Streamlit UI${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo -e "${YELLOW}请复制 .env.example 到 .env 并配置 GLM_API_KEY${NC}"
    echo ""

    if [ -f .env.example ]; then
        echo -e "${YELLOW}是否要创建 .env 文件? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            cp .env.example .env
            echo -e "${GREEN}已创建 .env 文件${NC}"
            echo -e "${YELLOW}请编辑 .env 文件并设置您的 GLM_API_KEY${NC}"
            exit 0
        fi
    fi

    echo -e "${RED}错误: 缺少 .env 文件${NC}"
    exit 1
fi

# 检查 GLM_API_KEY
if ! grep -q "GLM_API_KEY=" .env || grep -q "GLM_API_KEY=$" .env; then
    echo -e "${YELLOW}警告: GLM_API_KEY 未设置${NC}"
    echo -e "${YELLOW}请在 .env 文件中设置您的 GLM API Key${NC}"
    echo ""
    echo -e "${YELLOW}是否要继续启动? (y/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        exit 1
    fi
fi

# 显示配置信息
echo -e "${GREEN}配置信息:${NC}"
echo "  - 工作目录: $SCRIPT_DIR"
echo "  - 配置文件: $SCRIPT_DIR/.env"
echo ""

# 启动 Streamlit
echo -e "${GREEN}正在启动 Streamlit 仪表板...${NC}"
echo ""

# 使用 uv run 启动 streamlit
uv run streamlit run ui/dashboard.py \
    --server.port=8501 \
    --server.address=localhost \
    --theme.base=light \
    --theme.primaryColor="#1f77b4" \
    --theme.backgroundColor="#ffffff" \
    --theme.secondaryBackgroundColor="#f0f2f6" \
    --theme.textColor="#262730" \
    --browser.gatherUsageStats=false
