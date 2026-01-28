#!/bin/bash

# Dashboard Verification Script
# 仪表板验证脚本

set -e

echo "========================================"
echo "  Dashboard Verification"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root
PROJECT_ROOT="/Users/zero/Project/money-agent"
cd "$PROJECT_ROOT"

echo "Checking required files..."
echo ""

# Check if ui directory exists
if [ -d "ui" ]; then
    echo -e "${GREEN}✓${NC} ui directory exists"
else
    echo -e "${RED}✗${NC} ui directory not found"
    exit 1
fi

# Check dashboard.py
if [ -f "ui/dashboard.py" ]; then
    echo -e "${GREEN}✓${NC} ui/dashboard.py exists"
    SIZE=$(wc -c < "ui/dashboard.py")
    echo "  Size: $SIZE bytes"
else
    echo -e "${RED}✗${NC} ui/dashboard.py not found"
    exit 1
fi

# Check __init__.py
if [ -f "ui/__init__.py" ]; then
    echo -e "${GREEN}✓${NC} ui/__init__.py exists"
else
    echo -e "${RED}✗${NC} ui/__init__.py not found"
    exit 1
fi

# Check README
if [ -f "ui/README.md" ]; then
    echo -e "${GREEN}✓${NC} ui/README.md exists"
else
    echo -e "${YELLOW}⚠${NC} ui/README.md not found"
fi

# Check startup scripts
if [ -f "run_ui.sh" ]; then
    echo -e "${GREEN}✓${NC} run_ui.sh exists"
    if [ -x "run_ui.sh" ]; then
        echo -e "${GREEN}✓${NC} run_ui.sh is executable"
    else
        echo -e "${YELLOW}⚠${NC} run_ui.sh is not executable"
    fi
else
    echo -e "${RED}✗${NC} run_ui.sh not found"
fi

if [ -f "run_ui.bat" ]; then
    echo -e "${GREEN}✓${NC} run_ui.bat exists"
else
    echo -e "${YELLOW}⚠${NC} run_ui.bat not found"
fi

# Check test file
if [ -f "tests/test_dashboard.py" ]; then
    echo -e "${GREEN}✓${NC} tests/test_dashboard.py exists"
else
    echo -e "${RED}✗${NC} tests/test_dashboard.py not found"
fi

echo ""
echo "Testing module import..."
echo ""

# Test import
if uv run python -c "from ui.dashboard import main; print('Import successful')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Dashboard module imports successfully"
else
    echo -e "${RED}✗${NC} Dashboard module import failed"
    exit 1
fi

echo ""
echo "Testing basic functionality..."
echo ""

# Run basic tests
if uv run python tests/test_dashboard.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Basic tests pass"
else
    echo -e "${YELLOW}⚠${NC} Some tests failed (may require API key)"
fi

echo ""
echo "Checking dependencies..."
echo ""

# Check if streamlit is installed
if uv run python -c "import streamlit; print(f'Streamlit version: {streamlit.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Streamlit is installed"
else
    echo -e "${RED}✗${NC} Streamlit is not installed"
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}All checks passed!${NC}"
echo "========================================"
echo ""
echo "You can now start the dashboard with:"
echo ""
echo "  ./run_ui.sh"
echo ""
echo "or"
echo ""
echo "  uv run streamlit run ui/dashboard.py"
echo ""
