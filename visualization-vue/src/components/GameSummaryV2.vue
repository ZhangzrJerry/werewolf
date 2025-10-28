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
                            <span class="value">{{ gameInfo?.rounds_played || 0 }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">玩家数量:</span>
                            <span class="value">{{ Object.keys(players).length || 0 }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">游戏结果:</span>
                            <el-tag :type="getWinnerTagType(finalResult.winner)">
                                {{ getWinnerText(finalResult.winner) }}
                            </el-tag>
                        </div>
                        <div class="info-item">
                            <span class="label">游戏完成:</span>
                            <el-tag :type="gameInfo?.game_completed ? 'success' : 'warning'">
                                {{ gameInfo?.game_completed ? '是' : '否' }}
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
                            <span class="stat-label">死亡人数:</span>
                            <span class="stat-value">{{ deathCount }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">狼人剩余:</span>
                            <span class="stat-value">{{ finalResult.werewolves_remaining || 0 }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">村民剩余:</span>
                            <span class="stat-value">{{ finalResult.villagers_remaining || 0 }}</span>
                        </div>
                    </div>
                </div>
            </el-col>
        </el-row>

        <!-- 死亡时间线 -->
        <div class="timeline-section">
            <h4>📈 死亡时间线</h4>
            <el-timeline>
                <el-timeline-item v-for="(death, index) in deathTimeline.slice(0, 10)" :key="index"
                    :timestamp="`第${death.round}回合 - ${death.phase}`" placement="top">
                    <div class="timeline-content">
                        <h5>{{ death.player }} 死亡</h5>
                        <p>原因: {{ getDeathReasonText(death.reason) }}</p>
                        <el-tag size="small" :type="getDeathReasonType(death.reason)">
                            {{ death.reason }}
                        </el-tag>
                    </div>
                </el-timeline-item>
                <el-timeline-item v-if="deathTimeline.length > 10" timestamp="..." placement="top">
                    <p>还有 {{ deathTimeline.length - 10 }} 个死亡事件...</p>
                </el-timeline-item>
            </el-timeline>
        </div>

        <!-- 特殊行动概览 -->
        <div class="actions-section" v-if="specialActions.length > 0">
            <h4>🎯 特殊行动概览</h4>
            <el-table :data="specialActions.slice(0, 10)" stripe style="width: 100%">
                <el-table-column prop="round" label="回合" width="80" />
                <el-table-column prop="phase" label="阶段" width="100" />
                <el-table-column prop="type" label="行动类型" width="150">
                    <template #default="{ row }">
                        <el-tag size="small" :type="getActionType(row.type)">
                            {{ getActionName(row.type) }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="actor" label="执行者" width="120" />
                <el-table-column prop="target" label="目标" width="120" />
                <el-table-column prop="result" label="结果" />
            </el-table>
            <div v-if="specialActions.length > 10" class="more-actions">
                还有 {{ specialActions.length - 10 }} 个特殊行动...
            </div>
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

// 从传入的 gameData 中提取各部分数据
const gameInfo = computed(() => props.gameData.game_info || {})
const players = computed(() => props.gameData.players || {})
const roundSummary = computed(() => props.gameData.round_summary || [])
const deathTimeline = computed(() => props.gameData.death_timeline || [])
const votingHistory = computed(() => props.gameData.voting_history || [])
const specialActions = computed(() => props.gameData.special_actions || [])
const finalResult = computed(() => props.gameData.final_result || {})
const reviewsAndLessons = computed(() => props.gameData.reviews_and_lessons || {})

// 计算角色分布
const roleDistribution = computed(() => {
    const distribution = {}
    Object.values(players.value).forEach(player => {
        const role = player.role || 'unknown'
        distribution[role] = (distribution[role] || 0) + 1
    })
    return distribution
})

// 计算游戏统计
const votingRounds = computed(() => {
    const uniqueRounds = new Set(votingHistory.value.map(vote => vote.round))
    return uniqueRounds.size
})

const deathCount = computed(() => {
    return deathTimeline.value.length
})

// 工具函数
function getWinnerTagType(winner) {
    const types = {
        'werewolf': 'danger',
        'WEREWOLVES WIN': 'danger',
        'villager': 'success',
        'village': 'success',
        'VILLAGERS WIN': 'success'
    }
    return types[winner] || 'info'
}

function getWinnerText(winner) {
    const texts = {
        'werewolf': '狼人胜利',
        'WEREWOLVES WIN': '狼人胜利',
        'villager': '村民胜利',
        'village': '村民胜利',
        'VILLAGERS WIN': '村民胜利',
        'DRAW': '平局'
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

function getDeathReasonText(reason) {
    const texts = {
        'vote': '投票出局',
        'werewolf': '狼人击杀',
        'witch': '女巫毒杀',
        'hunter': '猎人技能',
        'unknown': '未知原因'
    }
    return texts[reason] || reason
}

function getDeathReasonType(reason) {
    const types = {
        'vote': 'warning',
        'werewolf': 'danger',
        'witch': 'primary',
        'hunter': 'success',
        'unknown': 'info'
    }
    return types[reason] || 'info'
}

function getActionName(type) {
    const names = {
        'werewolf_target': '狼人击杀',
        'seer_check': '预言家查验',
        'witch_save': '女巫救人',
        'witch_poison': '女巫毒杀',
        'hunter_skill': '猎人技能',
        'guardian_protect': '守卫保护'
    }
    return names[type] || type
}

function getActionType(type) {
    const types = {
        'werewolf_target': 'danger',
        'seer_check': 'primary',
        'witch_save': 'success',
        'witch_poison': 'warning',
        'hunter_skill': 'info',
        'guardian_protect': 'success'
    }
    return types[type] || 'default'
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

.timeline-section,
.actions-section {
    margin-top: 30px;
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.timeline-section h4,
.actions-section h4 {
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
    margin: 0 0 5px 0;
    color: #606266;
    font-size: 0.9em;
}

.more-actions {
    margin-top: 10px;
    text-align: center;
    color: #909399;
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