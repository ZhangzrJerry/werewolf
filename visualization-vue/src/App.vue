<template>
    <div class="app-shell">
        <header>
            <div class="header-top">
                <h1>🐺 Werewolf Game Replay Viewer</h1>
                <div class="header-links">
                    <a :href="`${import.meta.env.BASE_URL}doc.html`" class="doc-link" target="_blank">📖
                        Documentation</a>
                    <a href="https://github.com/ZhangzrJerry/werewolf" class="github-link" target="_blank">🔗 GitHub</a>
                </div>
            </div>
        </header>

        <div class="container">
            <main>
                <router-view />
            </main>
        </div>
    </div>
</template>

<script>
import './assets/style.css'

export default {
    name: 'App'
}
</script>

<style scoped>
header {
    background-color: transparent;
    color: white;
    padding: 16px 0;
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
    font-size: 24px;
    color: white;
}

.header-links a {
    color: white;
    text-decoration: none;
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-left: 8px;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}
</style>