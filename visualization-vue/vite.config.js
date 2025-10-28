import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'
import fs from 'fs'

// 自定义插件：复制 .training 目录
function copyTrainingDataPlugin() {
    return {
        name: 'copy-training-data',
        writeBundle() {
            const sourceDir = path.resolve(__dirname, '..', '.training');
            const targetDir = path.resolve(__dirname, 'dist', '.training');

            if (fs.existsSync(sourceDir)) {
                copyDirectory(sourceDir, targetDir);
                console.log('✅ .training 目录已复制到 dist 目录');
            } else {
                console.log('⚠️  .training 目录不存在，跳过复制');
            }
        }
    }
}

// 递归复制目录的辅助函数
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