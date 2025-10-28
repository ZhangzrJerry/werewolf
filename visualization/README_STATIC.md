# 狼人杀智能体博弈 - 静态站点生成

这个目录包含了将 Flask 应用转换为静态网站的工具和配置。

## 📁 文件结构

```
visualization/
├── generate_static_data.py    # 静态数据生成脚本
├── serve_local.py             # 本地开发服务器
├── parser.py                  # 游戏日志解析器
├── state_manager.py           # 游戏状态管理器
├── templates/                 # 原始Flask模板
├── static/                    # 静态资源文件
└── build/                     # 生成的静态网站文件
    ├── index.html            # 主页
    ├── learning-chain-*.html # 学习链页面
    ├── data/                 # 预生成的JSON数据
    │   ├── games.json       # 游戏列表
    │   ├── games/           # 各游戏详细数据
    │   └── learning/        # 学习链数据
    └── assets/              # 静态资源
```

## 🚀 快速开始

### 1. 生成静态文件

```bash
# 基本生成（无baseUrl）
python generate_static_data.py --clean

# 为GitHub Pages生成（带baseUrl）
python generate_static_data.py --clean --base-url="/werewolf"

# 自定义输出目录
python generate_static_data.py --output="dist" --base-url="/my-project"
```

### 2. 本地测试

```bash
# 启动本地服务器
python serve_local.py

# 自定义端口
python serve_local.py --port=3000

# 重新构建并启动服务器
python serve_local.py --rebuild
```

访问 `http://localhost:8000` 查看网站。

## 🔧 生成脚本参数

### `generate_static_data.py`

- `--output, -o`: 输出目录（默认：build）
- `--base-url, -b`: 部署的基础 URL（如：/werewolf）
- `--clean`: 清理输出目录后重新生成

### `serve_local.py`

- `--port, -p`: 服务器端口（默认：8000）
- `--build-dir, -d`: 构建目录（默认：build）
- `--rebuild, -r`: 启动前重新构建

## 🌐 部署到 GitHub Pages

### 自动部署（推荐）

1. 确保仓库设置中启用了 GitHub Pages
2. 推送代码到`main`或`master`分支
3. GitHub Actions 会自动构建和部署

工作流文件位于：`.github/workflows/deploy.yml`

### 手动部署

```bash
# 1. 生成静态文件
python generate_static_data.py --clean --base-url="/werewolf"

# 2. 将build目录内容推送到gh-pages分支
# 或直接使用GitHub Pages的source设置
```

## 📊 数据来源

静态生成器会从以下位置读取数据：

1. **游戏日志**: `.training/game_logs/` 或 `static/game_logs/`
2. **学习数据**: `.training/reviews/` 和 `.training/strategies/`
3. **静态资源**: `static/` 目录

## 🔄 与原 Flask 应用的差异

### 移除的功能

- Flask 服务器依赖
- 动态 API 端点
- 实时数据加载

### 保留的功能

- ✅ 游戏可视化界面
- ✅ 学习链展示
- ✅ 项目文档
- ✅ 所有交互功能

### 技术变更

- API 调用 → 静态 JSON 文件加载
- 服务器端模板渲染 → 客户端数据渲染
- Flask 路由 → 静态 HTML 页面

## 🛠️ 自定义和扩展

### 添加新的游戏数据

1. 将新的游戏日志文件放入游戏日志目录
2. 重新运行 `generate_static_data.py`

### 修改样式和脚本

1. 编辑 `static/` 目录中的文件
2. 重新运行生成脚本

### 自定义 baseUrl

根据你的部署环境修改 `--base-url` 参数：

- GitHub Pages: `/repository-name`
- 自定义域名: 留空或使用子路径
- 子目录部署: `/path/to/subdir`

## 📝 注意事项

1. **游戏日志要求**: 只处理已完成的游戏（包含"GAME OVER"标记）
2. **文件大小**: 大量游戏数据可能影响首次加载速度
3. **浏览器兼容性**: 需要支持 ES6+的现代浏览器
4. **CORS**: 本地文件访问可能需要 HTTP 服务器（不能直接打开 HTML 文件）

## 🔍 故障排除

### 常见问题

1. **找不到游戏日志**

   - 检查 `.training/game_logs/` 目录是否存在
   - 确认日志文件是完整的游戏记录

2. **静态资源 404**

   - 检查 baseUrl 设置是否正确
   - 确认文件路径大小写匹配

3. **JavaScript 错误**
   - 检查浏览器控制台错误信息
   - 确认 JSON 数据文件格式正确

### 调试模式

启动本地服务器并在浏览器开发者工具中检查：

- Network 面板：查看资源加载情况
- Console 面板：查看 JavaScript 错误
- Sources 面板：调试脚本执行
