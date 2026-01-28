@echo off
REM Streamlit Dashboard Startup Script for Windows
REM Streamlit 仪表板启动脚本 (Windows)

echo ======================================
echo   A 股 AI 投研竞技场 - Streamlit UI
echo ======================================
echo.

REM Check .env file
if not exist .env (
    echo [警告] 未找到 .env 文件
    echo [警告] 请复制 .env.example 到 .env 并配置 GLM_API_KEY
    echo.

    if exist .env.example (
        set /p response="是否要创建 .env 文件? (y/n): "
        if /i "%response%"=="y" (
            copy .env.example .env
            echo [成功] 已创建 .env 文件
            echo [提示] 请编辑 .env 文件并设置您的 GLM_API_KEY
            pause
            exit /b 0
        )
    )

    echo [错误] 缺少 .env 文件
    pause
    exit /b 1
)

REM Display configuration
echo [配置] 工作目录: %CD%
echo [配置] 配置文件: %CD%\.env
echo.

REM Start Streamlit
echo [启动] 正在启动 Streamlit 仪表板...
echo.

uv run streamlit run ui/dashboard.py ^
    --server.port=8501 ^
    --server.address=localhost ^
    --theme.base=light ^
    --theme.primaryColor="#1f77b4" ^
    --theme.backgroundColor="#ffffff" ^
    --theme.secondaryBackgroundColor="#f0f2f6" ^
    --theme.textColor="#262730" ^
    --browser.gatherUsageStats=false

pause
