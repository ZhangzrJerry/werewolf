<template>
    <div class="game-detail-container">
        <div class="detail-header">
            <el-button type="default" :icon="ArrowLeft" @click="$router.push('/')">
                返回首页
            </el-button>
            <h1>游戏详细分析: {{ gameId }}</h1>
        </div>

        <div v-loading="loading" class="detail-content">
            <div v-if="error" class="error-message">
                <el-alert :title="error" type="error" :closable="false" show-icon />
            </div>

            <div v-else-if="gameData" class="analysis-panels">
                <!-- 游戏概览 -->
                <el-card class="panel" shadow="hover">
                    <template #header>
                        <h3>🎮 游戏概览</h3>
                    </template>
                    <GameOverview :game-data="gameData" />
                </el-card>

                <!-- 回合分析 -->
                <el-card class="panel" shadow="hover">
                    <template #header>
                        <h3>📊 回合分析</h3>
                    </template>
                    <RoundAnalysis :rounds="gameData.rounds" />
                </el-card>

                <!-- 玩家表现 -->
                <el-card class="panel" shadow="hover">
                    <template #header>
                        <h3>👥 玩家表现</h3>
                    </template>
                    <PlayerPerformance :players="gameData.players" />
                </el-card>

                <!-- 投票分析 -->
                <el-card class="panel" shadow="hover">
                    <template #header>
                        <h3>🗳️ 投票分析</h3>
                    </template>
                    <VotingAnalysis :rounds="gameData.rounds" />
                </el-card>

                <!-- 策略分析 -->
                <el-card class="panel" shadow="hover">
                    <template #header>
                        <h3>🧠 策略分析</h3>
                    </template>
                    <StrategyAnalysis :game-data="gameData" />
                </el-card>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { useGameStore } from '../stores/game'

// 组件导入
import GameOverview from '../components/GameOverview.vue'
import RoundAnalysis from '../components/RoundAnalysis.vue'
import PlayerPerformance from '../components/PlayerPerformance.vue'
import VotingAnalysis from '../components/VotingAnalysis.vue'
import StrategyAnalysis from '../components/StrategyAnalysis.vue'

const route = useRoute()
const gameStore = useGameStore()

const gameId = computed(() => route.params.gameId)
const { gameData, loading, error } = storeToRefs(gameStore)

// 组件挂载时加载游戏数据
onMounted(async () => {
    if (!gameData.value || gameStore.currentGame !== gameId.value) {
        await gameStore.loadGame(gameId.value)
    }
})
</script>

<style scoped>
.game-detail-container {
    min-height: 100vh;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.detail-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 30px;
    color: white;
}

.detail-header h1 {
    margin: 0;
    font-size: 2em;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.detail-content {
    max-width: 1400px;
    margin: 0 auto;
}

.error-message {
    margin: 20px 0;
}

.analysis-panels {
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
}

.panel {
    background: white;
    border-radius: 12px;
    overflow: hidden;
}

.panel :deep(.el-card__header) {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-bottom: 1px solid #e4e7ed;
}

.panel h3 {
    margin: 0;
    color: #303133;
    font-size: 1.3em;
}

@media (min-width: 1200px) {
    .analysis-panels {
        grid-template-columns: repeat(2, 1fr);
    }

    .panel:first-child {
        grid-column: 1 / -1;
    }
}

@media (max-width: 768px) {
    .detail-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .detail-header h1 {
        font-size: 1.5em;
    }
}
</style>