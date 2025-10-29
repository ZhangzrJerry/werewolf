<template>
    <div class="app-shell">
        <header class="app-header">
            <h1>🐺 狼人杀智能体博弈 - 游戏回放</h1>
        </header>
        <main>
            <GameViewer />
        </main>
    </div>
</template>

<script>
import GameViewer from './components/GameViewer.vue'

export default {
    name: 'App',
    components: { GameViewer }
}
</script>

<style>
body {
    font-family: Arial, Helvetica, sans-serif;
    margin: 0;
}

.app-header {
    background: #2c3e50;
    color: #fff;
    padding: 12px 16px
}

.app-shell main {
    padding: 16px
}
</style>
