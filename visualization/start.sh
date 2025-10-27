#!/bin/bash

echo "========================================"
echo "狼人杀游戏回放可视化系统"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 找不到Python! 请先安装Python."
    exit 1
fi

echo "正在检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "启动Flask应用..."
echo "请在浏览器中访问: http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo ""

python3 app.py
