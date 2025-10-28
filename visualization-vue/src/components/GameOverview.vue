<template>
    <div class="game-overview">
        <el-row :gutter="20">
            <!-- 基础信息卡片 -->
            <el-col :xs="24" :md="12" :lg="8">
                <el-card class="info-card">
                    <template #header>
                        <h3>🎮 游戏信息</h3>
                    </template>
                    <div class="info-list">
                        <div class="info-item">
                            <span class="label">游戏ID:</span>
                            <span class="value">{{ gameData.id }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">回合数:</span>
                            <span class="value">{{ gameData.game_info?.rounds_played || 0 }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">事件总数:</span>
                            <span class="value">{{ gameData.metadata?.total_events || 0 }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">文件大小:</span>
                            <span class="value">{{ formatFileSize(gameData.metadata?.file_size) }}</span>
                        </div>
                    </div>
                </el-card>
            </el-col>

            <!-- 玩家统计 -->
            <el-col :xs="24" :md="12" :lg="8">
                <el-card class="info-card">
                    <template #header>
                        <h3>👥 玩家统计</h3>
                    </template>
                    <div class="player-stats">
                        <div v-for="(count, role) in roleDistribution" :key="role" class="role-stat">
                            <span class="role-name">{{ getRoleName(role) }}:</span>
                            <span class="role-count">{{ count }}</span>
                        </div>
                    </div>
                </el-card>
            </el-col>

            <!-- 胜负结果 -->
            <el-col :xs="24" :md="24" :lg="8">
                <el-card class="info-card">
                    <template #header>
                        <h3>🏆 胜负结果</h3>
                    </template>
                    <div class="result-display">
                        <el-tag :type="getWinnerTagType(gameData.game_info?.winner)" size="large" class="winner-tag">
                            {{ getWinnerText(gameData.game_info?.winner) }}
                        </el-tag>
                        <div class="completion-status">
                            <el-icon>
                                <SuccessFilled v-if="gameData.game_info?.game_completed" />
                                <WarningFilled v-else />
                            </el-icon>
                            <span>{{ gameData.game_info?.game_completed ? '游戏完成' : '游戏未完成' }}</span>
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 玩家详情表格 -->
        <el-card class="players-table" style="margin-top: 20px;">
            <template #header>
                <h3>👤 玩家详情</h3>
            </template>
            <el-table :data="playersArray" stripe style="width: 100%">
                <el-table-column prop="name" label="玩家名称" width="120" />
                <el-table-column prop="role" label="角色" width="100">
                    <template #default="{ row }">
                        <el-tag :type="getRoleTagType(row.role)" size="small">
                            {{ getRoleName(row.role) }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                    <template #default="{ row }">
                        <el-tag :type="row.status === 'alive' ? 'success' : 'danger'" size="small">
                            {{ row.status === 'alive' ? '存活' : '死亡' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="death_round" label="死亡回合" width="100" />
                <el-table-column prop="death_reason" label="死亡原因" />
            </el-table>
        </el-card>

        <!-- 复盘分析 -->
        <el-card v-if="gameData.reviews && gameData.reviews.length > 0" class="reviews-section"
            style="margin-top: 20px;">
            <template #header>
                <h3>📝 复盘分析</h3>
            </template>
            <el-collapse>
                <el-collapse-item v-for="(review, index) in gameData.reviews" :key="index" :title="review.title">
                    <div class="review-content">
                        <el-tag :type="getReviewTagType(review.type)" size="small">{{ review.type }}</el-tag>
                        <div class="review-text">{{ review.content }}</div>
                    </div>
                </el-collapse-item>
            </el-collapse>
        </el-card>
    </div>
</template>

<script setup>
import { SuccessFilled, WarningFilled } from '@element-plus/icons-vue'
import { computed } from 'vue'

const props = defineProps({
    gameData: {
        type: Object,
        required: true
    }
})

// 计算玩家数组
const playersArray = computed(() => {
    if (!props.gameData.players) return []
    return Object.values(props.gameData.players)
})

// 计算角色分布
const roleDistribution = computed(() => {
    const distribution = {}
    playersArray.value.forEach(player => {
        const role = player.role || 'unknown'
        distribution[role] = (distribution[role] || 0) + 1
    })
    return distribution
})

// 工具函数
function getRoleName(role) {
    const names = {
        'seer': '预言家',
        'werewolf': '狼人',
        'witch': '女巫',
        'villager': '村民',
        'guardian': '守卫',
        'hunter': '猎人'
    }
    return names[role] || role
}

function getRoleTagType(role) {
    const types = {
        'seer': 'primary',
        'werewolf': 'danger',
        'witch': 'warning',
        'villager': 'info',
        'guardian': 'success',
        'hunter': 'default'
    }
    return types[role] || 'default'
}

function getWinnerTagType(winner) {
    if (winner?.includes('WEREWOLVES') || winner === 'werewolf') return 'danger'
    if (winner?.includes('VILLAGERS') || winner === 'villager') return 'success'
    return 'info'
}

function getWinnerText(winner) {
    if (winner?.includes('WEREWOLVES') || winner === 'werewolf') return '狼人胜利'
    if (winner?.includes('VILLAGERS') || winner === 'villager') return '村民胜利'
    if (winner === 'DRAW') return '平局'
    return winner || '未知'
}

function getReviewTagType(type) {
    const types = {
        'seer_analysis': 'primary',
        'werewolf_analysis': 'danger',
        'witch_analysis': 'warning',
        'villager_analysis': 'info',
        'game_analysis': 'success',
        'strategy_analysis': 'default'
    }
    return types[type] || 'default'
}

function formatFileSize(bytes) {
    if (!bytes) return '未知'
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
.game-overview {
    padding: 20px 0;
}

.info-card {
    height: 100%;
}

.info-card h3 {
    margin: 0;
    color: #303133;
}

.info-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
    border-bottom: none;
}

.label {
    color: #606266;
    font-weight: 500;
}

.value {
    color: #303133;
    font-weight: 600;
}

.player-stats {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.role-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #f5f7fa;
    border-radius: 6px;
}

.role-name {
    color: #606266;
    font-weight: 500;
}

.role-count {
    color: #303133;
    font-weight: 600;
    font-size: 1.1em;
}

.result-display {
    text-align: center;
    padding: 20px 0;
}

.winner-tag {
    font-size: 1.2em;
    padding: 8px 16px;
    margin-bottom: 15px;
}

.completion-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #606266;
}

.players-table,
.reviews-section {
    margin-top: 20px;
}

.review-content {
    padding: 10px 0;
}

.review-text {
    margin-top: 10px;
    line-height: 1.6;
    color: #606266;
}

@media (max-width: 768px) {
    .info-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
}
</style>