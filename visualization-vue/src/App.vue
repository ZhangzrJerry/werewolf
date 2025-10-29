<template>
    <div class="app-shell">
        <header class="app-header">
            <h1>狼人杀 - 日志查看</h1>
        </header>
        <main>
            <TrainingViewer />
        </main>
    </div>
</template>

<script>
import TrainingViewer from './components/TrainingViewer.vue'

export default {
    name: 'App',
    components: { TrainingViewer }
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
