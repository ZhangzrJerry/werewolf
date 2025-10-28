# 狼人杀智能体博弈可视化平台 - Vue 版本

这是对原 Flask 可视化平台的完整 Vue.js 重写版本，忠实地复制了原始功能和API设计。

## 🎯 特性

- **完全匹配原 Flask API**: 所有 API 端点都与原版本保持一致
- **现代化 Vue 3 架构**: 使用 Composition API 和 Pinia 状态管理
- **响应式设计**: 支持各种屏幕尺寸的设备
- **组件化开发**: 可复用的组件系统
- **TypeScript 支持**: 类型安全的开发体验

## 📁 项目结构

```
visualization-vue/
├── src/
│   ├── api/           # API 调用层，忠实复制 Flask 路由
│   │   ├── index.js   # Axios 配置和拦截器
│   │   ├── game.js    # 游戏相关 API (对应 Flask 的游戏路由)
│   │   └── learning.js # 学习链相关 API
│   ├── components/    # 可复用组件
│   │   ├── GameSummaryV2.vue  # 游戏概览组件
│   │   └── ...
│   ├── stores/        # Pinia 状态管理
│   │   ├── game.js    # 游戏状态管理
│   │   └── learning.js # 学习数据状态管理
│   ├── views/         # 页面视图
│   │   ├── Home.vue           # 主页 (对应 Flask 的 index.html)
│   │   ├── GameDetail.vue     # 游戏详情页
│   │   ├── LearningChain.vue  # 学习链页面 (对应 Flask 的 learning_chain.html)
│   │   └── Documentation.vue  # 文档页面
│   ├── router/        # Vue Router 配置
│   ├── App.vue        # 根组件
│   └── main.js        # 应用入口
├── package.json       # 依赖配置
├── vite.config.js     # Vite 构建配置
└── index.html         # HTML 模板
```

## 🔗 API 映射

Vue 版本的 API 调用完全匹配原 Flask 应用的路由：

### 游戏相关 API

- `GET /api/logs` → `gameApi.getGameList()` - 获取游戏日志列表
- `GET /api/load/<filename>` → `gameApi.loadGame(filename)` - 加载特定游戏
- `GET /api/state` → `gameApi.getGameState()` - 获取当前游戏状态
- `GET /api/overview` → `gameApi.getGameOverview()` - 获取游戏概览
- `GET /api/next` → `gameApi.nextEvent()` - 移动到下一事件
- `GET /api/prev` → `gameApi.prevEvent()` - 移动到上一事件
- `GET /api/jump/<event_index>` → `gameApi.jumpToEvent(eventIndex)` - 跳转到特定事件
- `GET /api/reset` → `gameApi.resetGame()` - 重置游戏状态

### 静态站点生成 API

- `GET /api/games` → `gameApi.getAllGames()` - 获取所有游戏列表
- `GET /api/game/<game_id>` → `gameApi.getGameData(gameId)` - 获取特定游戏数据
- `GET /api/reviews` → `gameApi.getReviews()` - 获取所有复盘数据
- `GET /api/assets/<filename>` → `gameApi.getAsset(filename)` - 获取静态资源

### 学习链相关

- `/learning-chain/<role>` → Vue 路由处理 - 角色学习链页面

## 🚀 安装和运行

### 前提条件

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
cd visualization-vue
npm install
```

### 开发环境运行

```bash
npm run dev
```

应用将在 `http://localhost:3000` 启动，并自动代理 API 请求到后端的 `http://localhost:5000`。

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## ⚙️ 配置

### 开发环境配置

在 `vite.config.js` 中配置了开发服务器的代理，将 `/api` 路径的请求转发到 Flask 后端：

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  }
}
```

### API 基础配置

在 `src/api/index.js` 中配置了 Axios 实例：

```javascript
const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});
```

## 🎨 样式系统

- 使用 Element Plus 组件库提供统一的 UI 组件
- 保持与原 Flask 版本相同的视觉风格和布局
- 响应式设计支持移动设备
- CSS 变量和自定义样式覆盖

## 📱 响应式设计

所有组件都经过响应式设计优化：

- 桌面端: 完整功能布局
- 平板端: 适配的卡片布局
- 移动端: 垂直堆叠布局

## 🔄 状态管理

使用 Pinia 进行状态管理，主要包括：

### GameStore (游戏状态)

- `gameList`: 游戏列表
- `currentGameFilename`: 当前游戏文件名
- `gameOverview`: 游戏概览数据 (来自 Flask 的 /api/overview)
- `gameState`: 当前游戏状态
- `loading`: 加载状态
- `error`: 错误信息

### LearningStore (学习数据状态)

- `learningData`: 角色学习数据
- `currentRole`: 当前角色
- `loading`: 加载状态
- `error`: 错误信息

## 🛠 开发指南

### 添加新的 API 端点

1. 在对应的 API 文件中添加新方法 (如 `src/api/game.js`)
2. 在相应的 Store 中添加调用逻辑
3. 在组件中使用 Store 方法

### 添加新页面

1. 在 `src/views/` 中创建新的 Vue 组件
2. 在 `src/router/index.js` 中添加路由配置
3. 根据需要在导航中添加链接

### 组件开发规范

- 使用 Composition API 语法
- 合理使用 Element Plus 组件
- 保持与原 Flask 版本的功能一致性
- 添加适当的错误处理和加载状态

## 🔍 与原版本的对应关系

| Flask 模板                      | Vue 组件                  | 功能                 |
| ------------------------------- | ------------------------- | -------------------- |
| `templates/index.html`          | `views/Home.vue`          | 主页，游戏列表和选择 |
| `templates/learning_chain.html` | `views/LearningChain.vue` | 角色学习链展示       |
| N/A                             | `views/GameDetail.vue`    | 游戏详细分析页面     |
| N/A                             | `views/Documentation.vue` | 项目文档页面         |

| Flask 路由               | Vue API 方法                | 功能             |
| ------------------------ | --------------------------- | ---------------- |
| `/api/logs`              | `gameApi.getGameList()`     | 获取游戏日志列表 |
| `/api/load/<filename>`   | `gameApi.loadGame()`        | 加载游戏         |
| `/api/overview`          | `gameApi.getGameOverview()` | 获取游戏概览     |
| `/learning-chain/<role>` | Vue 路由 + API              | 角色学习链       |

## 🐛 故障排除

### API 代理问题

如果 API 请求失败，检查：

1. Flask 后端是否在 `http://localhost:5000` 运行
2. Vite 代理配置是否正确
3. 网络连接是否正常

### 样式问题

如果样式显示异常：

1. 确认 Element Plus 样式已正确导入
2. 检查 CSS 作用域和优先级
3. 验证响应式断点配置

### 路由问题

如果页面路由不工作：

1. 检查路由配置是否正确
2. 确认组件导入路径
3. 验证路由参数传递

## 📄 许可证

本项目继承原项目的许可证。

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests 来改进这个项目！
