import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'
import fs from 'fs'

// 自定义插件：处理和复制 .training 数据
function copyTrainingDataPlugin() {
    return {
        name: 'copy-training-data',
        buildStart() {
            // 构建开始时预处理数据
            const { execSync } = require('child_process');
            try {
                console.log('🚀 预处理训练数据...');
                execSync('node scripts/process-training-data.js', {
                    stdio: 'inherit',
                    cwd: __dirname
                });
            } catch (error) {
                console.error('❌ 数据预处理失败:', error.message);
            }
        },
        writeBundle() {
            const sourceDir = path.resolve(__dirname, 'public', '.training');
            const targetDir = path.resolve(__dirname, 'dist', '.training');

            if (fs.existsSync(sourceDir)) {
                copyDirectory(sourceDir, targetDir);
                console.log('✅ .training 目录已复制到 dist 目录');
            } else {
                console.log('⚠️  预处理的 .training 目录不存在，跳过复制');
            }
        },
        configureServer(server) {
            // 开发模式下服务预处理的数据
            server.middlewares.use('/.training', (req, res, next) => {
                const publicTrainingPath = path.resolve(__dirname, 'public', '.training');
                const filePath = path.join(publicTrainingPath, req.url.replace('/.training', ''));

                if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
                    const content = fs.readFileSync(filePath);
                    if (filePath.endsWith('.json')) {
                        res.setHeader('Content-Type', 'application/json');
                    }
                    res.end(content);
                } else {
                    next();
                }
            });
        }
    }
}// 递归复制目录的辅助函数
function copyDirectory(src, dest) {
    if (!fs.existsSync(dest)) {
        fs.mkdirSync(dest, { recursive: true });
    }

    const entries = fs.readdirSync(src, { withFileTypes: true });

    for (const entry of entries) {
        const srcPath = path.join(src, entry.name);
        const destPath = path.join(dest, entry.name);

        if (entry.isDirectory()) {
            copyDirectory(srcPath, destPath);
        } else {
            fs.copyFileSync(srcPath, destPath);
        }
    }
}

export default defineConfig({
    plugins: [
        vue(),
        AutoImport({
            resolvers: [ElementPlusResolver()],
            imports: ['vue', 'vue-router', 'pinia'],
            dts: true
        }),
        Components({
            resolvers: [ElementPlusResolver()],
            dts: true
        }),
        copyTrainingDataPlugin()
    ],
    server: {
        port: 3000
    },
    build: {
        outDir: 'dist',
        assetsDir: 'assets'
    }
})