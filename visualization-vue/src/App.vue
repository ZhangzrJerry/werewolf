<template>
    <div class="app-shell">
        <header>
            <div class="header-top">
                <h1>🐺 Werewolf Game Replay Viewer</h1>
                <div class="header-links">
                    <a href="/doc.html" class="doc-link" target="_blank">📖 Documentation</a>
                    <a href="https://github.com/ZhangzrJerry/werewolf" class="github-link" target="_blank">🔗 GitHub</a>
                </div>
            </div>
        </header>
        <div class="container">
            <main>
                <GameViewer />
            </main>
        </div>
    </div>
</template>

<script>
import GameViewer from './components/GameViewer.vue'
import './assets/style.css'

export default {
    name: 'App',
    components: { GameViewer }
}
</script>

<style scoped>
header {
    background-color: transparent;
    color: white;
    padding: 20px 0;
}

.header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 20px;
}

h1 {
    margin: 0;
    font-size: 28px;
    color: white;
}

.header-links {
    display: flex;
    gap: 16px;
    align-items: center;
}

.header-links a {
    color: white;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 4px;
    transition: all 0.3s ease;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid white;
}

.header-links a:hover {
    background-color: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
}

.doc-link {
    border-color: white;
    color: white;
}

.doc-link:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

.github-link {
    border-color: white;
    color: white;
}

.github-link:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

main {
    min-height: calc(100vh - 120px);
}
</style>