<template>
    <div id="app">
        <router-view />
    </div>
</template>

<script setup>
// 应用入口组件
</script>

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

#app {
    min-height: 100vh;
    width: 100%;
}
</style>