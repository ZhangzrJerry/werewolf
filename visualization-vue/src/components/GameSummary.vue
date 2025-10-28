<template>
    <div class="game-summary">
        <el-row :gutter="20">
            <!-- 基本信息 -->
            <el-col :xs="24" :sm="12" :md="8">
                <div class="summary-card">
                    <h4>🎮 游戏基本信息</h4>
                    <div class="info-list">
                        <div class="info-item">
                            <span class="label">总回合数:</span>
                            <span class="value">{{ gameData.rounds?.length || 0 }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">玩家数量:</span>
                            <span class="value">{{ gameData.players?.length || 0 }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">游戏结果:</span>
                            <el-tag :type="getWinnerTagType(gameData.winner)">
                                {{ getWinnerText(gameData.winner) }}
                            </el-tag>
                        </div>
                    </div>
                </div>
            </el-col>

            <!-- 角色分布 -->
            <el-col :xs="24" :sm="12" :md="8">
                <div class="summary-card">
                    <h4>👥 角色分布</h4>
                    <div class="role-distribution">
                        <div v-for="(count, role) in roleDistribution" :key="role" class="role-item">
                            <span class="role-icon">{{ getRoleIcon(role) }}</span>
                            <span class="role-name">{{ getRoleName(role) }}</span>
                            <el-tag size="small">{{ count }}</el-tag>
                        </div>
                    </div>
                </div>
            </el-col>

            <!-- 游戏统计 -->
            <el-col :xs="24" :sm="24" :md="8">
                <div class="summary-card">
                    <h4>📊 游戏统计</h4>
                    <div class="stats-list">
                        <div class="stat-item">
                            <span class="stat-label">投票轮数:</span>
                            <span class="stat-value">{{ votingRounds }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">淘汰人数:</span>
                            <span class="stat-value">{{ eliminatedCount }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">游戏时长:</span>
                            <span class="stat-value">{{ gameDuration }}</span>
                        </div>
                    </div>
                </div>
            </el-col>
        </el-row>

        <!-- 游戏进程时间线 -->
        <div class="timeline-section">
            <h4>📈 游戏进程时间线</h4>
            <el-timeline>
                <el-timeline-item v-for="(round, index) in gameData.rounds?.slice(0, 10)" :key="index"
                    :timestamp="formatRoundNumber(index + 1)" placement="top">
                    <div class="timeline-content">
                        <h5>第 {{ index + 1 }} 回合</h5>
                        <p>{{ getRoundSummary(round) }}</p>
                    </div>
                </el-timeline-item>
                <el-timeline-item v-if="gameData.rounds?.length > 10" timestamp="..." placement="top">
                    <p>还有 {{ gameData.rounds.length - 10 }} 个回合...</p>
                </el-timeline-item>
            </el-timeline>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    gameData: {
        type: Object,
        required: true
    }
})

// 计算角色分布
const roleDistribution = computed(() => {
    if (!props.gameData.players) return {}

    const distribution = {}
    props.gameData.players.forEach(player => {
        const role = player.role || 'unknown'
        distribution[role] = (distribution[role] || 0) + 1
    })

    return distribution
})

// 计算游戏统计
const votingRounds = computed(() => {
    return props.gameData.rounds?.filter(round =>
        round.actions?.some(action => action.type === 'vote')
    ).length || 0
})

const eliminatedCount = computed(() => {
    return props.gameData.players?.filter(player =>
        player.status === 'eliminated' || player.alive === false
    ).length || 0
})

const gameDuration = computed(() => {
    if (!props.gameData.start_time || !props.gameData.end_time) {
        return '未知'
    }

    const duration = props.gameData.end_time - props.gameData.start_time
    const minutes = Math.floor(duration / 60)
    const seconds = duration % 60

    return `${minutes}分${seconds}秒`
})

// 工具函数
function getWinnerTagType(winner) {
    const types = {
        'werewolf': 'danger',
        'villager': 'success',
        'village': 'success'
    }
    return types[winner] || 'info'
}

function getWinnerText(winner) {
    const texts = {
        'werewolf': '狼人胜利',
        'villager': '村民胜利',
        'village': '村民胜利'
    }
    return texts[winner] || winner || '游戏中'
}

function getRoleIcon(role) {
    const icons = {
        'seer': '🔮',
        'werewolf': '🐺',
        'witch': '🧙‍♀️',
        'villager': '👨‍🌾',
        'guardian': '🛡️',
        'hunter': '🏹'
    }
    return icons[role] || '❓'
}

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

function formatRoundNumber(round) {
    return `回合 ${round}`
}

function getRoundSummary(round) {
    if (!round.actions || round.actions.length === 0) {
        return '无特殊事件'
    }

    const actionTypes = round.actions.map(action => action.type).join(', ')
    return `执行动作: ${actionTypes}`
}
</script>

<style scoped>
.game-summary {
    padding: 20px 0;
}

.summary-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    height: 100%;
}

.summary-card h4 {
    margin: 0 0 15px 0;
    color: #303133;
    font-size: 1.1em;
}

.info-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.label {
    color: #606266;
    font-size: 0.9em;
}

.value {
    font-weight: 500;
    color: #303133;
}

.role-distribution {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.role-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.role-icon {
    font-size: 1.2em;
}

.role-name {
    flex: 1;
    color: #606266;
    font-size: 0.9em;
}

.stats-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stat-label {
    color: #606266;
    font-size: 0.9em;
}

.stat-value {
    font-weight: 500;
    color: #303133;
}

.timeline-section {
    margin-top: 30px;
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.timeline-section h4 {
    margin: 0 0 20px 0;
    color: #303133;
    font-size: 1.1em;
}

.timeline-content h5 {
    margin: 0 0 5px 0;
    color: #303133;
    font-size: 1em;
}

.timeline-content p {
    margin: 0;
    color: #606266;
    font-size: 0.9em;
}

@media (max-width: 768px) {
    .summary-card {
        margin-bottom: 15px;
    }

    .info-item,
    .stat-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 5px;
    }
}
</style>