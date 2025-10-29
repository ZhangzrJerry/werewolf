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
    color: #e6e6e6;
    padding: 20px 0;
    /* border-bottom: 1px solid #dee2e6; */
}

.header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

h1 {
    margin: 0;
    font-size: 28px;
    color: #1a1a2e;
}

.header-links {
    display: flex;
    gap: 16px;
    align-items: center;
}

.header-links a {
    color: #333;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 4px;
    transition: all 0.3s ease;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid transparent;
}

.header-links a:hover {
    background-color: #e9ecef;
    transform: translateY(-2px);
}

.doc-link {
    border-color: #007bff;
    color: #007bff;
}

.doc-link:hover {
    background-color: rgba(0, 123, 255, 0.1);
}

.github-link {
    border-color: #6c757d;
    color: #6c757d;
}

.github-link:hover {
    background-color: rgba(108, 117, 125, 0.1);
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