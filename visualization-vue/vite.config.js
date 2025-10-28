import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'

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
        })
    ],
    server: {
        port: 3000,
        proxy: {
            // Keep the /api prefix when proxying to the Flask backend so routes like
            // /api/logs map correctly to Flask's @app.route('/api/logs').
            '/api': {
                target: 'http://localhost:5000',
                changeOrigin: true,
                // don't rewrite the path — preserve /api
            },
            // Note: serving raw filesystem paths via the dev proxy is not supported.
            // If you need to expose `.training` during development, prefer adding a
            // small Flask route that serves files under /training/* and proxy to
            // http://localhost:5000/training when that's implemented.
        }
    },
    build: {
        outDir: 'dist',
        assetsDir: 'assets'
    }
})