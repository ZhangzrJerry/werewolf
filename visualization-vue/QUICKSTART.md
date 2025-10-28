# 快速启动指南

## 第一次设置

1. **安装依赖**

   ```bash
   cd visualization-vue
   npm install
   ```

2. **确保 Flask 后端运行**

   ```bash
   # 在另一个终端中，进入原项目的 visualization 目录
   cd ../visualization
   python app.py
   ```

   Flask 应用应该在 `http://localhost:5000` 运行

3. **启动 Vue 开发服务器**
   ```bash
   npm run dev
   ```
   Vue 应用将在 `http://localhost:3000` 启动

## 开发流程

### 启动开发环境

```bash
# 启动 Flask 后端 (终端 1)
cd visualization
python app.py

# 启动 Vue 前端 (终端 2)
cd visualization-vue
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 部署静态文件

构建完成后，`dist` 目录包含所有静态文件，可以部署到任何静态文件服务器。

## 重要提示

1. **API 代理**: Vue 开发服务器会自动将 `/api/*` 请求代理到 Flask 后端
2. **端口配置**:
   - Flask: `http://localhost:5000`
   - Vue Dev: `http://localhost:3000`
3. **数据来源**: Vue 应用从 Flask 后端获取所有数据，保持功能完全一致

## 故障排除

如果遇到问题：

1. **检查 Flask 后端是否运行**

   ```bash
   curl http://localhost:5000/api/logs
   ```

2. **检查 Vue 应用是否正常启动**
   打开 `http://localhost:3000` 查看是否显示主页

3. **检查 API 代理**
   在浏览器开发者工具的 Network 标签中查看 API 请求是否正常

4. **清除缓存**
   ```bash
   npm run build --force
   rm -rf node_modules package-lock.json
   npm install
   ```
