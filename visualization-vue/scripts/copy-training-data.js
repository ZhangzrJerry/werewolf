const fs = require('fs');
const path = require('path');

// 源目录：项目根目录下的 .training 文件夹
const sourceDir = path.join(__dirname, '..', '..', '.training');
// 目标目录：dist 文件夹下的 .training
const targetDir = path.join(__dirname, '..', 'dist', '.training');

/**
 * 递归复制目录
 * @param {string} src 源目录
 * @param {string} dest 目标目录
 */
function copyDirectory(src, dest) {
    try {
        // 检查源目录是否存在
        if (!fs.existsSync(src)) {
            console.log(`警告: 源目录不存在: ${src}`);
            return;
        }

        // 创建目标目录
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
        }

        // 读取源目录内容
        const entries = fs.readdirSync(src, { withFileTypes: true });

        for (const entry of entries) {
            const srcPath = path.join(src, entry.name);
            const destPath = path.join(dest, entry.name);

            if (entry.isDirectory()) {
                // 递归复制子目录
                copyDirectory(srcPath, destPath);
            } else {
                // 复制文件
                fs.copyFileSync(srcPath, destPath);
            }
        }

        console.log(`✅ 成功复制 .training 目录: ${src} -> ${dest}`);
    } catch (error) {
        console.error(`❌ 复制 .training 目录时出错:`, error);
        process.exit(1);
    }
}

// 执行复制操作
copyDirectory(sourceDir, targetDir);