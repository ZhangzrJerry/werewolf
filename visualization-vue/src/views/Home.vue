<template>
    <div class="home-container">
        <!-- 头部区域 -->
        <header class="header">
            <div class="header-top">
                <h1 class="title">🐺 狼人杀智能体博弈</h1>
                <div class="header-links">
                    <el-button type="primary" @click="$router.push('/doc')" :icon="Document">
                        项目介绍
                    </el-button>
                    <el-button type="link" @click="openGitHub" :icon="Link">
                        GitHub
                    </el-button>
                </div>
            </div>

            <!-- 学习链导航 -->
            <div class="learning-nav">
                <h3 class="nav-title">🎓 智能体学习链</h3>
                <div class="role-links">
                    <el-button v-for="role in roles" :key="role.name" :type="role.type" class="role-button"
                        @click="$router.push(`/learning-chain/${role.name}`)">
                        {{ role.icon }} {{ role.label }}
                    </el-button>
                </div>
            </div>
        </header>

        <!-- 主要内容区域 -->
        <main class="main-content">
            <!-- 游戏日志选择器 -->
            <el-card class="log-selector" shadow="hover">
                <template #header>
                    <div class="card-header">
                        <h2>选择游戏日志</h2>
                        <el-button type="primary" :icon="Refresh" @click="refreshGameList" :loading="loading">
                            刷新
                        </el-button>
                    </div>
                </template>

                <div v-loading="loading" class="log-list">
                    <div v-if="error" class="error-message">
                        <el-alert :title="error" type="error" :closable="false" show-icon />
                    </div>

                    <div v-else-if="sortedGameList.length === 0 && !loading" class="empty-state">
                        <el-empty description="暂无可用的游戏日志" />
                    </div>

                    <div v-else class="game-list">
                        <el-row :gutter="16">
                            <el-col v-for="game in sortedGameList" :key="game.filename" :xs="24" :sm="12" :md="8"
                                :lg="6">
                                <el-card class="game-card" :class="{ active: currentGameFilename === game.filename }"
                                    @click="selectGame(game)" shadow="hover">
                                    <div class="game-info">
                                        <h4 class="game-filename">{{ game.filename }}</h4>
                                        <div class="game-meta">
                                            <div class="meta-item">
                                                <el-icon>
                                                    <Clock />
                                                </el-icon>
                                                <span>{{ formatDate(game.modified) }}</span>
                                            </div>
                                            <div class="meta-item">
                                                <el-icon>
                                                    <Document />
                                                </el-icon>
                                                <span>{{ formatSize(game.size) }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </el-card>
                            </el-col>
                        </el-row>
                    </div>
                </div>
            </el-card>

            <!-- 游戏详情 -->
            <div v-if="isGameLoaded" class="game-detail">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <h2>游戏详情: {{ currentGameFilename }}</h2>
                            <el-button type="primary"
                                @click="$router.push(`/game/${currentGameFilename.replace('.txt', '')}`)">
                                查看详细分析
                            </el-button>
                        </div>
                    </template>

                    <GameSummaryV2 v-if="gameOverview" :game-data="gameOverview" />
                </el-card>
            </div>
        </main>
    </div>
</template>

<script setup>
import { Document, Link, Refresh, Clock } from '@element-plus/icons-vue'
import { useGameStore } from '../stores/game'
import GameSummaryV2 from '../components/GameSummaryV2.vue'

const gameStore = useGameStore()

// 响应式数据
const {
    gameList,
    sortedGameList,
    currentGameFilename,
    gameOverview,
    isGameLoaded,
    loading,
    error
} = storeToRefs(gameStore)

// 角色配置
const roles = [
    { name: 'seer', label: '预言家', icon: '🔮', type: 'primary' },
    { name: 'werewolf', label: '狼人', icon: '🐺', type: 'danger' },
    { name: 'witch', label: '女巫', icon: '🧙‍♀️', type: 'warning' },
    { name: 'villager', label: '村民', icon: '👨‍🌾', type: 'info' },
    { name: 'guardian', label: '守卫', icon: '🛡️', type: 'success' },
    { name: 'hunter', label: '猎人', icon: '🏹', type: 'default' }
]

// 组件挂载时获取游戏列表
onMounted(() => {
    refreshGameList()
})

// 方法
function refreshGameList() {
    gameStore.fetchGameList()
}

function selectGame(game) {
    gameStore.loadGame(game.filename)
}

function openGitHub() {
    window.open('https://github.com/ZhangzrJerry/werewolf', '_blank');
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`
}
</script>

<style scoped>
.home-container {
    min-height: 100vh;
    padding: 20px;
}

.header {
    text-align: center;
    color: white;
    margin-bottom: 30px;
}

.header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.title {
    font-size: 2.5em;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    margin: 0;
}

.header-links {
    display: flex;
    gap: 15px;
    align-items: center;
}

.learning-nav {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    padding: 20px;
    backdrop-filter: blur(10px);
}

.nav-title {
    margin-bottom: 15px;
    font-size: 1.2em;
}

.role-links {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
}

.role-button {
    font-weight: 500;
}

.main-content {
    max-width: 1400px;
    margin: 0 auto;
}

.log-selector {
    margin-bottom: 30px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-header h2 {
    margin: 0;
    font-size: 1.5em;
    color: #303133;
}

.error-message {
    margin: 20px 0;
}

.empty-state {
    padding: 40px 0;
}

.game-list {
    margin-top: 20px;
}

.game-card {
    cursor: pointer;
    transition: all 0.3s ease;
    margin-bottom: 16px;
}

.game-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.game-card.active {
    border-color: #409eff;
    background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
}

.game-info {
    padding: 10px 0;
}

.game-filename {
    margin: 0 0 10px 0;
    font-size: 1.1em;
    color: #303133;
    word-break: break-all;
}

.game-meta {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.meta-item {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.9em;
    color: #606266;
}

.game-detail {
    margin-top: 30px;
}

@media (max-width: 768px) {
    .header-top {
        flex-direction: column;
        gap: 15px;
    }

    .title {
        font-size: 2em;
    }

    .header-links {
        flex-wrap: wrap;
    }
}
</style>