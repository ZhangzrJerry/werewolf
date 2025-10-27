@echo off
echo ========================================
echo 狼人杀游戏回放可视化系统
echo ========================================
echo.

cd /d "%~dp0"

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 找不到Python! 请先安装Python.
    pause
    exit /b 1
)

echo 正在检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo 启动Flask应用...
echo 请在浏览器中访问: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

python app.py

pause
