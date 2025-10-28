const fs = require('fs')
const path = require('path')

function copyRecursiveSync(src, dest) {
    if (!fs.existsSync(src)) return false
    const stat = fs.statSync(src)
    if (stat.isDirectory()) {
        if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true })
        const entries = fs.readdirSync(src)
        for (const entry of entries) {
            const srcPath = path.join(src, entry)
            const destPath = path.join(dest, entry)
            copyRecursiveSync(srcPath, destPath)
        }
    } else if (stat.isFile()) {
        fs.copyFileSync(src, dest)
    }
    return true
}

function main() {
    const scriptDir = __dirname
    // repo root is two levels up from visualization-vue/scripts
    const repoRoot = path.resolve(scriptDir, '..', '..')
    const vizRoot = path.resolve(scriptDir, '..')

    const sources = [
        path.join(repoRoot, '.training'), // primary source: project root .training
        path.join(vizRoot, 'assets', '.training') // fallback: visualization assets
    ]

    const target = path.join(vizRoot, 'public', '.training')

    let copied = false
    for (const src of sources) {
        if (fs.existsSync(src)) {
            console.log(`Copying .training from ${src} -> ${target}`)
            copyRecursiveSync(src, target)
            copied = true
            break
        }
    }

    if (!copied) {
        console.warn('⚠️  No .training source found (searched repo root and visualization assets). Skipping.')
        process.exitCode = 0
        return
    }

    console.log('✅ .training copied to public/.training')
}

main()
